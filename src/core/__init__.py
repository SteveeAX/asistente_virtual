#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
Core Modules - Asistente Kata
==============================

Modulos centrales del sistema: audio, hardware, smart home y recordatorios.

Autor: Asistente Kata
Version: 2.0.0 - Refactoring
"""

# Imports de submodulos core
try:
    from .audio import *
    from .hardware import *
    from .smart_home import *
    from .reminders import *
    
except ImportError as e:
    print(f"Warning: Error importando modulos core: {e}")

# Metadata del modulo
__version__ = "2.0.0"
__all__ = [
    # Audio
    "tts_manager", "stt_manager", "wakeword_detector",
    
    # Hardware  
    "button_manager",
    
    # Smart Home
    "smart_home_manager",
    
    # Reminders
    "parse_natural_time", "format_time_confirmation", "calculate_reminder_datetime"
]