#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
Reminders Core - Asistente Kata
===============================

Sistema completo de recordatorios: interpretacion de tiempo natural,
programacion de alertas y gestion inteligente de medicamentos.

Autor: Asistente Kata
Version: 2.0.0 - Refactoring
"""

# Imports simplificados
try:
    from .time_interpreter import parse_natural_time, format_time_confirmation, calculate_reminder_datetime
    
except ImportError as e:
    # Fallback silencioso
    pass

# Metadata del modulo
__version__ = "2.0.0"
__all__ = ["parse_natural_time", "format_time_confirmation", "calculate_reminder_datetime"]