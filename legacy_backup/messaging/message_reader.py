#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
MessageReader - Lector de mensajes para Asistente Kata

Maneja la lectura y reproducción por voz de mensajes almacenados
en la base de datos compartida. Implementa la funcionalidad original:
- Leer los 3 mensajes MÁS ANTIGUOS
- Formato: "[Contacto] dice, [texto]"
- Eliminar después de leer
- Actualizar UI

Autor: Asistente Kata
"""

import logging
import threading
from typing import Optional, Callable

logger = logging.getLogger(__name__)

class MessageReader:
    """Lector de mensajes con TTS - FUNCIONALIDAD COMPLETA"""
    
    def __init__(self, db_path: str, tts_manager, selected_voice: str):
        """
        Inicializa el lector de mensajes
        
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
        
        logger.info("MessageReader inicializado correctamente")
    
    def set_ui_update_callback(self, callback: Callable):
        """Configura callback para actualizar UI"""
        self.ui_update_callback = callback
        logger.info("MessageReader: Callback de UI registrado")
    
    def has_unread_messages(self) -> bool:
        """
        Verifica si hay mensajes no leídos - FUNCIONALIDAD REAL
        
        Returns:
            bool: True si hay mensajes no leídos
        """
        try:
            if self.db_manager:
                count = self.db_manager.get_unread_message_count()
                return count > 0
            else:
                logger.warning("MessageReader: BD manager no disponible")
                return False
        except Exception as e:
            logger.error(f"MessageReader: Error verificando mensajes: {e}")
            return False
    
    def read_messages_sync(self, max_messages: int = 3) -> bool:
        """
        Lee mensajes de forma SÍNCRONA - FUNCIONALIDAD ORIGINAL
        
        Args:
            max_messages (int): Máximo mensajes a leer (default 3)
            
        Returns:
            bool: True si se leyeron mensajes exitosamente
        """
        try:
            if not self.db_manager:
                logger.error("MessageReader: BD manager no disponible")
                return False
            
            if not self.tts_manager:
                logger.error("MessageReader: TTS manager no disponible")
                return False
            
            # Obtener los mensajes MÁS ANTIGUOS (como especificado)
            messages = self.db_manager.get_unread_messages(limit=max_messages)
            
            if not messages:
                logger.info("MessageReader: No hay mensajes para leer")
                self.tts_manager.say("No tienes mensajes nuevos", self.selected_voice)
                return True
            
            logger.info(f"MessageReader: Leyendo {len(messages)} mensajes...")
            
            # Leer cada mensaje con el formato original: "[Contacto] dice, [texto]"
            for i, message in enumerate(messages, 1):
                contact_name = message['contact_name']
                message_text = message['message_text']
                
                # Formato TTS original: "[Contacto] dice, [texto]"
                tts_text = f"{contact_name} dice, {message_text}"
                
                logger.info(f"MessageReader: Leyendo mensaje {i}/{len(messages)} de {contact_name}")
                
                # Reproducir mensaje
                self.tts_manager.say(tts_text, self.selected_voice)
            
            # Marcar mensajes como leídos y ELIMINAR (como funcionalidad original)
            message_ids = [msg['id'] for msg in messages]
            success = self.db_manager.mark_messages_as_read(message_ids)
            
            if success:
                logger.info(f"MessageReader: {len(messages)} mensajes eliminados después de leer")
                
                # Actualizar UI
                self._update_ui_after_reading()
            else:
                logger.error("MessageReader: Error eliminando mensajes después de leer")
            
            return success
            
        except Exception as e:
            logger.error(f"MessageReader: Error leyendo mensajes: {e}")
            return False
    
    def read_messages_async(self, max_messages: int = 3):
        """
        Lee mensajes de forma asíncrona (wrapper para compatibilidad)
        
        Args:
            max_messages (int): Máximo mensajes a leer
        """
        def _read_messages_thread():
            try:
                self.read_messages_sync(max_messages)
            except Exception as e:
                logger.error(f"MessageReader: Error en hilo asíncrono: {e}")
        
        # Ejecutar en hilo separado
        thread = threading.Thread(target=_read_messages_thread, daemon=True)
        thread.start()
        logger.info(f"MessageReader: Lectura asíncrona iniciada para hasta {max_messages} mensajes")
    
    def _update_ui_after_reading(self):
        """
        Actualiza la UI después de leer mensajes
        """
        try:
            if self.ui_update_callback and self.db_manager:
                # Obtener nuevo contador después de eliminar mensajes
                updated_count = self.db_manager.get_unread_message_count()
                
                # Actualizar UI con nuevo contador
                self.ui_update_callback(updated_count)
                
                logger.info(f"MessageReader: UI actualizada - {updated_count} mensajes restantes")
            else:
                logger.warning("MessageReader: No se pudo actualizar UI (callback o BD no disponible)")
                
        except Exception as e:
            logger.error(f"MessageReader: Error actualizando UI: {e}")

def initialize_message_reader(db_path: str, tts_manager, selected_voice: str) -> Optional[MessageReader]:
    """
    Inicializa y retorna una instancia de MessageReader
    
    Args:
        db_path (str): Path a la base de datos
        tts_manager: Gestor de TTS
        selected_voice (str): Voz para TTS
        
    Returns:
        MessageReader o None si falla
    """
    try:
        reader = MessageReader(db_path, tts_manager, selected_voice)
        return reader
    except Exception as e:
        logger.error(f"Error inicializando MessageReader: {e}")
        return None