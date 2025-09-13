#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
Web UI - Asistente Virtual
========================

Servidor web Flask para administracion remota del sistema.

Autor: SteveeAX
Version: 2.0.0 - Refactoring
"""

# Import principal de la aplicacion web
try:
    from .app import app as web_app
    from .app import *
    
    # Alias para compatibilidad
    web_server = web_app
    
except ImportError as e:
    print(f"Warning: Error importando aplicacion web: {e}")
    web_app = None
    web_server = None

# Metadata del modulo
__version__ = "2.0.0"
__all__ = ["web_app", "web_server"]