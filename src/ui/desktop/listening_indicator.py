#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
ListeningIndicator - Indicador visual de escucha para Asistente Virtual

Proporciona un indicador visual animado que muestra cuando el asistente
está escuchando comandos de voz.

Autor: SteveeAX
"""

import customtkinter as ctk
import logging
import threading
import time

logger = logging.getLogger(__name__)

class ListeningIndicator:
    """Indicador visual animado para mostrar estado de escucha"""
    
    def __init__(self, parent_frame):
        """
        Inicializa el indicador de escucha
        
        Args:
            parent_frame: Frame padre donde se mostrará el indicador
        """
        self.parent_frame = parent_frame
        self.is_visible = False
        self.is_animating = False
        self.animation_thread = None
        
        # Crear frame contenedor para el indicador
        self.indicator_frame = ctk.CTkFrame(
            parent_frame,
            fg_color="transparent",
            height=60,
            width=200
        )
        
        # Crear label para el texto indicador
        self.indicator_label = ctk.CTkLabel(
            self.indicator_frame,
            text="🎤 Escuchando...",
            font=ctk.CTkFont(size=16, weight="bold"),
            text_color="#00ff00"  # Verde brillante
        )
        self.indicator_label.pack(pady=10)
        
        logger.info("LISTENING_INDICATOR: Inicializado correctamente")
    
    def show(self, start_animation=True):
        """
        Muestra el indicador de escucha
        
        Args:
            start_animation (bool): Si debe iniciar animación
        """
        try:
            if not self.is_visible:
                self.indicator_frame.pack(pady=10)
                self.is_visible = True
                
                if start_animation:
                    self._start_animation()
                
                logger.info("LISTENING_INDICATOR: Mostrado con animación" if start_animation else "LISTENING_INDICATOR: Mostrado sin animación")
                
        except Exception as e:
            logger.error(f"LISTENING_INDICATOR: Error mostrando indicador: {e}")
    
    def hide(self):
        """Oculta el indicador de escucha"""
        try:
            if self.is_visible:
                self._stop_animation()
                self.indicator_frame.pack_forget()
                self.is_visible = False
                logger.info("LISTENING_INDICATOR: Ocultado")
                
        except Exception as e:
            logger.error(f"LISTENING_INDICATOR: Error ocultando indicador: {e}")
    
    def is_shown(self):
        """Retorna si el indicador está visible"""
        return self.is_visible
    
    def _start_animation(self):
        """Inicia la animación del indicador"""
        if not self.is_animating:
            self.is_animating = True
            self.animation_thread = threading.Thread(target=self._animate_loop, daemon=True)
            self.animation_thread.start()
            logger.info("LISTENING_INDICATOR: Animación iniciada")
    
    def _stop_animation(self):
        """Detiene la animación del indicador"""
        if self.is_animating:
            self.is_animating = False
            if self.animation_thread:
                self.animation_thread.join(timeout=1.0)
            logger.info("LISTENING_INDICATOR: Animación detenida")
    
    def _animate_loop(self):
        """Loop principal de animación"""
        animation_states = [
            "🎤 Escuchando...",
            "🎤 Escuchando.",
            "🎤 Escuchando..",
            "🎤 Escuchando..."
        ]
        
        state_index = 0
        
        while self.is_animating and self.is_visible:
            try:
                # Actualizar texto en el hilo principal
                if hasattr(self.indicator_label, 'configure'):
                    self.indicator_label.configure(text=animation_states[state_index])
                
                state_index = (state_index + 1) % len(animation_states)
                time.sleep(0.5)  # Cambiar cada 500ms
                
            except Exception as e:
                logger.error(f"LISTENING_INDICATOR: Error en animación: {e}")
                break
        
        logger.debug("LISTENING_INDICATOR: Loop de animación terminado")