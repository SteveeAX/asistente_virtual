#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
Asistente Kata - Paquete Principal
==================================

Punto de entrada principal para todos los modulos del asistente.
Proporciona compatibilidad hacia atras durante la refactorizacion.

Autor: Asistente Kata
Version: 2.0.0 - Refactoring
"""

__version__ = "2.0.0"
__author__ = "Asistente Kata"

# ============================================
# IMPORTS DE COMPATIBILIDAD
# ============================================
# Estos imports permitiran que el codigo existente siga funcionando
# mientras migramos gradualmente a la nueva estructura

# Imports de compatibilidad hacia atras (ACTIVADOS)
try:
    from .utils import system_actions, firestore_logger
    from .core.audio import tts_manager, stt_manager, wakeword_detector
    from .core.hardware import button_manager  
    from .core.smart_home import smart_home_manager
    from .core.reminders import parse_natural_time, format_time_confirmation, calculate_reminder_datetime
    from .messaging import (VoiceMessageSender, MessageReceiver, MessageReader, 
                           MessageNotifier, contact_normalizer, voice_message_sender)
    from .ui.desktop import ClockInterface, ReminderTab, ContactTab
    from .ui.web import web_app, web_server
    from .ai import (parse_intent, parse_send_message_intent, INTENTS,
                     MessageAI, message_ai, VoiceReminderManager, voice_reminder_manager)
    from .app import (KataApp, initialize_app, run_app, 
                      get_reminders_service, get_current_user_name)
    
    # Hacer disponibles en el nivel superior para compatibilidad
    import sys
    current_module = sys.modules[__name__]
    
    # Agregar modulos al namespace para imports directos
    setattr(current_module, 'system_actions', system_actions)
    setattr(current_module, 'firestore_logger', firestore_logger)
    setattr(current_module, 'tts_manager', tts_manager)
    setattr(current_module, 'stt_manager', stt_manager)
    setattr(current_module, 'wakeword_detector', wakeword_detector)
    setattr(current_module, 'button_manager', button_manager)
    setattr(current_module, 'smart_home_manager', smart_home_manager)
    
    # Modulos de recordatorios
    setattr(current_module, 'parse_natural_time', parse_natural_time)
    setattr(current_module, 'format_time_confirmation', format_time_confirmation) 
    setattr(current_module, 'calculate_reminder_datetime', calculate_reminder_datetime)
    
    # Modulos de mensajeria
    setattr(current_module, 'VoiceMessageSender', VoiceMessageSender)
    setattr(current_module, 'voice_message_sender', voice_message_sender)
    setattr(current_module, 'MessageReceiver', MessageReceiver)
    setattr(current_module, 'MessageReader', MessageReader)
    setattr(current_module, 'MessageNotifier', MessageNotifier)
    setattr(current_module, 'contact_normalizer', contact_normalizer)
    
    # Interfaces de usuario
    setattr(current_module, 'ClockInterface', ClockInterface)
    setattr(current_module, 'ReminderTab', ReminderTab)
    setattr(current_module, 'ContactTab', ContactTab)
    setattr(current_module, 'web_app', web_app)
    setattr(current_module, 'web_server', web_server)
    
    # Modulos de IA
    setattr(current_module, 'parse_intent', parse_intent)
    setattr(current_module, 'parse_send_message_intent', parse_send_message_intent)
    setattr(current_module, 'INTENTS', INTENTS)
    setattr(current_module, 'MessageAI', MessageAI)
    setattr(current_module, 'message_ai', message_ai)
    setattr(current_module, 'VoiceReminderManager', VoiceReminderManager)
    setattr(current_module, 'voice_reminder_manager', voice_reminder_manager)
    
    # Modulos de aplicación principal
    setattr(current_module, 'KataApp', KataApp)
    setattr(current_module, 'initialize_app', initialize_app)
    setattr(current_module, 'run_app', run_app)
    setattr(current_module, 'get_reminders_service', get_reminders_service)
    setattr(current_module, 'get_current_user_name', get_current_user_name)
    
except ImportError as e:
    # Fallback silencioso durante la migracion
    pass

# ============================================
# CONFIGURACION GLOBAL
# ============================================

import sys
from pathlib import Path

# Agregar el directorio src al path para imports relativos
SRC_DIR = Path(__file__).parent
PROJECT_ROOT = SRC_DIR.parent

if str(SRC_DIR) not in sys.path:
    sys.path.insert(0, str(SRC_DIR))

if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

# ============================================
# METADATA DEL PROYECTO
# ============================================

PACKAGE_INFO = {
    "name": "asistente-kata",
    "version": __version__,
    "description": "Asistente de voz para adultos mayores con Raspberry Pi",
    "author": __author__,
    "python_requires": ">=3.8",
}

# ============================================
# FUNCIONES DE UTILIDAD
# ============================================

def get_package_info():
    """Retorna informacion del paquete."""
    return PACKAGE_INFO.copy()

def print_version():
    """Imprime la version actual."""
    print(f"Asistente Kata v{__version__}")

# ============================================
# VALIDACION DEL ENTORNO
# ============================================

def validate_environment():
    """Valida que el entorno este correctamente configurado."""
    try:
        # Importar configuracion centralizada
        import config
        config.validate_config()
        return True
    except Exception as e:
        print(f"Error validando entorno: {e}")
        return False

# ============================================
# INICIALIZACION
# ============================================

if __name__ == "__main__":
    print_version()
    if validate_environment():
        print("Entorno validado correctamente")
    else:
        print("Problemas en la validacion del entorno")