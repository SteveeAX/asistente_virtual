#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
Desktop UI - Asistente Virtual
============================

Interfaces de usuario de escritorio: reloj, tabs administrativas, etc.

Autor: SteveeAX
Version: 2.0.0 - Refactoring
"""

# Imports para compatibilidad hacia atras
try:
    from .listening_indicator import ListeningIndicator
    from .blue_gradient_bar import BlueGradientBar
    from .clock_interface import ClockInterface
    from .reminder_tab import ReminderTab
    from .contact_tab import ContactTab
    
except ImportError as e:
    print(f"Warning: Error importando interfaces de escritorio: {e}")

# Metadata del modulo
__version__ = "2.0.0"
__all__ = ["ClockInterface", "ReminderTab", "ContactTab", "ListeningIndicator", "BlueGradientBar"]