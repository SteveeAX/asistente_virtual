#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
GenerativeRoute - Ruta de procesamiento para IA generativa

Implementación mínima que conecta con Gemini API para generar respuestas
cuando el sistema clásico no tiene suficiente confianza.

Autor: Asistente Kata
Fecha: 2024-08-16
Versión: 1.0.0
"""

import logging
import os
import asyncio
import threading
import time
from datetime import datetime
from typing import Dict, Any, Optional

from .gemini_api_manager import GeminiAPIManager
from .context_enricher import ContextEnricher
from .prompt_builder import PromptBuilder
from .conversation_memory import ConversationMemory

logger = logging.getLogger(__name__)

class GenerativeRoute:
    """
    Ruta generativa mínima para consultas no cubiertas por el sistema clásico.
    """
    
    # Prompt básico para adultos mayores en Ecuador
    BASIC_SYSTEM_PROMPT = """
Eres un asistente virtual amable para adultos mayores en Ecuador.

REGLAS IMPORTANTES:
- Máximo 40 palabras por respuesta
- Usa "usted" siempre (formal ecuatoriano)
- Para temas de salud: sugiere consultar médico
- Sé empático y claro
- Si no entiendes, pide que repitan la pregunta

Responde de forma amable y respetuosa.
"""
    
    def __init__(self):
        """Inicializa la ruta generativa con personalización y memoria"""
        self.gemini_manager = GeminiAPIManager()
        self.enabled = self._is_enabled()
        
        # Componentes de personalización
        self.context_enricher = ContextEnricher()
        self.prompt_builder = PromptBuilder()
        self.personalization_enabled = self._is_personalization_enabled()
        
        # Memoria conversacional (se inicializa por usuario)
        self.conversation_memory = None
        
        # Cache inteligente de respuestas
        self._response_cache = {}
        self._cache_max_size = 50
        self._cache_ttl_seconds = 300  # 5 minutos
        
        # Respuestas instantáneas pre-cargadas para consultas comunes
        self._instant_responses = {
            'que es el seco de pollo': '¡Hola Francisca! El seco de pollo es un delicioso guiso ecuatoriano con pollo, cilantro, cebolla y especias. ¡Seguro lo cocinas muy bien!',
            'que puedo hacer de almuerzo': '¡Hola Francisca! Te recomiendo un locro de papa, arroz con pollo, o tallarín saltado. ¿Qué te apetece más?',
            'que es el cafe': 'El café es una bebida energizante hecha de granos tostados, perfecto para acompañar el desayuno o merienda.',
            'como estas': '¡Hola Francisca! Muy bien, gracias por preguntar. ¿En qué puedo ayudarte hoy?',
            'hola': '¡Hola Francisca! ¿Cómo está usted hoy? ¿En qué puedo ayudarla?',
            'buenos dias': '¡Buenos días Francisca! ¿Cómo amaneció hoy?',
            'buenas tardes': '¡Buenas tardes Francisca! ¿Cómo ha estado su día?',
            'apagate': 'COMANDO_SHUTDOWN',  # Comando especial
            'apaga te': 'COMANDO_SHUTDOWN',  # Variación STT
            'que hora es': self._get_current_time,
            'que dia es': self._get_current_date,
        }
        
        # Estadísticas expandidas
        self.stats = {
            'total_queries': 0,
            'successful_responses': 0,
            'fallback_to_classic': 0,
            'errors': 0,
            'personalized_responses': 0,
            'basic_responses': 0,
            'cache_hits': 0,
            'cache_misses': 0,
            'instant_responses': 0,
            'streaming_responses': 0
        }
        
        if self.enabled and self.gemini_manager.is_available():
            logger.info(f"GenerativeRoute: Inicializada correctamente con Gemini (personalización: {self.personalization_enabled})")
        else:
            logger.warning("GenerativeRoute: No disponible - usando solo sistema clásico")
    
    def _is_enabled(self) -> bool:
        """Verifica si la ruta generativa está habilitada"""
        enabled_env = os.getenv('GENERATIVE_ENABLED', 'false').lower()
        return enabled_env in ['true', '1', 'yes', 'on']
    
    def _is_personalization_enabled(self) -> bool:
        """Verifica si la personalización está habilitada"""
        # Por defecto habilitada si la ruta generativa está activa
        personalization_env = os.getenv('PERSONALIZATION_ENABLED', 'true').lower()
        return personalization_env in ['true', '1', 'yes', 'on'] and self.enabled
    
    def initialize_memory(self, user_db_path: str):
        """
        Inicializa la memoria conversacional para el usuario actual.
        
        Args:
            user_db_path: Ruta a la base de datos del usuario actual
        """
        try:
            self.conversation_memory = ConversationMemory(user_db_path)
            logger.info(f"Memoria conversacional inicializada para: {user_db_path}")
        except Exception as e:
            logger.error(f"Error inicializando memoria conversacional: {e}")
            self.conversation_memory = None
    
    def is_available(self) -> bool:
        """Verifica si la ruta generativa está disponible para usar"""
        return self.enabled and self.gemini_manager.is_available()
    
    def process_query(self, user_input: str, classic_context: Dict[str, Any] = None) -> Dict[str, Any]:
        """
        Procesa una consulta del usuario usando IA generativa con personalización
        
        Args:
            user_input (str): Input del usuario
            classic_context (Dict): Contexto del análisis clásico (opcional)
        
        Returns:
            Dict[str, Any]: Resultado en formato compatible con sistema clásico
        """
        self.stats['total_queries'] += 1
        
        if not self.is_available():
            logger.warning("GenerativeRoute: No disponible, retornando fallback")
            self.stats['fallback_to_classic'] += 1
            return self._create_fallback_response(user_input)
        
        try:
            logger.debug(f"GenerativeRoute: Procesando consulta: '{user_input[:50]}...'")
            
            # PRIORIDAD 1: Verificar respuestas instantáneas (0ms)
            instant_response = self._get_instant_response(user_input)
            if instant_response:
                self.stats['instant_responses'] += 1
                logger.info("GenerativeRoute: Respuesta instantánea")
                return instant_response
            
            # PRIORIDAD 2: Verificar cache
            cached_response = self._get_cached_response(user_input)
            if cached_response:
                self.stats['cache_hits'] += 1
                logger.info("GenerativeRoute: Respuesta desde cache")
                return cached_response
            
            self.stats['cache_misses'] += 1
            
            # Decidir si usar personalización o modo básico
            if self.personalization_enabled:
                result = self._process_personalized_query(user_input, classic_context)
            else:
                result = self._process_basic_query(user_input, classic_context)
            
            # Guardar en cache si es exitoso
            if result.get('success') and self._is_cacheable(user_input, result):
                self._cache_response(user_input, result)
            
            return result
                
        except Exception as e:
            logger.error(f"GenerativeRoute: Error procesando consulta: {str(e)}")
            self.stats['errors'] += 1
            
            # Fallback inteligente basado en palabras clave
            smart_fallback = self._create_smart_fallback(user_input)
            if smart_fallback:
                return smart_fallback
            
            return self._create_fallback_response(user_input, str(e))
    
    def _process_personalized_query(self, user_input: str, classic_context: Dict[str, Any] = None) -> Dict[str, Any]:
        """
        Procesa consulta con personalización completa y paralelización optimizada
        
        Args:
            user_input (str): Input del usuario
            classic_context (Dict): Contexto clásico opcional
            
        Returns:
            Dict[str, Any]: Resultado personalizado
        """
        try:
            parallel_start = time.time()
            
            # 1 & 2. Ejecutar contexto y memoria EN PARALELO (optimización clave)
            enriched_context = None
            memory_context = None
            
            def enrich_context():
                nonlocal enriched_context
                enriched_context = self.context_enricher.enrich_context(user_input)
            
            def get_memory():
                nonlocal memory_context
                if self.conversation_memory:
                    memory_context = self.conversation_memory.get_memory_context(user_input)
            
            # Ejecutar ambas tareas en paralelo
            context_thread = threading.Thread(target=enrich_context)
            memory_thread = threading.Thread(target=get_memory)
            
            context_thread.start()
            memory_thread.start()
            
            # Esperar que ambas terminen
            context_thread.join()
            memory_thread.join()
            
            parallel_time = time.time() - parallel_start
            logger.debug(f"GenerativeRoute: Contexto+Memoria paralelo en {parallel_time:.3f}s")
            
            # 3. Construir prompt personalizado con memoria
            personalized_prompt = self.prompt_builder.build_personalized_prompt(
                user_input, enriched_context, memory_context
            )
            
            # 4. Generar respuesta con Gemini con timeout ultra rápido
            gemini_result = None
            error_occurred = None
            
            def generate_fast():
                nonlocal gemini_result, error_occurred
                try:
                    gemini_result = self.gemini_manager.generate_response(personalized_prompt)
                except Exception as e:
                    error_occurred = e
            
            # Timeout moderado para balance velocidad-calidad
            thread = threading.Thread(target=generate_fast)
            thread.daemon = True
            thread.start()
            thread.join(timeout=3.0)  # Dar más tiempo para consultas complejas
            
            if thread.is_alive() or error_occurred:
                logger.warning("GenerativeRoute: Timeout/error en IA, usando smart fallback")
                smart_fallback = self._create_smart_fallback(user_input)
                if smart_fallback:
                    return smart_fallback
                # Si no hay smart fallback, usar respuesta de error
                return {
                    'success': False,
                    'route': 'generative_timeout',
                    'response': 'Disculpe, no pude procesar su consulta ahora mismo. ¿Puede repetir de otra forma?',
                    'intent': 'timeout_fallback',
                    'confidence': 0.1,
                    'entities': {},
                    'router_metadata': {
                        'source': 'timeout_fallback',
                        'response_time': 1.5,
                        'timestamp': datetime.now().isoformat(),
                        'timeout_occurred': True
                    }
                }
            
            if gemini_result['success']:
                self.stats['successful_responses'] += 1
                self.stats['personalized_responses'] += 1
                
                response = self._format_personalized_response(
                    gemini_result, user_input, enriched_context
                )
                
                # 5. Guardar intercambio en memoria conversacional
                if self.conversation_memory:
                    self.conversation_memory.save_interaction(
                        user_input, 
                        gemini_result['response'],
                        enriched_context.domain,
                        enriched_context.confidence
                    )
                
                logger.info(f"GenerativeRoute: Respuesta personalizada generada (dominio: {enriched_context.domain})")
                return response
            else:
                # Error en Gemini, fallback
                logger.warning(f"GenerativeRoute: Error Gemini en personalización: {gemini_result['error']}")
                self.stats['errors'] += 1
                return self._create_fallback_response(user_input, gemini_result['error'])
                
        except Exception as e:
            logger.error(f"GenerativeRoute: Error en personalización: {e}")
            # Fallback a modo básico si la personalización falla
            return self._process_basic_query(user_input, classic_context)
    
    def _process_basic_query(self, user_input: str, classic_context: Dict[str, Any] = None) -> Dict[str, Any]:
        """
        Procesa consulta en modo básico (sin personalización)
        
        Args:
            user_input (str): Input del usuario
            classic_context (Dict): Contexto clásico opcional
            
        Returns:
            Dict[str, Any]: Resultado básico
        """
        # Preparar prompt básico con contexto clásico
        enhanced_prompt = self._prepare_prompt(user_input, classic_context)
        
        # Generar respuesta con Gemini usando prompt básico
        gemini_result = self.gemini_manager.generate_response(
            enhanced_prompt,
            self.BASIC_SYSTEM_PROMPT
        )
        
        if gemini_result['success']:
            self.stats['successful_responses'] += 1
            self.stats['basic_responses'] += 1
            
            response = self._format_response(gemini_result, user_input)
            
            # Guardar intercambio en memoria conversacional
            if self.conversation_memory:
                self.conversation_memory.save_interaction(
                    user_input, 
                    gemini_result['response'],
                    'general',  # Dominio por defecto para modo básico
                    0.8        # Confianza estándar para modo básico
                )
            
            logger.info("GenerativeRoute: Respuesta básica generada exitosamente")
            return response
        else:
            # Error en Gemini, fallback
            logger.warning(f"GenerativeRoute: Error Gemini: {gemini_result['error']}")
            self.stats['errors'] += 1
            return self._create_fallback_response(user_input, gemini_result['error'])
    
    def _prepare_prompt(self, user_input: str, classic_context: Dict[str, Any] = None) -> str:
        """
        Prepara el prompt para enviar a Gemini incluyendo contexto relevante
        
        Args:
            user_input (str): Input del usuario
            classic_context (Dict): Contexto del sistema clásico
        
        Returns:
            str: Prompt preparado
        """
        # Por ahora, prompt simple - se puede enriquecer después
        prompt = user_input
        
        # Si hay contexto clásico, agregarlo como información adicional
        if classic_context:
            detected_intent = classic_context.get('intent')
            if detected_intent and detected_intent != 'unknown':
                prompt += f"\n[Contexto: El usuario podría estar preguntando sobre {detected_intent}]"
        
        return prompt
    
    def _format_response(self, gemini_result: Dict[str, Any], user_input: str) -> Dict[str, Any]:
        """
        Formatea la respuesta de Gemini al formato esperado por el sistema
        
        Args:
            gemini_result (Dict): Resultado de Gemini API
            user_input (str): Input original del usuario
        
        Returns:
            Dict[str, Any]: Respuesta formateada
        """
        return {
            'success': True,
            'route': 'generative',
            'response': gemini_result['response'],
            'intent': 'generative_query',  # Intent genérico para consultas generativas
            'confidence': 0.8,  # Confianza estándar para respuestas generativas
            'entities': {},  # Sin extracción de entidades por ahora
            'router_metadata': {
                'source': 'gemini_api',
                'model': gemini_result.get('model', 'unknown'),
                'tokens_used': gemini_result.get('tokens_used', 0),
                'response_time': gemini_result.get('response_time', 0),
                'timestamp': datetime.now().isoformat(),
                'user_input_length': len(user_input)
            },
            'raw_gemini_result': gemini_result
        }
    
    def _format_personalized_response(self, gemini_result: Dict[str, Any], 
                                    user_input: str, context) -> Dict[str, Any]:
        """
        Formatea la respuesta personalizada de Gemini al formato esperado
        
        Args:
            gemini_result (Dict): Resultado de Gemini API
            user_input (str): Input original del usuario
            context: Contexto enriquecido
            
        Returns:
            Dict[str, Any]: Respuesta personalizada formateada
        """
        return {
            'success': True,
            'route': 'generative_personalized',
            'response': gemini_result['response'],
            'intent': 'personalized_query',
            'confidence': 0.9,  # Alta confianza para respuestas personalizadas
            'entities': {},
            'router_metadata': {
                'source': 'gemini_personalized',
                'model': gemini_result.get('model', 'unknown'),
                'tokens_used': gemini_result.get('tokens_used', 0),
                'response_time': gemini_result.get('response_time', 0),
                'timestamp': datetime.now().isoformat(),
                'user_input_length': len(user_input),
                'personalization': {
                    'domain': context.domain,
                    'domain_confidence': context.confidence,
                    'user_name': context.personalization_data.get('nombre_usuario'),
                    'personality': context.personalization_data.get('personalidad'),
                    'period_of_day': context.temporal_context.get('periodo_dia'),
                    'query_type': context.query_characteristics.get('tipo_pregunta')
                }
            },
            'raw_gemini_result': gemini_result
        }
    
    def _create_fallback_response(self, user_input: str, error_message: str = None) -> Dict[str, Any]:
        """
        Crea una respuesta de fallback cuando la ruta generativa no está disponible
        
        Args:
            user_input (str): Input del usuario
            error_message (str): Mensaje de error opcional
        
        Returns:
            Dict[str, Any]: Respuesta de fallback
        """
        fallback_responses = [
            "Disculpe, no entendí bien su pregunta. ¿Podría repetirla de otra manera?",
            "Lo siento, no pude procesar su consulta en este momento. ¿Podría intentar de nuevo?",
            "Perdón, no tengo una respuesta para eso. ¿Hay algo más en lo que pueda ayudarle?",
        ]
        
        # Seleccionar respuesta basada en longitud del input
        response_index = len(user_input) % len(fallback_responses)
        response = fallback_responses[response_index]
        
        return {
            'success': True,  # Es exitoso porque proporciona una respuesta útil
            'route': 'generative_fallback',
            'response': response,
            'intent': 'fallback',
            'confidence': 0.3,  # Baja confianza para fallback
            'entities': {},
            'router_metadata': {
                'source': 'fallback',
                'is_fallback': True,
                'error_message': error_message,
                'timestamp': datetime.now().isoformat(),
                'fallback_reason': 'generative_unavailable' if not self.is_available() else 'api_error'
            }
        }
    
    def test_functionality(self) -> Dict[str, Any]:
        """
        Prueba la funcionalidad básica de la ruta generativa
        
        Returns:
            Dict[str, Any]: Resultado del test
        """
        if not self.is_available():
            return {
                'success': False,
                'error': 'Ruta generativa no disponible',
                'details': {
                    'enabled': self.enabled,
                    'gemini_available': self.gemini_manager.is_available()
                }
            }
        
        # Test básico con pregunta simple
        test_query = "¿Cómo está usted hoy?"
        
        try:
            result = self.process_query(test_query)
            
            return {
                'success': result['success'],
                'test_query': test_query,
                'response': result['response'],
                'route': result['route'],
                'response_time': result.get('router_metadata', {}).get('response_time', 0),
                'tokens_used': result.get('router_metadata', {}).get('tokens_used', 0)
            }
            
        except Exception as e:
            return {
                'success': False,
                'error': f"Error en test: {str(e)}",
                'test_query': test_query
            }
    
    def get_stats(self) -> Dict[str, Any]:
        """Retorna estadísticas de la ruta generativa con métricas de personalización"""
        total_queries = max(self.stats['total_queries'], 1)
        
        return {
            **self.stats,
            'enabled': self.enabled,
            'available': self.is_available(),
            'personalization_enabled': self.personalization_enabled,
            'gemini_stats': self.gemini_manager.get_stats() if self.gemini_manager else {},
            'success_rate': (self.stats['successful_responses'] / total_queries * 100),
            'personalization_rate': (self.stats['personalized_responses'] / total_queries * 100),
            'basic_rate': (self.stats['basic_responses'] / total_queries * 100),
            'error_rate': (self.stats['errors'] / total_queries * 100)
        }
    
    def reset_stats(self):
        """Reinicia las estadísticas incluidas las de personalización"""
        self.stats = {
            'total_queries': 0,
            'successful_responses': 0,
            'fallback_to_classic': 0,
            'errors': 0,
            'personalized_responses': 0,
            'basic_responses': 0
        }
        if self.gemini_manager:
            self.gemini_manager.reset_stats()
        logger.info("GenerativeRoute: Estadísticas reiniciadas (incluye personalización)")
    
    def reload_user_context(self):
        """
        Recarga el contexto del usuario cuando cambia el usuario activo.
        
        Este método actualiza las preferencias del usuario en el ContextEnricher
        para asegurar que las respuestas generativas sean personalizadas para
        el usuario actualmente activo.
        """
        try:
            if hasattr(self, 'context_enricher'):
                self.context_enricher.reload_user_preferences()
                logger.info("GenerativeRoute: Contexto de usuario recargado exitosamente")
            else:
                logger.warning("GenerativeRoute: ContextEnricher no disponible para recarga")
        except Exception as e:
            logger.error(f"GenerativeRoute: Error recargando contexto de usuario: {e}")
    
    def _get_instant_response(self, user_input: str) -> Dict[str, Any]:
        """Obtiene respuesta instantánea para consultas comunes (0ms)"""
        try:
            normalized = self._normalize_query(user_input)
            
            if normalized in self._instant_responses:
                response_value = self._instant_responses[normalized]
                
                # Si es una función, ejecutarla
                if callable(response_value):
                    response_text = response_value()
                else:
                    response_text = response_value
                
                return {
                    'success': True,
                    'route': 'instant_response',
                    'response': response_text,
                    'intent': 'instant',
                    'confidence': 1.0,
                    'entities': {},
                    'router_metadata': {
                        'source': 'instant_cache',
                        'response_time': 0.001,
                        'timestamp': datetime.now().isoformat(),
                        'is_instant': True
                    }
                }
            
            return None
        except Exception as e:
            logger.warning(f"Error en respuesta instantánea: {e}")
            return None
    
    def _get_current_time(self) -> str:
        """Función para obtener hora actual"""
        from datetime import datetime
        now = datetime.now()
        return f"Son las {now.strftime('%I:%M %p')}"
    
    def _get_current_date(self) -> str:
        """Función para obtener fecha actual"""
        from datetime import datetime
        import locale
        now = datetime.now()
        try:
            locale.setlocale(locale.LC_TIME, 'es_ES.UTF-8')
        except:
            pass
        return f"Hoy es {now.strftime('%A %d de %B')}"
    
    def _normalize_query(self, query: str) -> str:
        """Normaliza consulta para cache (quita variaciones menores)"""
        import re
        import unicodedata
        
        # Convertir a minúsculas y eliminar acentos
        normalized = query.lower().strip()
        normalized = unicodedata.normalize('NFD', normalized)
        normalized = ''.join(c for c in normalized if unicodedata.category(c) != 'Mn')
        
        # Quitar puntuación extra
        normalized = re.sub(r'[¿?¡!.,;:]', '', normalized)
        
        # Quitar palabras de cortesía que no afectan la respuesta
        stopwords = ['por favor', 'gracias', 'disculpe', 'perdón']
        for word in stopwords:
            normalized = normalized.replace(word, '')
        
        return ' '.join(normalized.split())  # Normalizar espacios
    
    def _get_cached_response(self, user_input: str) -> Dict[str, Any]:
        """Obtiene respuesta del cache si existe y no ha expirado"""
        try:
            cache_key = self._normalize_query(user_input)
            
            if cache_key in self._response_cache:
                cached_item = self._response_cache[cache_key]
                
                # Verificar TTL
                if time.time() - cached_item['timestamp'] < self._cache_ttl_seconds:
                    # Actualizar timestamp para respuestas recientes
                    cached_response = cached_item['response'].copy()
                    cached_response['router_metadata']['cache_hit'] = True
                    cached_response['router_metadata']['timestamp'] = datetime.now().isoformat()
                    return cached_response
                else:
                    # Eliminar entrada expirada
                    del self._response_cache[cache_key]
            
            return None
        except Exception as e:
            logger.warning(f"Error obteniendo del cache: {e}")
            return None
    
    def _cache_response(self, user_input: str, response: Dict[str, Any]):
        """Guarda respuesta en cache si es apropiada"""
        try:
            cache_key = self._normalize_query(user_input)
            
            # Limpiar cache si está lleno
            if len(self._response_cache) >= self._cache_max_size:
                # Eliminar entrada más antigua
                oldest_key = min(self._response_cache.keys(), 
                               key=lambda k: self._response_cache[k]['timestamp'])
                del self._response_cache[oldest_key]
            
            # Guardar respuesta con timestamp
            self._response_cache[cache_key] = {
                'response': response.copy(),
                'timestamp': time.time(),
                'original_query': user_input
            }
            
            logger.debug(f"Cache: Guardada respuesta para '{cache_key}'")
        except Exception as e:
            logger.warning(f"Error guardando en cache: {e}")
    
    def _is_cacheable(self, user_input: str, response: Dict[str, Any]) -> bool:
        """Determina si una respuesta debe ser cacheada"""
        try:
            # No cachear respuestas personales/temporales
            response_text = response.get('response', '').lower()
            
            # No cachear si contiene información temporal
            temporal_keywords = ['hoy', 'ahora', 'actualmente', 'en este momento']
            if any(keyword in response_text for keyword in temporal_keywords):
                return False
            
            # No cachear respuestas muy específicas/personales
            personal_keywords = ['tu nombre', 'te llamas', 'recordatorio', 'cita médica']
            if any(keyword in user_input.lower() for keyword in personal_keywords):
                return False
            
            # Cachear información general, recetas, plantas, etc.
            cacheable_domains = ['plantas', 'cocina', 'informacion', 'entretenimiento']
            domain = response.get('router_metadata', {}).get('personalization', {}).get('domain', '')
            
            return domain in cacheable_domains or len(response.get('response', '')) > 20
            
        except Exception as e:
            logger.warning(f"Error determinando si cachear: {e}")
            return False
    
    def _create_smart_fallback(self, user_input: str) -> Dict[str, Any]:
        """Crea fallback inteligente basado en palabras clave"""
        try:
            user_lower = user_input.lower()
            
            # Fallbacks por dominio
            if any(word in user_lower for word in ['cocina', 'receta', 'comida', 'cocinar', 'preparar']):
                response = "¡Hola Francisca! Me encantan sus preguntas de cocina. ¿Podría ser más específica sobre qué le gustaría cocinar?"
            elif any(word in user_lower for word in ['planta', 'plantas', 'sembrar', 'regar']):
                response = "¡Hola Francisca! Las plantas son su especialidad. ¿Podría repetir la pregunta de otra forma?"
            elif any(word in user_lower for word in ['salud', 'dolor', 'medicina', 'doctor']):
                response = "¡Hola Francisca! Para temas de salud, siempre recomiendo consultar con su médico de confianza."
            else:
                return None  # No hay fallback específico
            
            return {
                'success': True,
                'route': 'smart_fallback', 
                'response': response,
                'intent': 'smart_fallback',
                'confidence': 0.7,
                'entities': {},
                'router_metadata': {
                    'source': 'smart_fallback',
                    'response_time': 0.001,
                    'timestamp': datetime.now().isoformat(),
                    'is_fallback': True
                }
            }
            
        except Exception as e:
            logger.warning(f"Error en smart fallback: {e}")
            return None
    
    def process_query_streaming(self, user_input: str, classic_context: Dict[str, Any] = None):
        """
        Procesa consulta con streaming end-to-end (Gemini → TTS)
        
        Args:
            user_input (str): Input del usuario
            classic_context (Dict): Contexto clásico opcional
            
        Yields:
            Dict[str, Any]: Chunks de streaming o resultado final
        """
        self.stats['total_queries'] += 1
        
        if not self.is_available():
            logger.warning("GenerativeRoute: No disponible para streaming")
            yield self._create_fallback_response(user_input)
            return
        
        try:
            logger.debug(f"GenerativeRoute: STREAMING consulta: '{user_input[:50]}...'")
            
            # PRIORIDAD 1: Verificar respuestas instantáneas (no streaming necesario)
            instant_response = self._get_instant_response(user_input)
            if instant_response:
                self.stats['instant_responses'] += 1
                logger.info("GenerativeRoute: Respuesta instantánea (no streaming)")
                yield instant_response
                return
            
            # PRIORIDAD 2: Cache (no streaming necesario)
            cached_response = self._get_cached_response(user_input)
            if cached_response:
                self.stats['cache_hits'] += 1
                logger.info("GenerativeRoute: Respuesta desde cache (no streaming)")
                yield cached_response
                return
            
            self.stats['cache_misses'] += 1
            self.stats['streaming_responses'] += 1
            
            # STREAMING: Procesar con IA generativa
            if self.personalization_enabled:
                yield from self._process_personalized_streaming(user_input, classic_context)
            else:
                yield from self._process_basic_streaming(user_input, classic_context)
                
        except Exception as e:
            logger.error(f"GenerativeRoute: Error en streaming: {str(e)}")
            self.stats['errors'] += 1
            
            # Fallback inteligente
            smart_fallback = self._create_smart_fallback(user_input)
            if smart_fallback:
                yield smart_fallback
            else:
                yield self._create_fallback_response(user_input, str(e))
    
    def _process_personalized_streaming(self, user_input: str, classic_context: Dict[str, Any] = None):
        """Procesa streaming con personalización completa"""
        try:
            parallel_start = time.time()
            
            # Contexto y memoria en paralelo (como antes)
            enriched_context = None
            memory_context = None
            
            def enrich_context():
                nonlocal enriched_context
                enriched_context = self.context_enricher.enrich_context(user_input)
            
            def get_memory():
                nonlocal memory_context
                if self.conversation_memory:
                    memory_context = self.conversation_memory.get_memory_context(user_input)
            
            context_thread = threading.Thread(target=enrich_context)
            memory_thread = threading.Thread(target=get_memory)
            
            context_thread.start()
            memory_thread.start()
            context_thread.join()
            memory_thread.join()
            
            parallel_time = time.time() - parallel_start
            logger.debug(f"GenerativeRoute: Contexto+Memoria paralelo en {parallel_time:.3f}s")
            
            # Construir prompt personalizado
            personalized_prompt = self.prompt_builder.build_personalized_prompt(
                user_input, enriched_context, memory_context
            )
            
            # STREAMING: Generar respuesta chunk por chunk
            first_chunk = True
            accumulated_text = ""
            
            for chunk in self.gemini_manager.generate_response_stream(personalized_prompt):
                if chunk.get('success', False):
                    chunk_text = chunk.get('chunk_text', '')
                    accumulated_text = chunk.get('accumulated_text', accumulated_text)
                    
                    if first_chunk:
                        logger.info("GenerativeRoute: Primer chunk streaming recibido")
                        first_chunk = False
                    
                    # Formatear chunk para streaming
                    streaming_chunk = {
                        'success': True,
                        'route': 'streaming_personalized',
                        'chunk_text': chunk_text,
                        'accumulated_text': accumulated_text,
                        'is_final': chunk.get('is_final', False),
                        'chunk_number': chunk.get('chunk_number', 0),
                        'router_metadata': {
                            'source': 'gemini_streaming',
                            'model': chunk.get('model', 'gemini-2.0-flash'),
                            'personalization': {
                                'domain': enriched_context.domain if enriched_context else 'general',
                                'user_name': enriched_context.personalization_data.get('nombre_usuario', 'Usuario') if enriched_context else 'Usuario',
                            },
                            'streaming': True,
                            'chunk_type': chunk.get('chunk_type', 'content')
                        }
                    }
                    
                    yield streaming_chunk
                    
                    # Si es el chunk final, guardar en memoria
                    if chunk.get('is_final', False):
                        if self.conversation_memory and accumulated_text:
                            self.conversation_memory.save_interaction(
                                user_input, accumulated_text,
                                enriched_context.domain if enriched_context else 'general',
                                0.9
                            )
                        logger.info("GenerativeRoute: Streaming personalizado completado")
                        break
                else:
                    # Error en chunk, usar fallback
                    logger.warning(f"GenerativeRoute: Error en chunk streaming: {chunk.get('error', 'unknown')}")
                    fallback = self._create_smart_fallback(user_input)
                    if fallback:
                        yield fallback
                    break
                    
        except Exception as e:
            logger.error(f"GenerativeRoute: Error en streaming personalizado: {e}")
            fallback = self._create_smart_fallback(user_input)
            if fallback:
                yield fallback
    
    def _process_basic_streaming(self, user_input: str, classic_context: Dict[str, Any] = None):
        """Procesa streaming en modo básico"""
        try:
            # Prompt básico
            enhanced_prompt = self._prepare_prompt(user_input, classic_context)
            
            # STREAMING básico
            for chunk in self.gemini_manager.generate_response_stream(
                enhanced_prompt, self.BASIC_SYSTEM_PROMPT
            ):
                if chunk.get('success', False):
                    streaming_chunk = {
                        'success': True,
                        'route': 'streaming_basic',
                        'chunk_text': chunk.get('chunk_text', ''),
                        'accumulated_text': chunk.get('accumulated_text', ''),
                        'is_final': chunk.get('is_final', False),
                        'chunk_number': chunk.get('chunk_number', 0),
                        'router_metadata': {
                            'source': 'gemini_streaming_basic',
                            'streaming': True,
                            'chunk_type': chunk.get('chunk_type', 'content')
                        }
                    }
                    
                    yield streaming_chunk
                    
                    if chunk.get('is_final', False):
                        logger.info("GenerativeRoute: Streaming básico completado")
                        break
                else:
                    # Error en streaming básico
                    fallback = self._create_smart_fallback(user_input)
                    if fallback:
                        yield fallback
                    break
                    
        except Exception as e:
            logger.error(f"GenerativeRoute: Error en streaming básico: {e}")
            fallback = self._create_smart_fallback(user_input)
            if fallback:
                yield fallback