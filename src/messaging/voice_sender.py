#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
VoiceMessageSender - Sistema de envío de mensajes por voz para Asistente Kata

Orquesta todo el flujo de envío de mensajes:
1. Detectar comando de envío
2. Normalizar nombre de contacto  
3. Validar contacto existe
4. Procesar mensaje con IA (primera persona)
5. Enviar via Telegram con feedback inmediato

Autor: Asistente Kata
"""

import logging
import threading
import time
from typing import Optional, Callable, Dict, Any, List
import requests
import os

logger = logging.getLogger(__name__)

class VoiceMessageSender:
    """Sistema de envío de mensajes por voz con feedback inmediato"""
    
    def __init__(self, tts_manager, selected_voice: str, message_ai=None):
        """
        Inicializa el sistema de envío de mensajes por voz
        
        Args:
            tts_manager: Gestor de text-to-speech
            selected_voice (str): Voz seleccionada para TTS
            message_ai: Procesador de mensajes con IA
        """
        self.tts_manager = tts_manager
        self.selected_voice = selected_voice
        self.message_ai = message_ai
        
        # Importar módulos necesarios
        try:
            import sys
            import os
            from dotenv import load_dotenv
            load_dotenv()  # Cargar variables de entorno
            
            # Agregar paths necesarios
            sys.path.append(os.path.dirname(os.path.dirname(__file__)))  # src/
            sys.path.append(os.path.dirname(os.path.dirname(os.path.dirname(__file__))))  # raíz del proyecto
            
            from database.models.shared_data_manager import shared_data_manager
            from .contact_normalizer import contact_normalizer
            from ai.intent_manager import parse_send_message_intent, parse_conversational_message_intent
            from ai.contextual_inference import initialize_contextual_inference
            from ai.failed_commands_logger import initialize_failed_commands_logger
            
            self.db_manager = shared_data_manager
            self.contact_normalizer = contact_normalizer
            self.parse_intent = parse_send_message_intent
            self.parse_conversational_intent = parse_conversational_message_intent
            
            # FASE 2: Inicializar motor de inferencia contextual
            self.contextual_engine = initialize_contextual_inference(
                self.db_manager, self.contact_normalizer
            )
            
            # Inicializar logger simple de comandos fallidos
            self.failed_logger = initialize_failed_commands_logger()
            
        except ImportError as e:
            logger.error(f"Error importando dependencias: {e}")
            self.db_manager = None
            self.contact_normalizer = None
            self.parse_intent = None
            self.parse_conversational_intent = None
            self.contextual_engine = None
            self.failed_logger = None
        
        # Configuración de Telegram
        self.bot_token = os.getenv('TELEGRAM_BOT_TOKEN')
        self.api_url = f"https://api.telegram.org/bot{self.bot_token}" if self.bot_token else None
        
        logger.info("VoiceMessageSender inicializado correctamente")
    
    def can_process_message(self, text: str) -> bool:
        """
        Verifica si el texto es un comando de envío de mensaje (directo, conversacional o inferido)
        
        Args:
            text (str): Texto del usuario
            
        Returns:
            bool: True si es comando de envío
        """
        if not any([self.parse_intent, self.parse_conversational_intent, self.contextual_engine]):
            return False
        
        # Intentar parser tradicional primero
        if self.parse_intent:
            result = self.parse_intent(text)
            if result is not None:
                return True
        
        # Si no funciona, intentar parser conversacional - FASE 1
        if self.parse_conversational_intent:
            result = self.parse_conversational_intent(text)
            if result is not None:
                return True
        
        # Si fallan ambos, intentar inferencia contextual - FASE 2
        if self.contextual_engine:
            can_infer = self.contextual_engine.can_infer_message_intent(text)
            if can_infer:
                return True
        
        return False
    
    def process_voice_message(self, text: str, user_name: str = "Marina") -> bool:
        """
        Procesa comando de envío de mensaje por voz con flujo completo
        
        Args:
            text (str): Comando del usuario ("dile a Marina que llegué bien")
            user_name (str): Nombre del usuario que envía
            
        Returns:
            bool: True si se procesó exitosamente
        """
        try:
            logger.info(f"VoiceMessageSender: Procesando comando - '{text}'")
            
            # 🚀 RESPUESTA INMEDIATA - Dar feedback instantáneo mientras procesamos
            self._say_feedback("Procesando mensaje")
            
            # 1. Parsear comando - Cascada de parsers: Tradicional → Conversacional → Contextual
            parse_result = None
            inference_confidence = None
            
            # Intentar parser tradicional
            if self.parse_intent:
                parse_result = self.parse_intent(text)
                
            # Si falla, intentar parser conversacional - FASE 1
            if not parse_result and self.parse_conversational_intent:
                parse_result = self.parse_conversational_intent(text)
                if parse_result:
                    logger.info("VoiceMessageSender: Usando parser conversacional FASE 1")
                
            # Si fallan ambos, intentar inferencia contextual - FASE 2
            if not parse_result and self.contextual_engine:
                inference_result = self.contextual_engine.infer_message_command(text)
                if inference_result:
                    command, contact, message, confidence = inference_result
                    parse_result = (command, contact, message)
                    inference_confidence = confidence
                    logger.info(f"VoiceMessageSender: Usando inferencia contextual FASE 2 (confianza: {confidence})")
                
            if not parse_result:
                logger.warning("VoiceMessageSender: No se pudo procesar el comando con ningún método (Tradicional/Conversacional/Contextual)")
                
                # Registrar comando fallido para análisis posterior
                if self.failed_logger:
                    self.failed_logger.log_failed_command(text, user_name, "No se reconoció como comando de mensaje")
                
                self._say_error("No entendí el comando de mensaje")
                return False
            
            command, contact_raw, message_body = parse_result
            logger.info(f"Parseado: comando='{command}', contacto='{contact_raw}', mensaje='{message_body}'")
            
            # 2. Validar contacto - Si viene de inferencia contextual, ya está validado
            if inference_confidence is not None:
                # Contacto ya validado por motor de inferencia contextual
                matched_contact = contact_raw
                logger.info(f"VoiceMessageSender: Contacto validado por inferencia contextual: '{matched_contact}'")
            else:
                # Usar normalización tradicional para parsers directos
                contact_variants = self.contact_normalizer.normalize_contact_name(contact_raw)
                available_contacts = self._get_available_contacts()
                matched_contact = self.contact_normalizer.find_best_match(contact_raw, available_contacts)
                
                if not matched_contact:
                    logger.warning(f"VoiceMessageSender: Contacto '{contact_raw}' no encontrado")
                    
                    # Registrar comando fallido por contacto no encontrado
                    if self.failed_logger:
                        self.failed_logger.log_failed_command(text, user_name, f"Contacto '{contact_raw}' no encontrado")
                    
                    self._say_error(f"No encontré el contacto {contact_raw}")
                    return False
            
            # 4. Feedback inmediato + procesamiento en paralelo
            self._say_feedback("procesando mensaje")
            
            # Ejecutar procesamiento en hilo separado
            thread = threading.Thread(
                target=self._process_and_send_message,
                args=(command, matched_contact, message_body, user_name),
                daemon=True
            )
            thread.start()
            
            return True
            
        except Exception as e:
            logger.error(f"VoiceMessageSender: Error procesando mensaje: {e}")
            self._say_error("Hubo un error procesando tu mensaje")
            return False
    
    def _process_and_send_message(self, command: str, contact: str, message_body: str, user_name: str):
        """
        Procesa y envía el mensaje en hilo separado
        
        Args:
            command (str): Comando original
            contact (str): Contacto validado  
            message_body (str): Cuerpo del mensaje
            user_name (str): Usuario que envía
        """
        try:
            logger.info(f"VoiceMessageSender: Procesando mensaje para '{contact}'")
            
            # 1. Procesar mensaje con IA (primera persona)
            processed_message = self._process_message_with_ai(command, message_body, user_name)
            
            # 2. Obtener chat_id del contacto
            chat_id = self._get_contact_chat_id(contact)
            if not chat_id:
                logger.error(f"VoiceMessageSender: No se encontró chat_id para '{contact}'")
                self._say_feedback("No pude encontrar el chat del contacto")
                return
            
            # 3. Enviar mensaje via Telegram
            success = self._send_telegram_message(chat_id, processed_message)
            
            # 4. Feedback final
            if success:
                logger.info(f"VoiceMessageSender: Mensaje enviado exitosamente a '{contact}'")
                self._say_feedback("mensaje enviado")
            else:
                logger.error(f"VoiceMessageSender: Error enviando mensaje a '{contact}'")
                self._say_feedback("error enviando mensaje")
                
        except Exception as e:
            logger.error(f"VoiceMessageSender: Error en procesamiento: {e}")
            self._say_feedback("error procesando mensaje")
    
    def _process_message_with_ai(self, command: str, message_body: str, user_name: str) -> str:
        """
        Procesa el mensaje con IA para convertir a primera persona
        
        Args:
            command (str): Comando original ("dile a", "preguntale a")
            message_body (str): Cuerpo del mensaje
            user_name (str): Usuario que envía
            
        Returns:
            str: Mensaje procesado
        """
        try:
            if self.message_ai:
                # Determinar tipo de comando - MEJORADO FASE 1
                command_lower = command.lower()
                
                # Comandos que implican preguntas
                question_commands = ["pregunta", "será que", "no sé si", "me pregunto si"]
                command_type = "pregunta" if any(cmd in command_lower for cmd in question_commands) else "dice"
                
                # Procesar con IA
                processed = self.message_ai.process_message_to_first_person(
                    message_body, command_type, user_name
                )
                
                logger.info(f"VoiceMessageSender: Mensaje procesado por IA - '{processed}'")
                return processed
            else:
                # Fallback simple
                return f"{user_name} dice: {message_body}"
                
        except Exception as e:
            logger.error(f"VoiceMessageSender: Error procesando con IA: {e}")
            return f"{user_name} dice: {message_body}"
    
    def _get_available_contacts(self) -> List[Dict[str, Any]]:
        """
        Obtiene lista de contactos disponibles desde BD incluyendo alias
        
        Returns:
            List[Dict]: Lista de contactos con nombres y alias
        """
        try:
            if not self.db_manager:
                return []
            
            # Obtener contactos con alias desde la tabla contacts
            with self.db_manager.get_connection() as conn:
                cursor = conn.cursor()
                cursor.execute("""
                    SELECT display_name, aliases, telegram_chat_id 
                    FROM contacts 
                    WHERE is_active = TRUE 
                    ORDER BY display_name
                """)
                
                contacts = []
                for row in cursor.fetchall():
                    import json
                    aliases = json.loads(row['aliases']) if row['aliases'] else []
                    
                    contacts.append({
                        'display_name': row['display_name'],
                        'aliases': aliases,
                        'telegram_chat_id': row['telegram_chat_id']
                    })
                
                logger.debug(f"VoiceMessageSender: {len(contacts)} contactos disponibles con alias")
                return contacts
                
        except Exception as e:
            logger.error(f"VoiceMessageSender: Error obteniendo contactos: {e}")
            return []
    
    def _get_contact_chat_id(self, contact_name: str) -> Optional[str]:
        """
        Obtiene el chat_id de Telegram para un contacto
        
        Args:
            contact_name (str): Nombre del contacto (display_name)
            
        Returns:
            str: chat_id o None si no se encuentra
        """
        try:
            # Primero intentar obtener desde los contactos en memoria
            available_contacts = self._get_available_contacts()
            for contact in available_contacts:
                if contact['display_name'].lower() == contact_name.lower():
                    chat_id = contact.get('telegram_chat_id')
                    if chat_id:
                        logger.debug(f"VoiceMessageSender: chat_id encontrado para '{contact_name}': {chat_id}")
                        return chat_id
                    break
            
            # Fallback a consulta directa en BD
            if not self.db_manager:
                return None
            
            with self.db_manager.get_connection() as conn:
                cursor = conn.cursor()
                cursor.execute(
                    "SELECT telegram_chat_id FROM contacts WHERE display_name = ? LIMIT 1",
                    (contact_name,)
                )
                result = cursor.fetchone()
                
                if result and result['telegram_chat_id']:
                    return result['telegram_chat_id']
                else:
                    logger.warning(f"VoiceMessageSender: No se encontró chat_id para '{contact_name}'")
                    return None
                    
        except Exception as e:
            logger.error(f"VoiceMessageSender: Error obteniendo chat_id: {e}")
            return None
    
    def _send_telegram_message(self, chat_id: str, message: str) -> bool:
        """
        Envía mensaje via Telegram Bot API
        
        Args:
            chat_id (str): ID del chat de destino
            message (str): Mensaje a enviar
            
        Returns:
            bool: True si se envió exitosamente
        """
        try:
            if not self.api_url:
                logger.error("VoiceMessageSender: Bot token no configurado")
                return False
            
            url = f"{self.api_url}/sendMessage"
            payload = {
                'chat_id': chat_id,
                'text': message,
                'parse_mode': 'HTML'
            }
            
            response = requests.post(url, json=payload, timeout=10)
            
            if response.status_code == 200:
                result = response.json()
                if result.get('ok'):
                    logger.info(f"VoiceMessageSender: Mensaje enviado exitosamente a {chat_id}")
                    return True
                else:
                    logger.error(f"VoiceMessageSender: Error API Telegram: {result}")
                    return False
            else:
                logger.error(f"VoiceMessageSender: HTTP Error {response.status_code}: {response.text}")
                return False
                
        except Exception as e:
            logger.error(f"VoiceMessageSender: Error enviando mensaje: {e}")
            return False
    
    def _say_feedback(self, message: str):
        """Reproduce feedback por TTS"""
        try:
            if self.tts_manager:
                self.tts_manager.say(message, self.selected_voice)
            else:
                logger.warning(f"VoiceMessageSender: TTS no disponible para '{message}'")
        except Exception as e:
            logger.error(f"VoiceMessageSender: Error en TTS: {e}")
    
    def _say_error(self, message: str):
        """Reproduce mensaje de error por TTS"""
        self._say_feedback(message)
    
    def send_medication_timeout_alert(self, medication_name: str, user_name: str = "Usuario") -> bool:
        """
        Envía alerta de medicamento no confirmado a TODOS los contactos de emergencia.
        Esta función se llama cuando el usuario NO confirma su medicamento en 5 minutos.
        
        Args:
            medication_name (str): Nombre del medicamento
            user_name (str): Nombre del usuario
            
        Returns:
            bool: True si se envió al menos una alerta exitosamente
        """
        logger.info(f"VoiceMessageSender: Enviando alerta de medicamento para '{medication_name}' de {user_name}")
        
        try:
            if not self.db_manager:
                logger.error("VoiceMessageSender: DB manager no disponible para alerta de medicamento")
                return False
            
            # Obtener todos los contactos de emergencia
            with self.db_manager.get_connection() as conn:
                cursor = conn.cursor()
                cursor.execute("""
                    SELECT display_name, telegram_chat_id 
                    FROM contacts 
                    WHERE is_emergency = 1 AND is_active = TRUE
                """)
                emergency_contacts = cursor.fetchall()
            
            if not emergency_contacts:
                logger.warning("VoiceMessageSender: No hay contactos de emergencia configurados")
                return False
            
            # Crear mensaje de alerta específico para medicamento
            from datetime import datetime
            current_time = datetime.now().strftime("%H:%M")
            current_date = datetime.now().strftime("%d/%m/%Y")
            
            alert_message = f"""🚨 ALERTA MEDICAMENTO 🚨

📍 {user_name} NO ha confirmado su medicamento:
💊 {medication_name}

🕐 Hora programada: {current_time}
📅 Fecha: {current_date}

⚠️ Han pasado más de 5 minutos sin confirmación.
Por favor, verifica que esté bien."""
            
            # Enviar a todos los contactos de emergencia
            alerts_sent = 0
            for contact in emergency_contacts:
                try:
                    chat_id = contact['telegram_chat_id']
                    if chat_id and self._send_telegram_message(chat_id, alert_message):
                        alerts_sent += 1
                        logger.info(f"VoiceMessageSender: Alerta enviada a {contact['display_name']} ({chat_id})")
                    else:
                        logger.warning(f"VoiceMessageSender: No se pudo enviar a {contact['display_name']} - chat_id: {chat_id}")
                except Exception as e:
                    logger.error(f"VoiceMessageSender: Error enviando a {contact['display_name']}: {e}")
            
            logger.info(f"VoiceMessageSender: {alerts_sent}/{len(emergency_contacts)} alertas de medicamento enviadas exitosamente")
            return alerts_sent > 0
            
        except Exception as e:
            logger.error(f"VoiceMessageSender: Error general enviando alertas de medicamento: {e}")
            return False

def initialize_voice_message_sender(tts_manager, selected_voice: str, message_ai=None) -> Optional[VoiceMessageSender]:
    """
    Inicializa y retorna una instancia de VoiceMessageSender
    
    Args:
        tts_manager: Gestor de TTS
        selected_voice (str): Voz para TTS
        message_ai: Procesador de mensajes con IA
        
    Returns:
        VoiceMessageSender o None si falla
    """
    try:
        sender = VoiceMessageSender(tts_manager, selected_voice, message_ai)
        return sender
    except Exception as e:
        logger.error(f"Error inicializando VoiceMessageSender: {e}")
        return None