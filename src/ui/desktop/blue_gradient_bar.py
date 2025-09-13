#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
BlueGradientBar - Barra azul degradada para indicar escucha activa

Proporciona una barra horizontal con gradiente azul que aparece en la parte 
inferior de la pantalla cuando el asistente está escuchando.

Características:
- Gradiente azul suave
- Posicionamiento absolute para evitar conflictos de layout
- Animación sutil opcional
- Optimizado para rendimiento

Autor: Asistente Kata
"""

import customtkinter as ctk
import tkinter as tk
from PIL import Image, ImageDraw, ImageTk
import logging
import threading
import time

logger = logging.getLogger(__name__)

class BlueGradientBar:
    """Barra azul degradada para indicador de escucha"""
    
    def __init__(self, parent_window):
        """
        Inicializa la barra de gradiente azul
        
        Args:
            parent_window: Ventana padre donde se mostrará la barra
        """
        self.parent_window = parent_window
        self.is_visible = False
        self.is_animating = False
        self.animation_thread = None
        
        # Configuración visual
        self.bar_height = 60  # Altura de la barra en pixels (muy visible - 2.5x más)
        self.bar_width = None  # Se calculará dinámicamente
        self.gradient_colors = [
            "#003d82",  # Azul oscuro pero más brillante (izquierda)
            "#0074D9",  # Azul medio brillante
            "#4da6ff",  # Azul claro brillante (centro)
            "#0074D9",  # Azul medio brillante  
            "#003d82"   # Azul oscuro pero más brillante (derecha)
        ]
        
        # Cache para la imagen del gradiente
        self._gradient_image = None
        self._gradient_photo = None
        
        # Crear canvas para la barra (inicialmente oculto)
        self.canvas = tk.Canvas(
            parent_window,
            height=self.bar_height,
            highlightthickness=0,
            bg='black'  # Usar color fijo compatible
        )
        
        logger.info("BLUE_GRADIENT_BAR: Inicializado correctamente")
    
    def _create_gradient_image(self, width):
        """
        Crea imagen de gradiente azul optimizada
        
        Args:
            width (int): Ancho de la barra en pixels
        """
        try:
            # Solo recrear si el ancho cambió
            if self._gradient_image and self._gradient_image.size[0] == width:
                return
            
            height = self.bar_height
            image = Image.new('RGB', (width, height))
            draw = ImageDraw.Draw(image)
            
            # Crear gradiente horizontal
            for x in range(width):
                # Calcular posición en el gradiente (0.0 a 1.0)
                position = x / (width - 1) if width > 1 else 0
                
                # Interpolar entre colores del gradiente
                color = self._interpolate_gradient_color(position)
                
                # Dibujar línea vertical con el color calculado
                draw.line([(x, 0), (x, height - 1)], fill=color)
            
            # Convertir a PhotoImage para Tkinter
            self._gradient_image = image
            self._gradient_photo = ImageTk.PhotoImage(image)
            
            logger.debug(f"BLUE_GRADIENT_BAR: Gradiente creado ({width}x{height})")
            
        except Exception as e:
            logger.error(f"BLUE_GRADIENT_BAR: Error creando gradiente: {e}")
    
    def _interpolate_gradient_color(self, position):
        """
        Interpola color en el gradiente basado en la posición
        
        Args:
            position (float): Posición de 0.0 a 1.0
            
        Returns:
            tuple: Color RGB
        """
        try:
            # Mapear posición a segmentos del gradiente
            num_segments = len(self.gradient_colors) - 1
            segment_size = 1.0 / num_segments
            segment_index = int(position / segment_size)
            
            # Manejar caso edge (posición = 1.0)
            if segment_index >= num_segments:
                segment_index = num_segments - 1
            
            # Calcular posición dentro del segmento (0.0 a 1.0)
            local_position = (position - segment_index * segment_size) / segment_size
            
            # Obtener colores del segmento
            color1_hex = self.gradient_colors[segment_index]
            color2_hex = self.gradient_colors[segment_index + 1]
            
            # Convertir hex a RGB
            color1 = tuple(int(color1_hex[i:i+2], 16) for i in (1, 3, 5))
            color2 = tuple(int(color2_hex[i:i+2], 16) for i in (1, 3, 5))
            
            # Interpolación lineal entre los dos colores
            r = int(color1[0] + (color2[0] - color1[0]) * local_position)
            g = int(color1[1] + (color2[1] - color1[1]) * local_position)
            b = int(color1[2] + (color2[2] - color1[2]) * local_position)
            
            return (r, g, b)
            
        except Exception as e:
            logger.error(f"BLUE_GRADIENT_BAR: Error interpolando color: {e}")
            return (0, 116, 217)  # Color azul fallback
    
    def show(self, animate=False):
        """
        Muestra la barra de gradiente en la parte inferior de la pantalla
        
        Args:
            animate (bool): Si debe mostrar animación sutil
        """
        try:
            if self.is_visible:
                return
            
            # Obtener dimensiones de la ventana padre
            self.parent_window.update_idletasks()
            window_width = self.parent_window.winfo_width()
            window_height = self.parent_window.winfo_height()
            
            # Configurar canvas
            self.canvas.configure(width=window_width)
            self.bar_width = window_width
            
            # Crear imagen del gradiente
            self._create_gradient_image(window_width)
            
            # Limpiar canvas y dibujar gradiente
            self.canvas.delete("all")
            if self._gradient_photo:
                self.canvas.create_image(0, 0, anchor='nw', image=self._gradient_photo)
            
            # Posicionar en la parte inferior usando place()
            self.canvas.place(
                x=0, 
                y=window_height - self.bar_height,
                width=window_width,
                height=self.bar_height
            )
            
            self.is_visible = True
            
            # Iniciar animación si se solicita
            if animate:
                self._start_animation()
            
            logger.info(f"BLUE_GRADIENT_BAR: Mostrada ({window_width}x{self.bar_height}) {'con animación' if animate else ''}")
            
        except Exception as e:
            logger.error(f"BLUE_GRADIENT_BAR: Error mostrando barra: {e}")
    
    def hide(self):
        """Oculta la barra de gradiente"""
        try:
            if not self.is_visible:
                return
            
            # Detener animación
            self._stop_animation()
            
            # Ocultar canvas
            self.canvas.place_forget()
            self.is_visible = False
            
            logger.info("BLUE_GRADIENT_BAR: Ocultada")
            
        except Exception as e:
            logger.error(f"BLUE_GRADIENT_BAR: Error ocultando barra: {e}")
    
    def is_shown(self):
        """Retorna si la barra está visible"""
        return self.is_visible
    
    def _start_animation(self):
        """Inicia animación sutil de pulsación"""
        if not self.is_animating:
            self.is_animating = True
            self.animation_thread = threading.Thread(target=self._animate_pulse, daemon=True)
            self.animation_thread.start()
            logger.debug("BLUE_GRADIENT_BAR: Animación iniciada")
    
    def _stop_animation(self):
        """Detiene la animación"""
        if self.is_animating:
            self.is_animating = False
            if self.animation_thread:
                self.animation_thread.join(timeout=0.5)
            logger.debug("BLUE_GRADIENT_BAR: Animación detenida")
    
    def _animate_pulse(self):
        """
        Loop de animación de pulsación sutil
        Varía ligeramente la opacidad para crear efecto de "respiración"
        """
        opacity_values = [1.0, 0.8, 0.6, 0.4, 0.6, 0.8]  # Valores de opacidad
        opacity_index = 0
        
        while self.is_animating and self.is_visible:
            try:
                # Para simplificar, solo cambiar cada 800ms
                # En una implementación más compleja se podría modificar la opacidad del canvas
                time.sleep(0.8)
                opacity_index = (opacity_index + 1) % len(opacity_values)
                
            except Exception as e:
                logger.error(f"BLUE_GRADIENT_BAR: Error en animación: {e}")
                break
        
        logger.debug("BLUE_GRADIENT_BAR: Loop de animación terminado")
    
    def update_position(self):
        """
        Actualiza la posición de la barra si la ventana cambió de tamaño
        """
        try:
            if not self.is_visible:
                return
            
            # Re-posicionar la barra
            self.parent_window.update_idletasks()
            window_width = self.parent_window.winfo_width()
            window_height = self.parent_window.winfo_height()
            
            # Solo actualizar si el tamaño cambió significativamente
            if abs(self.bar_width - window_width) > 10:
                logger.debug(f"BLUE_GRADIENT_BAR: Actualizando tamaño {self.bar_width} -> {window_width}")
                self.hide()
                self.show(self.is_animating)
            else:
                # Solo actualizar posición Y
                self.canvas.place_configure(y=window_height - self.bar_height)
                
        except Exception as e:
            logger.error(f"BLUE_GRADIENT_BAR: Error actualizando posición: {e}")