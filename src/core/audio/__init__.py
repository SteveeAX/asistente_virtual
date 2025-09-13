#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
Audio Core - Asistente Kata
============================

Modulos core de audio: TTS, STT y Wake Word Detection.

Autor: Asistente Kata  
Version: 2.0.0 - Refactoring
"""

# Imports para compatibilidad hacia atras
from .tts_manager import *
from .stt_manager import *  
from .wakeword_detector import *

# Metadata del modulo
__version__ = "2.0.0"
__all__ = ["tts_manager", "stt_manager", "wakeword_detector"]