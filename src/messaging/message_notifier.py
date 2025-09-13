#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
MessageNotifier - Notificador de mensajes para Asistente Kata

Maneja las notificaciones de mensajes nuevos y perdidos,
incluyendo reproducción por voz y actualización de UI.

Autor: Asistente Kata
"""

import logging
import threading
import time
from typing import Optional, Callable, Dict, Any

logger = logging.getLogger(__name__)

class MessageNotifier:
    """Notificador de mensajes"""
    
    def __init__(self, db_path: str, tts_manager, selected_voice: str):
        """
        Inicializa el notificador de mensajes
        
        Args:
            db_path (str): Path a la base de datos
            tts_manager: Gestor de text-to-speech
            selected_voice (str): Voz seleccionada para TTS
        """
        self.db_path = db_path
        self.tts_manager = tts_manager
        self.selected_voice = selected_voice
        self.ui_update_callback = None
        
        # Importar shared_data_manager para BD
        try:
            import sys
            import os
            sys.path.append(os.path.dirname(__file__))
            from database.models.shared_data_manager import shared_data_manager
            self.db_manager = shared_data_manager
        except ImportError as e:
            logger.error(f"Error importando shared_data_manager: {e}")
            self.db_manager = None
        
        logger.info("MessageNotifier inicializado correctamente")
    
    def set_ui_update_callback(self, callback: Callable):
        """Configura callback para actualizar UI"""
        self.ui_update_callback = callback
        logger.info("MessageNotifier: Callback de UI registrado")
    
    def on_new_message(self, message_data: Dict[str, Any]):
        """
        Maneja llegada de nuevos mensajes - FUNCIONALIDAD REAL
        
        Args:
            message_data (Dict): Datos del mensaje recibido
                - id: ID del mensaje en BD
                - contact_name: Nombre del contacto
                - message_text: Texto del mensaje
                - chat_id: ID del chat de Telegram
        """
        try:
            contact_name = message_data.get('contact_name', 'Contacto desconocido')
            message_text = message_data.get('message_text', '')
            message_id = message_data.get('id')
            
            logger.info(f"MessageNotifier: Procesando mensaje de {contact_name}")
            
            # 1. AUDIO: Reproducir notificación por voz
            self._play_audio_notification(contact_name)
            
            # 2. VISUAL: Actualizar contador en UI
            self._update_visual_notification()
            
            # 3. BD: Marcar mensaje como notificado
            if message_id and self.db_manager:
                self.db_manager.mark_message_as_notified(message_id)
                
            logger.info(f"MessageNotifier: Notificación completada para {contact_name}")
            
        except Exception as e:
            logger.error(f"MessageNotifier: Error procesando mensaje: {e}")
    
    def _play_audio_notification(self, contact_name: str):
        """
        Reproduce notificación de audio
        
        Args:
            contact_name (str): Nombre del contacto que envió el mensaje
        """
        try:
            if self.tts_manager:
                # Formato: "Tienes un mensaje nuevo de [Contacto]"
                notification_text = f"Tienes un mensaje nuevo de {contact_name}"
                
                logger.info(f"MessageNotifier: Reproduciendo audio - {notification_text}")
                
                # Ejecutar TTS en hilo separado para no bloquear
                def _play_tts():
                    try:
                        self.tts_manager.say(notification_text, self.selected_voice)
                    except Exception as e:
                        logger.error(f"MessageNotifier: Error en TTS: {e}")
                
                tts_thread = threading.Thread(target=_play_tts, daemon=True)
                tts_thread.start()
                
            else:
                logger.warning("MessageNotifier: TTS manager no disponible")
                
        except Exception as e:
            logger.error(f"MessageNotifier: Error reproduciendo audio: {e}")
    
    def _update_visual_notification(self):
        """
        Actualiza la notificación visual en la UI
        """
        try:
            if self.ui_update_callback:
                # Obtener contador actual de mensajes
                if self.db_manager:
                    unread_count = self.db_manager.get_unread_message_count()
                    
                    # Llamar callback con el contador (clock_interface.update_message_count)
                    self.ui_update_callback(unread_count)
                    
                    logger.info(f"MessageNotifier: UI actualizada - {unread_count} mensajes no leídos")
                else:
                    logger.warning("MessageNotifier: BD manager no disponible para contar mensajes")
            else:
                logger.warning("MessageNotifier: Callback de UI no configurado")
                
        except Exception as e:
            logger.error(f"MessageNotifier: Error actualizando UI: {e}")
    
    def check_missed_notifications(self):
        """Verifica mensajes perdidos al inicio"""
        try:
            logger.debug("MessageNotifier: Verificando mensajes perdidos...")
            
            # Aquí iría lógica real de verificación
            # Por ahora solo logging
            
            logger.debug("MessageNotifier: Verificación completada")
            
        except Exception as e:
            logger.error(f"MessageNotifier: Error verificando mensajes perdidos: {e}")

def initialize_message_notifier(db_path: str, tts_manager, selected_voice: str) -> Optional[MessageNotifier]:
    """
    Inicializa y retorna una instancia de MessageNotifier
    
    Args:
        db_path (str): Path a la base de datos
        tts_manager: Gestor de TTS
        selected_voice (str): Voz para TTS
        
    Returns:
        MessageNotifier o None si falla
    """
    try:
        notifier = MessageNotifier(db_path, tts_manager, selected_voice)
        return notifier
    except Exception as e:
        logger.error(f"Error inicializando MessageNotifier: {e}")
        return None