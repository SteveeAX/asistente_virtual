#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
App Module - Asistente Kata
============================

Modulo principal de aplicacion con punto de entrada organizado.
Exporta la aplicacion principal y funciones de inicializacion.

Autor: Asistente Kata
Version: 2.0.0 - Refactoring
"""

# Imports principales
try:
    from .main_app import KataApp, initialize_app, run_app
    
    # Funciones helper
    from .main_app import get_reminders_service, get_current_user_name
    
    __all__ = [
        # Clase principal
        "KataApp",
        
        # Funciones de aplicacion
        "initialize_app",
        "run_app",
        
        # Funciones helper
        "get_reminders_service",
        "get_current_user_name"
    ]
    
except ImportError as e:
    # Fallback silencioso para compatibilidad
    print(f"Warning: Error importando modulos de app: {e}")
    __all__ = []

# Metadata del modulo
__version__ = "2.0.0"