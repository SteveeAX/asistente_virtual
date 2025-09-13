#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
Artificial Intelligence - Asistente Kata
=========================================

Modulos de inteligencia artificial: reconocimiento de intenciones, 
procesamiento de mensajes con IA y gestion inteligente de recordatorios.

Autor: Asistente Kata
Version: 2.0.0 - Refactoring
"""

# Imports para compatibilidad hacia atras
try:
    from .intent_manager import *
    from .message_ai import MessageAI
    from .voice_reminder_manager import VoiceReminderManager, voice_reminder_manager
    
    # Alias para compatibilidad
    message_ai = MessageAI
    
except ImportError as e:
    print(f"Warning: Error importando modulos de IA: {e}")

# Metadata del modulo
__version__ = "2.0.0"
__all__ = [
    # Intent Manager
    "parse_intent", "parse_send_message_intent", "INTENTS",
    
    # Message AI  
    "MessageAI", "message_ai",
    
    # Voice Reminder Manager
    "VoiceReminderManager", "voice_reminder_manager"
]