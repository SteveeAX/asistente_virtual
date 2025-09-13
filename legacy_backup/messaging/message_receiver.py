#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
MessageReceiver - Receptor de mensajes de Telegram para Asistente Kata

Maneja la recepción de mensajes desde Telegram usando el bot token
y los almacena en la base de datos compartida.

Autor: Asistente Kata
"""

import logging
import threading
import time
import os
import requests
import json
from typing import List, Dict, Any, Optional, Callable

logger = logging.getLogger(__name__)

class MessageReceiver:
    """Receptor de mensajes de Telegram"""
    
    def __init__(self, bot_token: str, db_path: str):
        """
        Inicializa el receptor de mensajes
        
        Args:
            bot_token (str): Token del bot de Telegram
            db_path (str): Path a la base de datos compartida
        """
        self.bot_token = bot_token
        self.db_path = db_path
        self.api_url = f"https://api.telegram.org/bot{bot_token}"
        self.is_running = False
        self.polling_thread = None
        self.last_update_id = 0
        self.new_message_callbacks = []
        
        # Importar shared_data_manager para BD
        try:
            import sys
            sys.path.append(os.path.dirname(__file__))
            from database.models.shared_data_manager import shared_data_manager
            self.db_manager = shared_data_manager
        except ImportError as e:
            logger.error(f"Error importando shared_data_manager: {e}")
            self.db_manager = None
        
        # Mapeo de chat_id a nombres conocidos
        self.chat_id_to_contact = {}
        
        # Inicializar contactos conocidos desde BD
        self._load_known_contacts()
        
        logger.info(f"Cargados {len(self.known_contacts)} contactos conocidos para validación")
        logger.info("MessageReceiver inicializado correctamente")
    
    def _load_known_contacts(self):
        """Carga contactos conocidos desde la base de datos"""
        try:
            if self.db_manager:
                # Obtener contactos de Telegram existentes
                with self.db_manager.get_connection() as conn:
                    cursor = conn.cursor()
                    cursor.execute("""
                        SELECT display_name, details 
                        FROM contacts 
                        WHERE platform = 'telegram' AND is_active = TRUE
                    """)
                    
                    contacts = {}
                    for row in cursor.fetchall():
                        contact_name = row['display_name'].lower()
                        chat_id = row['details']
                        contacts[contact_name] = {
                            "name": row['display_name'],
                            "chat_id": chat_id
                        }
                        # Mapeo inverso para lookups rápidos
                        self.chat_id_to_contact[chat_id] = row['display_name']
                    
                    self.known_contacts = contacts
                    logger.info(f"Contactos Telegram cargados desde BD: {list(contacts.keys())}")
            else:
                # Fallback: contactos hardcodeados
                self.known_contacts = {
                    "steveen": {"name": "Steveen", "chat_id": None},
                    "hijo": {"name": "Hijo", "chat_id": None}
                }
                logger.warning("Usando contactos hardcodeados (BD no disponible)")
                
        except Exception as e:
            logger.error(f"Error cargando contactos: {e}")
            self.known_contacts = {}
    
    def add_new_message_callback(self, callback: Callable):
        """Añade callback para nuevos mensajes"""
        self.new_message_callbacks.append(callback)
    
    def start_polling(self):
        """Inicia el polling de mensajes"""
        try:
            if not self.is_running:
                self.is_running = True
                self.polling_thread = threading.Thread(target=self._polling_loop, daemon=True)
                self.polling_thread.start()
                
                logger.info("MessageReceiver: Iniciando sistema de polling...")
                time.sleep(0.1)  # Dar tiempo al hilo para iniciar
                logger.info("MessageReceiver: 🚀 POLLING LOOP INICIADO - Empezando a escuchar mensajes...")
                logger.info("MessageReceiver: ✅ Hilo de polling iniciado correctamente")
                
        except Exception as e:
            logger.error(f"MessageReceiver: Error iniciando polling: {e}")
            self.is_running = False
    
    def stop_polling(self):
        """Detiene el polling de mensajes"""
        if self.is_running:
            self.is_running = False
            if self.polling_thread:
                self.polling_thread.join(timeout=2.0)
            logger.info("MessageReceiver: Polling detenido")
    
    def _polling_loop(self):
        """Loop principal de polling de Telegram"""
        logger.info("MessageReceiver: Iniciando loop de polling real")
        
        while self.is_running:
            try:
                # Obtener actualizaciones de Telegram
                updates = self._get_updates()
                
                if updates:
                    for update in updates:
                        self._process_update(update)
                        
                # Pausa entre verificaciones
                time.sleep(2)  # Verificar cada 2 segundos
                
            except Exception as e:
                logger.error(f"MessageReceiver: Error en polling loop: {e}")
                time.sleep(10)  # Pausa más larga en caso de error
    
    def _get_updates(self) -> List[Dict[str, Any]]:
        """
        Obtiene actualizaciones de Telegram usando long polling
        
        Returns:
            List[Dict]: Lista de actualizaciones
        """
        try:
            url = f"{self.api_url}/getUpdates"
            params = {
                'offset': self.last_update_id + 1,
                'timeout': 30,  # Long polling de 30 segundos
                'allowed_updates': ['message']  # Solo mensajes
            }
            
            response = requests.get(url, params=params, timeout=35)
            response.raise_for_status()
            
            data = response.json()
            
            if data['ok']:
                updates = data['result']
                if updates:
                    # Actualizar last_update_id
                    self.last_update_id = max(update['update_id'] for update in updates)
                    logger.debug(f"MessageReceiver: Recibidas {len(updates)} actualizaciones")
                
                return updates
            else:
                logger.error(f"MessageReceiver: Error de API Telegram: {data.get('description')}")
                return []
                
        except requests.exceptions.Timeout:
            # Timeout es normal en long polling
            return []
        except requests.exceptions.RequestException as e:
            logger.error(f"MessageReceiver: Error de red: {e}")
            return []
        except Exception as e:
            logger.error(f"MessageReceiver: Error obteniendo actualizaciones: {e}")
            return []
    
    def _process_update(self, update: Dict[str, Any]):
        """
        Procesa una actualización de Telegram
        
        Args:
            update (Dict): Actualización de Telegram
        """
        try:
            if 'message' not in update:
                return
            
            message = update['message']
            
            # Solo procesar mensajes de texto
            if 'text' not in message:
                return
            
            chat_id = str(message['chat']['id'])
            message_text = message['text']
            telegram_message_id = message['message_id']
            
            # Determinar nombre del contacto
            contact_name = self._get_contact_name(message['from'], chat_id)
            
            # Guardar mensaje en BD
            if self.db_manager:
                message_id = self.db_manager.add_message(
                    contact_name=contact_name,
                    message_text=message_text,
                    telegram_message_id=telegram_message_id,
                    sender_chat_id=chat_id
                )
                
                if message_id > 0:
                    logger.info(f"MessageReceiver: Nuevo mensaje guardado - ID: {message_id}, De: {contact_name}")
                    
                    # Notificar a callbacks
                    message_data = {
                        'id': message_id,
                        'contact_name': contact_name,
                        'message_text': message_text,
                        'chat_id': chat_id,
                        'telegram_message_id': telegram_message_id
                    }
                    
                    self._notify_callbacks(message_data)
                else:
                    logger.error("MessageReceiver: Error guardando mensaje en BD")
            else:
                logger.error("MessageReceiver: BD no disponible para guardar mensaje")
                
        except Exception as e:
            logger.error(f"MessageReceiver: Error procesando actualización: {e}")
    
    def _get_contact_name(self, from_user: Dict[str, Any], chat_id: str) -> str:
        """
        Determina el nombre del contacto basado en la información de Telegram
        
        Args:
            from_user (Dict): Información del usuario de Telegram
            chat_id (str): ID del chat
            
        Returns:
            str: Nombre del contacto
        """
        # Primero intentar mapeo por chat_id
        if chat_id in self.chat_id_to_contact:
            return self.chat_id_to_contact[chat_id]
        
        # Intentar por username de Telegram
        if 'username' in from_user:
            username = from_user['username'].lower()
            for contact_key, contact_data in self.known_contacts.items():
                if username == contact_key or username in contact_data.get('name', '').lower():
                    # Actualizar mapeo para próximas veces
                    self.chat_id_to_contact[chat_id] = contact_data['name']
                    # Actualizar BD también
                    self._update_contact_chat_id(contact_data['name'], chat_id)
                    return contact_data['name']
        
        # Fallback: usar nombre de Telegram
        telegram_name = from_user.get('first_name', '')
        if from_user.get('last_name'):
            telegram_name += f" {from_user['last_name']}"
        
        # Si está vacío, usar username o ID
        if not telegram_name:
            telegram_name = from_user.get('username', f"User_{chat_id[-4:]}")
        
        # Guardar nuevo contacto
        self.chat_id_to_contact[chat_id] = telegram_name
        
        return telegram_name
    
    def _update_contact_chat_id(self, contact_name: str, chat_id: str):
        """
        Actualiza el chat_id de un contacto existente en la BD
        
        Args:
            contact_name (str): Nombre del contacto
            chat_id (str): ID del chat de Telegram
        """
        try:
            if self.db_manager:
                with self.db_manager.get_connection() as conn:
                    cursor = conn.cursor()
                    cursor.execute("""
                        UPDATE contacts 
                        SET details = ? 
                        WHERE display_name = ? AND platform = 'telegram'
                    """, (chat_id, contact_name))
                    conn.commit()
                    
                    if cursor.rowcount > 0:
                        logger.info(f"MessageReceiver: Chat ID actualizado para {contact_name}: {chat_id}")
                        
        except Exception as e:
            logger.error(f"MessageReceiver: Error actualizando chat ID: {e}")
    
    def _notify_callbacks(self, message_data: Dict[str, Any]):
        """
        Notifica a todos los callbacks registrados sobre nuevos mensajes
        
        Args:
            message_data (Dict): Datos del mensaje
        """
        for callback in self.new_message_callbacks:
            try:
                callback(message_data)
            except Exception as e:
                logger.error(f"MessageReceiver: Error en callback: {e}")

def initialize_message_receiver(bot_token: str, db_path: str) -> Optional[MessageReceiver]:
    """
    Inicializa y retorna una instancia de MessageReceiver
    
    Args:
        bot_token (str): Token del bot de Telegram
        db_path (str): Path a la base de datos
        
    Returns:
        MessageReceiver o None si falla
    """
    try:
        receiver = MessageReceiver(bot_token, db_path)
        return receiver
    except Exception as e:
        logger.error(f"Error inicializando MessageReceiver: {e}")
        return None