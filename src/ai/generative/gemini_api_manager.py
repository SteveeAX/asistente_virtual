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
from typing import Dict, Any, Optional, Iterator, Generator
from datetime import datetime
import threading
import queue

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
        self.timeout = 3  # Valor por defecto agresivo
        self.max_retries = 3
        self.available = False
        
        # Estadísticas básicas
        self.stats = {
            'total_requests': 0,
            'successful_requests': 0,
            'failed_requests': 0,
            'total_tokens_used': 0,
            'avg_response_time': 0.0,
            'streaming_requests': 0,
            'streaming_chunks': 0
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
            
            # Configuración básica optimizada para velocidad
            self.model_name = 'gemini-1.5-flash-latest'  # Usar directamente el modelo que funciona
            self.timeout = int(os.getenv('GEMINI_TIMEOUT', '3'))  # Ultra agresivo: solo 3 segundos
            self.max_retries = int(os.getenv('MAX_RETRIES', '2'))  # Reducido de 3 a 2
            
            # Configurar API
            genai.configure(api_key=self.api_key)
            
            # Crear modelo con configuración optimizada para velocidad + respuestas cortas
            generation_config = {
                "temperature": 0.3,          # Menos variación = más rápido y conciso
                "top_p": 0.8,               # Más selectivo para respuestas cortas
                "top_k": 20,                # Muy eficiente
                "max_output_tokens": 80,    # Forzar respuestas muy cortas (2-3 oraciones)
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
        
        # Usar timeout forzado con threading para garantizar límite estricto
        try:
            # Si hay system_prompt, combinarlo, sino usar prompt directo
            if system_prompt:
                full_prompt = f"{system_prompt}\n\nUsuario: {prompt}\nAsistente:"
            else:
                full_prompt = prompt
            
            logger.debug(f"GEMINI: Enviando prompt: {full_prompt[:50]}...")
            
            # Timeout forzado con threading
            response = None
            error_occurred = None
            
            def generate_with_timeout():
                nonlocal response, error_occurred
                try:
                    response = self.model.generate_content(full_prompt)
                except Exception as e:
                    error_occurred = e
            
            import threading
            thread = threading.Thread(target=generate_with_timeout)
            thread.daemon = True
            thread.start()
            thread.join(timeout=self.timeout)
            
            if thread.is_alive():
                logger.warning(f"GEMINI: Timeout forzado después de {self.timeout}s")
                raise TimeoutError(f"Gemini API timeout después de {self.timeout}s")
            
            if error_occurred:
                raise error_occurred
            
            if response is None:
                raise Exception("No se recibió respuesta de Gemini")
            
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
    
    def generate_response_stream(self, prompt: str, system_prompt: str = None) -> Iterator[Dict[str, Any]]:
        """
        Genera respuesta usando streaming de Gemini API
        
        Args:
            prompt (str): Pregunta/input del usuario
            system_prompt (str): Prompt del sistema (opcional)
        
        Yields:
            Dict[str, Any]: Chunk de respuesta o error
        """
        if not self.is_available():
            yield {
                'success': False,
                'error': 'Gemini API no disponible',
                'error_type': 'not_available',
                'chunk_type': 'error'
            }
            return

        start_time = time.time()
        self.stats['total_requests'] += 1
        self.stats['streaming_requests'] += 1
        
        try:
            # Combinar prompts
            if system_prompt:
                full_prompt = f"{system_prompt}\n\nUsuario: {prompt}\nAsistente:"
            else:
                full_prompt = prompt
            
            logger.debug(f"GEMINI_STREAM: Iniciando streaming para: {full_prompt[:50]}...")
            
            # Usar streaming con timeout por chunk
            chunk_count = 0
            first_chunk_time = None
            accumulated_text = ""
            
            # Implementar timeout con threading para streaming
            response_generator = None
            error_occurred = None
            
            def generate_stream():
                nonlocal response_generator, error_occurred
                try:
                    response_generator = self.model.generate_content(
                        full_prompt,
                        stream=True  # ¡Esta es la clave del streaming!
                    )
                except Exception as e:
                    error_occurred = e
            
            # Ejecutar generación en thread con timeout
            thread = threading.Thread(target=generate_stream)
            thread.daemon = True
            thread.start()
            thread.join(timeout=5.0)  # Timeout para iniciar streaming (ajustado para consultas complejas)
            
            if thread.is_alive() or error_occurred:
                logger.warning("GEMINI_STREAM: Timeout/error iniciando streaming")
                yield {
                    'success': False,
                    'error': f'Timeout iniciando streaming: {error_occurred}',
                    'error_type': 'timeout',
                    'chunk_type': 'error'
                }
                return
            
            if not response_generator:
                yield {
                    'success': False,
                    'error': 'No se pudo crear generador de streaming',
                    'error_type': 'generator_error',
                    'chunk_type': 'error'
                }
                return
            
            # Procesar chunks de streaming
            for chunk in response_generator:
                chunk_count += 1
                self.stats['streaming_chunks'] += 1
                
                if first_chunk_time is None:
                    first_chunk_time = time.time()
                    logger.info(f"GEMINI_STREAM: Primer chunk en {(first_chunk_time - start_time)*1000:.0f}ms")
                
                # Extraer texto del chunk
                chunk_text = ""
                if hasattr(chunk, 'text') and chunk.text:
                    chunk_text = chunk.text
                    accumulated_text += chunk_text
                
                # Yield chunk con información completa
                yield {
                    'success': True,
                    'chunk_text': chunk_text,
                    'accumulated_text': accumulated_text,
                    'chunk_number': chunk_count,
                    'chunk_type': 'content',
                    'is_final': False,
                    'timestamp': time.time(),
                    'response_time': time.time() - start_time
                }
                
                # Timeout entre chunks (evitar chunks colgados)
                if time.time() - start_time > self.timeout:
                    logger.warning(f"GEMINI_STREAM: Timeout total después de {chunk_count} chunks")
                    break
            
            # Chunk final
            total_time = time.time() - start_time
            
            if accumulated_text:
                self.stats['successful_requests'] += 1
                self._update_avg_response_time(total_time)
                
                yield {
                    'success': True,
                    'chunk_text': '',
                    'accumulated_text': accumulated_text,
                    'chunk_number': chunk_count,
                    'chunk_type': 'final',
                    'is_final': True,
                    'total_chunks': chunk_count,
                    'response_time': total_time,
                    'model': self.model_name,
                    'tokens_used': len(accumulated_text.split())  # Estimación
                }
                
                logger.info(f"GEMINI_STREAM: Completado - {chunk_count} chunks en {total_time:.2f}s")
            else:
                yield {
                    'success': False,
                    'error': 'No se recibió contenido en streaming',
                    'error_type': 'empty_response',
                    'chunk_type': 'error'
                }
                
        except Exception as e:
            error_msg = str(e)
            logger.error(f"GEMINI_STREAM: Error en streaming: {error_msg}")
            
            self.stats['failed_requests'] += 1
            
            yield {
                'success': False,
                'error': error_msg,
                'error_type': 'streaming_error',
                'chunk_type': 'error',
                'accumulated_text': accumulated_text if 'accumulated_text' in locals() else ''
            }