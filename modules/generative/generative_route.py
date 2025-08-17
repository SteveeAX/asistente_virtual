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
from datetime import datetime
from typing import Dict, Any, Optional

from .gemini_api_manager import GeminiAPIManager
from .context_enricher import ContextEnricher
from .prompt_builder import PromptBuilder

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
        """Inicializa la ruta generativa con personalización"""
        self.gemini_manager = GeminiAPIManager()
        self.enabled = self._is_enabled()
        
        # Componentes de personalización
        self.context_enricher = ContextEnricher()
        self.prompt_builder = PromptBuilder()
        self.personalization_enabled = self._is_personalization_enabled()
        
        # Estadísticas expandidas
        self.stats = {
            'total_queries': 0,
            'successful_responses': 0,
            'fallback_to_classic': 0,
            'errors': 0,
            'personalized_responses': 0,
            'basic_responses': 0
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
            
            # Decidir si usar personalización o modo básico
            if self.personalization_enabled:
                return self._process_personalized_query(user_input, classic_context)
            else:
                return self._process_basic_query(user_input, classic_context)
                
        except Exception as e:
            logger.error(f"GenerativeRoute: Error procesando consulta: {str(e)}")
            self.stats['errors'] += 1
            return self._create_fallback_response(user_input, str(e))
    
    def _process_personalized_query(self, user_input: str, classic_context: Dict[str, Any] = None) -> Dict[str, Any]:
        """
        Procesa consulta con personalización completa
        
        Args:
            user_input (str): Input del usuario
            classic_context (Dict): Contexto clásico opcional
            
        Returns:
            Dict[str, Any]: Resultado personalizado
        """
        try:
            # 1. Enriquecer contexto con personalización
            enriched_context = self.context_enricher.enrich_context(user_input)
            
            # 2. Construir prompt personalizado
            personalized_prompt = self.prompt_builder.build_personalized_prompt(user_input, enriched_context)
            
            # 3. Generar respuesta con Gemini
            gemini_result = self.gemini_manager.generate_response(personalized_prompt)
            
            if gemini_result['success']:
                self.stats['successful_responses'] += 1
                self.stats['personalized_responses'] += 1
                
                response = self._format_personalized_response(
                    gemini_result, user_input, enriched_context
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