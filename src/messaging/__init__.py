#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
Messaging System - Asistente Kata
==================================

Sistema completo de mensajeria bidireccional via Telegram.
Incluye envio por voz, recepcion, notificaciones y normalizacion de contactos.

Autor: Asistente Kata
Version: 2.0.0 - Refactoring
"""

# Imports para compatibilidad hacia atras
try:
    from .voice_sender import VoiceMessageSender
    from .message_receiver import MessageReceiver  
    from .message_reader import MessageReader
    from .message_notifier import MessageNotifier
    from .contact_normalizer import contact_normalizer
    
    # Alias para compatibilidad con nombres anteriores
    voice_message_sender = VoiceMessageSender
    message_receiver = MessageReceiver
    
except ImportError as e:
    # Fallback durante la migracion
    print(f"Warning: Error importando modulos de mensajeria: {e}")

# Metadata del modulo
__version__ = "2.0.0"
__all__ = [
    "VoiceMessageSender", 
    "MessageReceiver", 
    "MessageReader",
    "MessageNotifier", 
    "contact_normalizer",
    # Aliases de compatibilidad
    "voice_message_sender",
    "message_receiver"
]