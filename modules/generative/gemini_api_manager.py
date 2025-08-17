#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
GeminiAPIManager - Gestor básico para conexión con Google Gemini API

Implementación mínima para validar conectividad y generar respuestas básicas.
Enfocado en estabilidad y manejo de errores.

Autor: Asistente Kata
Fecha: 2024-08-16
Versión: 1.0.0
"""

import os
import time
import logging
from typing import Dict, Any, Optional
from datetime import datetime

try:
    import google.generativeai as genai
    from google.generativeai.types import HarmCategory, HarmBlockThreshold
    GEMINI_AVAILABLE = True
except ImportError as e:
    GEMINI_AVAILABLE = False
    genai = None

logger = logging.getLogger(__name__)

class GeminiAPIManager:
    """
    Gestor básico para Google Gemini API con manejo robusto de errores.
    """
    
    def __init__(self):
        """Inicializa el manager con configuración desde variables de entorno"""
        self.api_key = None
        self.model = None
        self.timeout = 30
        self.max_retries = 3
        self.available = False
        
        # Estadísticas básicas
        self.stats = {
            'total_requests': 0,
            'successful_requests': 0,
            'failed_requests': 0,
            'total_tokens_used': 0,
            'avg_response_time': 0.0
        }
        
        self._initialize()
    
    def _initialize(self):
        """Inicializa la conexión con Gemini API"""
        try:
            if not GEMINI_AVAILABLE:
                logger.error("GEMINI: google-generativeai no está instalado")
                return
            
            # Cargar configuración desde variables de entorno
            # Prioridad: GOOGLE_API_KEY (principal) -> GEMINI_API_KEY (fallback)
            self.api_key = os.getenv('GOOGLE_API_KEY') or os.getenv('GEMINI_API_KEY')
            if not self.api_key:
                logger.error("GEMINI: No se encontró GOOGLE_API_KEY o GEMINI_API_KEY")
                return
            
            # Configuración básica (forzar modelo que funciona)
            self.model_name = 'gemini-1.5-flash-latest'  # Usar directamente el modelo que funciona
            self.timeout = int(os.getenv('GEMINI_TIMEOUT', '30'))
            self.max_retries = int(os.getenv('MAX_RETRIES', '3'))
            
            # Configurar API
            genai.configure(api_key=self.api_key)
            
            # Crear modelo con configuración que funciona (copiada de gemini_manager.py)
            generation_config = {
                "temperature": 0.7,
                "top_p": 0.95,
                "top_k": 40,
                "max_output_tokens": 2048,  # Usar misma configuración que funciona
            }
            
            # Configuración de seguridad (formato que funciona)
            safety_settings = [
                {"category": "HARM_CATEGORY_HARASSMENT", "threshold": "BLOCK_MEDIUM_AND_ABOVE"},
                {"category": "HARM_CATEGORY_HATE_SPEECH", "threshold": "BLOCK_MEDIUM_AND_ABOVE"},
                {"category": "HARM_CATEGORY_SEXUALLY_EXPLICIT", "threshold": "BLOCK_MEDIUM_AND_ABOVE"},
                {"category": "HARM_CATEGORY_DANGEROUS_CONTENT", "threshold": "BLOCK_MEDIUM_AND_ABOVE"},
            ]
            
            self.model = genai.GenerativeModel(
                model_name=self.model_name,
                generation_config=generation_config,
                safety_settings=safety_settings
            )
            
            self.available = True
            logger.info(f"GEMINI: Inicializado correctamente con modelo {self.model_name}")
            
        except Exception as e:
            logger.error(f"GEMINI: Error en inicialización: {str(e)}")
            self.available = False
    
    def is_available(self) -> bool:
        """Verifica si Gemini está disponible para usar"""
        return self.available and GEMINI_AVAILABLE
    
    def generate_response(self, prompt: str, system_prompt: str = None) -> Dict[str, Any]:
        """
        Genera una respuesta usando Gemini API con la lógica exacta que funciona
        
        Args:
            prompt (str): Pregunta/input del usuario
            system_prompt (str): Prompt del sistema (opcional)
        
        Returns:
            Dict[str, Any]: Resultado con respuesta o error
        """
        if not self.is_available():
            return {
                'success': False,
                'error': 'Gemini API no disponible',
                'error_type': 'not_available'
            }
        
        start_time = time.time()
        self.stats['total_requests'] += 1
        
        # Usar la lógica exacta del gemini_manager.py que funciona
        try:
            # Si hay system_prompt, combinarlo, sino usar prompt directo
            if system_prompt:
                full_prompt = f"{system_prompt}\n\nUsuario: {prompt}\nAsistente:"
            else:
                full_prompt = prompt
            
            logger.debug(f"GEMINI: Enviando prompt: {full_prompt[:50]}...")
            
            # Usar generate_content directamente como en gemini_manager.py
            response = self.model.generate_content(full_prompt)
            
            # Extraer texto igual que gemini_manager.py
            text_response = response.text
            
            if not text_response:
                logger.warning("GEMINI: Respuesta vacía recibida")
                return {
                    'success': False,
                    'error': 'Respuesta vacía de Gemini',
                    'error_type': 'empty_response'
                }
            
            # Calcular tiempo de respuesta
            response_time = time.time() - start_time
            
            # Actualizar estadísticas
            self.stats['successful_requests'] += 1
            self._update_avg_response_time(response_time)
            
            logger.info(f"GEMINI: Respuesta generada exitosamente en {response_time:.2f}s")
            
            return {
                'success': True,
                'response': text_response.strip(),
                'model': self.model_name,
                'tokens_used': 0,  # No extraemos tokens por ahora para simplificar
                'response_time': response_time,
                'attempt': 1
            }
            
        except Exception as e:
            error_msg = str(e)
            logger.error(f"GEMINI: Error generando respuesta: {error_msg}")
            
            self.stats['failed_requests'] += 1
            
            # Clasificar tipo de error
            error_type = 'unknown'
            if 'timeout' in error_msg.lower():
                error_type = 'timeout'
            elif 'api key' in error_msg.lower() or 'authentication' in error_msg.lower():
                error_type = 'auth_error'
            elif 'quota' in error_msg.lower() or 'limit' in error_msg.lower():
                error_type = 'quota_exceeded'
            elif 'safety' in error_msg.lower():
                error_type = 'safety_filter'
            
            return {
                'success': False,
                'error': error_msg,
                'error_type': error_type,
                'attempts': 1
            }
    
    def test_connection(self) -> Dict[str, Any]:
        """
        Prueba la conexión con Gemini API usando una consulta simple
        
        Returns:
            Dict[str, Any]: Resultado del test de conexión
        """
        if not self.is_available():
            return {
                'success': False,
                'error': 'Gemini API no está disponible',
                'details': {
                    'gemini_available': GEMINI_AVAILABLE,
                    'api_key_set': bool(self.api_key),
                    'initialized': self.available
                }
            }
        
        test_prompt = "Responde únicamente 'Hola' en español."
        
        try:
            result = self.generate_response(test_prompt)
            
            if result['success']:
                return {
                    'success': True,
                    'message': 'Conexión con Gemini API exitosa',
                    'test_response': result['response'],
                    'response_time': result['response_time'],
                    'model': result['model']
                }
            else:
                return {
                    'success': False,
                    'error': f"Test falló: {result['error']}",
                    'error_type': result.get('error_type')
                }
                
        except Exception as e:
            return {
                'success': False,
                'error': f"Error en test de conexión: {str(e)}",
                'error_type': 'test_exception'
            }
    
    def _update_avg_response_time(self, response_time: float):
        """Actualiza el tiempo promedio de respuesta"""
        if self.stats['successful_requests'] == 1:
            self.stats['avg_response_time'] = response_time
        else:
            # Promedio móvil simple
            total_time = self.stats['avg_response_time'] * (self.stats['successful_requests'] - 1)
            self.stats['avg_response_time'] = (total_time + response_time) / self.stats['successful_requests']
    
    def get_stats(self) -> Dict[str, Any]:
        """Retorna estadísticas de uso"""
        return {
            **self.stats,
            'available': self.available,
            'model': self.model_name,
            'timeout': self.timeout,
            'max_retries': self.max_retries,
            'success_rate': (
                self.stats['successful_requests'] / max(self.stats['total_requests'], 1) * 100
            ) if self.stats['total_requests'] > 0 else 0
        }
    
    def reset_stats(self):
        """Reinicia las estadísticas"""
        self.stats = {
            'total_requests': 0,
            'successful_requests': 0,
            'failed_requests': 0,
            'total_tokens_used': 0,
            'avg_response_time': 0.0
        }
        logger.info("GEMINI: Estadísticas reiniciadas")