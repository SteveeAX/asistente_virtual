#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
RouterCentral - Enrutador inteligente para Asistente Kata

Este módulo implementa el enrutamiento entre el sistema clásico de intenciones
y las nuevas capacidades de IA generativa, asegurando compatibilidad total
con el sistema existente.

Autor: Asistente Kata
Fecha: 2024-08-16
Versión: 1.0.0
"""

import logging
import json
import os
import time
import threading
from datetime import datetime
from typing import Dict, Any, Optional, Tuple
from dataclasses import dataclass

# Configuración de logging
logger = logging.getLogger(__name__)

# Importar sistema de mensajes inteligentes
try:
    from ai.message_ai import MessageAI
    MESSAGE_AI_AVAILABLE = True
    logger.info("ROUTER: Sistema de mensajes inteligentes disponible")
except ImportError as e:
    MESSAGE_AI_AVAILABLE = False
    logger.warning(f"ROUTER: Sistema de mensajes no disponible: {e}")

@dataclass
class DecisionMetrics:
    """Métricas de decisión para análisis y debugging"""
    timestamp: datetime
    input_text: str
    classic_confidence: float
    classic_intent: Optional[str]
    decision_route: str  # 'classic' o 'generative'
    decision_reason: str
    processing_time_ms: float
    success: bool
    error_message: Optional[str] = None

class RouterCentral:
    """
    Enrutador central que decide entre procesamiento clásico e IA generativa.
    
    En esta primera versión, solo maneja el enrutamiento clásico para
    mantener compatibilidad total. La funcionalidad generativa se agregará
    en fases posteriores.
    """
    
    def __init__(self, intent_manager, generative_manager=None):
        """
        Inicializa el router central.
        
        Args:
            intent_manager: Gestor de intenciones clásico existente
            generative_manager: Gestor de IA generativa (opcional)
        """
        self.intent_manager = intent_manager
        
        # Inicializar GenerativeRoute si no se proporciona un generative_manager
        if generative_manager is None:
            try:
                # Primero inicializar cliente Gemini
                from .gemini_api_manager import GeminiAPIManager
                gemini_client = GeminiAPIManager()
                
                # Luego crear GenerativeRoute con cliente Gemini
                from .generative_route import GenerativeRoute
                self.generative_route = GenerativeRoute()
                
                # Asignar cliente Gemini a GenerativeRoute
                if hasattr(self.generative_route, 'gemini_client'):
                    self.generative_route.gemini_client = gemini_client
                else:
                    # Si GenerativeRoute no tiene gemini_client, agregarlo
                    self.generative_route.gemini_client = gemini_client
                
                logger.info("RouterCentral: GenerativeRoute inicializada automáticamente con cliente Gemini")
                
                # Inicializar memoria conversacional
                self._initialize_conversation_memory()
                
            except ImportError as e:
                logger.warning(f"RouterCentral: No se pudo inicializar GenerativeRoute: {e}")
                self.generative_route = None
        else:
            self.generative_route = generative_manager
        
        # Inicializar sistema de mensajes inteligentes
        self.message_ai = None
        if MESSAGE_AI_AVAILABLE:
            try:
                # Necesitamos el cliente Gemini y servicio de BD
                if hasattr(self.generative_route, 'gemini_client'):
                    # Importar servicio de BD desde improved_app (disponible globalmente)
                    import sys
                    sys.path.append(os.path.join(os.path.dirname(__file__), '../..'))
                    from database.models.reminders_adapter import reminders_adapter
                    db_service = reminders_adapter if reminders_adapter else None
                    
                    if db_service:
                        self.message_ai = MessageAI(self.generative_route.gemini_client, db_service)
                        logger.info("ROUTER: Sistema de mensajes inteligentes inicializado")
                    else:
                        logger.warning("ROUTER: No se encontró servicio de BD para mensajes")
                else:
                    logger.warning("ROUTER: No se encontró cliente Gemini para mensajes")
            except Exception as e:
                logger.error(f"ROUTER: Error inicializando sistema de mensajes: {e}")
                self.message_ai = None
            # Inicializar memoria conversacional para manager externo también
            self._initialize_conversation_memory()
        
        # Cargar configuración de usuario
        self.user_preferences = self._load_user_preferences()
        
        # Configuración de confianza mínima para sistema clásico
        # También verificar variables de entorno para override
        env_threshold = os.getenv('CONFIDENCE_THRESHOLD')
        if env_threshold:
            self.min_classic_confidence = float(env_threshold)
        else:
            self.min_classic_confidence = self.user_preferences.get(
                'ia_generativa', {}
            ).get('confianza_minima_clasica', 0.85)  # Actualizado a 0.85 como especificado
        
        # Comandos que siempre van por ruta clásica
        self.always_classic_commands = self.user_preferences.get(
            'comandos_clasicos', {}
        ).get('siempre_preferir', [])
        
        # Comandos que nunca van a IA generativa (críticos)
        self.never_generative_commands = self.user_preferences.get(
            'comandos_clasicos', {}
        ).get('nunca_derivar_ia', [])
        
        # Estado de IA generativa - verificar también variables de entorno
        env_enabled = os.getenv('GENERATIVE_ENABLED', '').lower()
        if env_enabled in ['true', '1', 'yes', 'on']:
            self.generative_enabled = True
        else:
            self.generative_enabled = self.user_preferences.get(
                'ia_generativa', {}
            ).get('habilitada', False)
        
        # Métricas para análisis
        self.decision_metrics = []
        self.stats = {
            'total_requests': 0,
            'classic_route': 0,
            'generative_route': 0,
            'errors': 0,
            'avg_processing_time': 0.0
        }
        
        # Configurar logging
        self._setup_logging()
        
        logger.info("RouterCentral inicializado correctamente")
        logger.info(f"IA generativa habilitada: {self.generative_enabled}")
        logger.info(f"Confianza mínima clásica: {self.min_classic_confidence}")
        logger.info(f"Comandos siempre clásicos: {len(self.always_classic_commands)}")
    
    def _initialize_conversation_memory(self):
        """Inicializa la memoria conversacional en GenerativeRoute"""
        if not self.generative_route:
            return
        
        try:
            # Obtener ruta de BD del usuario actual desde user_manager
            import sys
            sys.path.append(os.path.join(os.path.dirname(__file__), '../../database'))
            from models.user_manager import user_manager
            
            user_db_path = str(user_manager.get_user_database_path())
            
            # Inicializar memoria en GenerativeRoute
            if hasattr(self.generative_route, 'initialize_memory'):
                self.generative_route.initialize_memory(user_db_path)
                logger.info("RouterCentral: Memoria conversacional inicializada")
            else:
                logger.warning("RouterCentral: GenerativeRoute no soporta memoria conversacional")
                
        except Exception as e:
            logger.error(f"RouterCentral: Error inicializando memoria conversacional: {e}")
    
    def _load_user_preferences(self) -> Dict[str, Any]:
        """Carga las preferencias del usuario desde la base de datos multi-usuario"""
        try:
            # Intentar cargar desde sistema multi-usuario
            try:
                import sys
                sys.path.append(os.path.join(os.path.dirname(__file__), '../../database'))
                from models.user_manager import user_manager
                
                # Obtener preferencias del usuario actual
                preferences = user_manager.get_user_preferences()
                logger.info(f"Preferencias cargadas desde BD para usuario: {user_manager.current_user}")
                return preferences
                
            except ImportError:
                logger.warning("Sistema multi-usuario no disponible, usando JSON legacy")
                # Fallback a JSON si el sistema multi-usuario no está disponible
                preferences_path = os.path.join(
                    os.path.dirname(__file__), 
                    '../../data/preferences/user_preferences.json'
                )
                
                if os.path.exists(preferences_path):
                    with open(preferences_path, 'r', encoding='utf-8') as f:
                        preferences = json.load(f)
                    logger.info("Preferencias de usuario cargadas desde JSON legacy")
                    return preferences
                else:
                    logger.warning(f"Archivo de preferencias no encontrado: {preferences_path}")
                    return self._get_default_preferences()
                
        except Exception as e:
            logger.error(f"Error cargando preferencias: {e}")
            return self._get_default_preferences()
    
    def _get_default_preferences(self) -> Dict[str, Any]:
        """Retorna preferencias por defecto si no se puede cargar el archivo"""
        return {
            'ia_generativa': {
                'habilitada': False,
                'confianza_minima_clasica': 0.7
            },
            'comandos_clasicos': {
                'siempre_preferir': [
                    'recordatorio', 'medicacion', 'contacto_emergencia',
                    'fecha', 'hora', 'enchufe'
                ],
                'nunca_derivar_ia': [
                    'emergencia', 'medicacion_critica', 'sistema_apagar', 'leer_mensajes'
                ]
            }
        }
    
    def _setup_logging(self):
        """Configura el logging específico para el router"""
        try:
            log_dir = os.path.join(
                os.path.dirname(__file__), 
                '../../logs/generative'
            )
            os.makedirs(log_dir, exist_ok=True)
            
            # Handler específico para decisiones del router
            log_file = os.path.join(log_dir, 'router_decisions.log')
            handler = logging.FileHandler(log_file, encoding='utf-8')
            formatter = logging.Formatter(
                '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
            )
            handler.setFormatter(formatter)
            logger.addHandler(handler)
            
        except Exception as e:
            logger.error(f"Error configurando logging: {e}")
    
    def process_user_input(self, user_text: str) -> Dict[str, Any]:
        """
        Procesa la entrada del usuario y decide la ruta de procesamiento.
        
        Args:
            user_text (str): Texto del usuario a procesar
            
        Returns:
            Dict[str, Any]: Resultado del procesamiento con metadatos
        """
        start_time = time.time()
        self.stats['total_requests'] += 1
        
        try:
            # Análisis inicial del input
            logger.debug(f"Procesando input: '{user_text[:50]}...'")
            
            # PRIORIDAD MÁXIMA: Verificar respuestas instantáneas antes que todo
            if self.generative_route and hasattr(self.generative_route, '_get_instant_response'):
                instant_response = self.generative_route._get_instant_response(user_text)
                if instant_response:
                    logger.info("RouterCentral: Respuesta instantánea (sin análisis)")
                    processing_time = (time.time() - start_time) * 1000
                    self._record_decision_metrics(
                        user_text, {'route': 'instant', 'reason': 'respuesta_instantanea'}, 
                        instant_response, processing_time, True
                    )
                    return instant_response
            
            # PRIORIDAD ALTA: Verificar comandos de mensaje inteligentes
            if self.message_ai and self.message_ai.is_message_command(user_text):
                logger.info("RouterCentral: Detectado comando de mensaje - usando IA especializada")
                
                # Procesar directamente sin múltiples respuestas
                result = self._process_message_command(user_text)
                
                processing_time = (time.time() - start_time) * 1000
                self._record_decision_metrics(
                    user_text, {'route': 'message_ai', 'reason': 'comando_mensaje'}, 
                    result, processing_time, True
                )
                return result
            
            # Decidir ruta de procesamiento (clásico vs generativo)
            route_decision = self._decide_processing_route(user_text)
            
            # Procesar según la ruta decidida
            if route_decision['route'] == 'classic':
                result = self._process_classic_route(user_text, route_decision)
            elif route_decision['route'] == 'generative':
                result = self._process_generative_route(user_text, route_decision)
            else:
                # Fallback por seguridad
                logger.warning(f"Ruta desconocida: {route_decision['route']}, usando clásica")
                result = self._process_classic_route(user_text, route_decision)
            
            # Registrar métricas
            processing_time = (time.time() - start_time) * 1000
            self._record_decision_metrics(
                user_text, route_decision, result, processing_time, True
            )
            
            return result
            
        except Exception as e:
            # Manejo de errores robusto
            self.stats['errors'] += 1
            processing_time = (time.time() - start_time) * 1000
            
            logger.error(f"Error procesando input: {e}")
            
            # Intentar fallback a sistema clásico
            try:
                fallback_result = self._process_classic_fallback(user_text)
                self._record_decision_metrics(
                    user_text, {'route': 'classic_fallback'}, 
                    fallback_result, processing_time, False, str(e)
                )
                return fallback_result
            except Exception as fallback_error:
                logger.error(f"Error en fallback clásico: {fallback_error}")
                return self._create_error_response(str(e))
    
    def _decide_processing_route(self, user_text: str) -> Dict[str, Any]:
        """
        Decide qué ruta de procesamiento usar basado en el análisis del input.
        
        Args:
            user_text (str): Texto del usuario
            
        Returns:
            Dict[str, Any]: Decisión de enrutamiento con metadatos
        """
        # Análisis con sistema clásico
        classic_analysis = self._analyze_with_classic_system(user_text)
        
        # Verificar comandos que siempre van por ruta clásica
        if self._is_always_classic_command(user_text, classic_analysis):
            return {
                'route': 'classic',
                'reason': 'comando_siempre_clasico',
                'classic_confidence': classic_analysis.get('confidence', 0.0),
                'classic_intent': classic_analysis.get('intent')
            }
        
        # Verificar comandos críticos que nunca van a IA generativa
        if self._is_never_generative_command(user_text, classic_analysis):
            return {
                'route': 'classic',
                'reason': 'comando_critico_nunca_ia',
                'classic_confidence': classic_analysis.get('confidence', 0.0),
                'classic_intent': classic_analysis.get('intent')
            }
        
        # Verificar si IA generativa está habilitada
        if not self.generative_enabled:
            return {
                'route': 'classic',
                'reason': 'ia_generativa_deshabilitada',
                'classic_confidence': classic_analysis.get('confidence', 0.0),
                'classic_intent': classic_analysis.get('intent')
            }
        
        # Verificar confianza del sistema clásico
        classic_confidence = classic_analysis.get('confidence', 0.0)
        if classic_confidence >= self.min_classic_confidence:
            return {
                'route': 'classic',
                'reason': 'confianza_clasica_alta',
                'classic_confidence': classic_confidence,
                'classic_intent': classic_analysis.get('intent')
            }
        
        # Si llegamos aquí, verificar disponibilidad de IA generativa
        if self.generative_route and self.generative_route.is_available():
            return {
                'route': 'generative',
                'reason': 'confianza_clasica_baja_usar_ia',
                'classic_confidence': classic_confidence,
                'classic_intent': classic_analysis.get('intent'),
                'classic_analysis': classic_analysis
            }
        else:
            # Fallback a clásico si generativa no está disponible
            return {
                'route': 'classic',
                'reason': 'ia_generativa_no_disponible',
                'classic_confidence': classic_confidence,
                'classic_intent': classic_analysis.get('intent')
            }
    
    def _analyze_with_classic_system(self, user_text: str) -> Dict[str, Any]:
        """
        Analiza el texto con el sistema clásico de intenciones.
        
        Args:
            user_text (str): Texto a analizar
            
        Returns:
            Dict[str, Any]: Resultado del análisis clásico
        """
        try:
            # Usar el intent_manager existente (método correcto: parse_intent)
            intent_result = self.intent_manager.parse_intent(user_text)
            
            # Convertir resultado de string a formato esperado
            if intent_result:
                # Si se detectó un intent, alta confianza
                confidence = 0.95
            else:
                # Si no se detectó, baja confianza
                confidence = 0.1
                
            return {
                'intent': intent_result,
                'confidence': confidence,
                'entities': {},  # El sistema clásico no extrae entidades
                'raw_result': intent_result
            }
            
        except Exception as e:
            logger.error(f"Error en análisis clásico: {e}")
            return {
                'intent': None,
                'confidence': 0.0,
                'entities': {},
                'error': str(e)
            }
    
    def _is_always_classic_command(self, user_text: str, classic_analysis: Dict) -> bool:
        """Verifica si el comando debe ir siempre por ruta clásica"""
        # Verificar por intent detectado - esto es más preciso
        detected_intent = classic_analysis.get('intent')
        if detected_intent:
            # Intents que SIEMPRE van por ruta clásica (sin depender de configuración)
            forced_classic_intents = ['SEND_MESSAGE', 'READ_MESSAGES']
            if detected_intent in forced_classic_intents:
                logger.info(f"RouterCentral fuerza ruta clásica para: {detected_intent}")
                return True
                
            # Mapear intents a comandos clásicos (configurables por usuario)
            intent_to_command = {
                'GET_TIME': 'hora',
                'GET_DATE': 'fecha',
                'PLUG_ON': 'enchufe',
                'PLUG_OFF': 'enchufe',
                'CREATE_REMINDER': 'recordatorio',
                'CREATE_DAILY_REMINDER': 'recordatorio',
                'LIST_REMINDERS': 'recordatorio',
                'DELETE_REMINDER': 'recordatorio',
                'CONTACT_PERSON': 'contacto_emergencia',
                'EMERGENCY_ALERT': 'emergencia'
            }
            
            mapped_command = intent_to_command.get(detected_intent)
            if mapped_command and mapped_command in self.always_classic_commands:
                return True
        
        return False
    
    def _is_never_generative_command(self, user_text: str, classic_analysis: Dict) -> bool:
        """Verifica si el comando nunca debe ir a IA generativa"""
        # Verificar por intent detectado
        detected_intent = classic_analysis.get('intent')
        if detected_intent and detected_intent in self.never_generative_commands:
            return True
        
        # Verificar por palabras clave críticas
        user_text_lower = user_text.lower()
        critical_keywords = ['emergencia', 'ayuda', 'socorro', 'urgente', 'medicación']
        message_keywords = ['lee mensaje', 'lee mensajes', 'leer mensaje', 'leer mensajes', 
                           'mostrar mensaje', 'mostrar mensajes', 'qué mensajes', 'que mensajes',
                           'tienes mensajes', 'tengo mensajes', 'dime los mensajes']
        
        # Verificar palabras críticas
        for keyword in critical_keywords:
            if keyword in user_text_lower:
                return True
        
        # Verificar palabras de mensajes
        for keyword in message_keywords:
            if keyword in user_text_lower:
                return True
        
        return False
    
    def _process_classic_route(self, user_text: str, route_decision: Dict) -> Dict[str, Any]:
        """
        Procesa la entrada usando el sistema clásico.
        
        Args:
            user_text (str): Texto del usuario
            route_decision (Dict): Decisión de enrutamiento
            
        Returns:
            Dict[str, Any]: Resultado del procesamiento clásico
        """
        try:
            self.stats['classic_route'] += 1
            
            # Procesar con el intent manager existente (solo devuelve el intent)
            detected_intent = self.intent_manager.parse_intent(user_text)
            
            # En lugar de generar respuesta genérica, señalar que requiere ejecución clásica
            if detected_intent:
                # Señalar al sistema principal que debe ejecutar este intent
                enriched_result = {
                    'success': True,
                    'route': 'classic',
                    'intent': detected_intent,
                    'confidence': 0.95,
                    'requires_classic_execution': True,  # ← Señal clave para improved_app.py
                    'user_text': user_text,
                    'entities': {},
                    'router_metadata': {
                        'decision_reason': route_decision.get('reason'),
                        'classic_confidence': route_decision.get('classic_confidence'),
                        'timestamp': datetime.now().isoformat()
                    },
                    'raw_classic_result': detected_intent
                }
                
                logger.debug(f"Intent clásico detectado, requiere ejecución: {detected_intent}")
                return enriched_result
            else:
                # No se detectó intent válido
                return {
                    'success': False,
                    'route': 'classic',
                    'response': "Comando no reconocido",
                    'intent': None,
                    'confidence': 0.1,
                    'router_metadata': {
                        'decision_reason': route_decision.get('reason'),
                        'classic_confidence': route_decision.get('classic_confidence'),
                        'timestamp': datetime.now().isoformat()
                    }
                }
            
        except Exception as e:
            logger.error(f"Error en procesamiento clásico: {e}")
            return self._create_error_response(f"Error en sistema clásico: {e}")
    
    def _process_generative_route(self, user_text: str, route_decision: Dict) -> Dict[str, Any]:
        """
        Procesa la entrada usando la ruta generativa (Gemini API).
        
        Args:
            user_text (str): Texto del usuario
            route_decision (Dict): Decisión de enrutamiento
            
        Returns:
            Dict[str, Any]: Resultado del procesamiento generativo
        """
        try:
            self.stats['generative_route'] += 1
            
            if not self.generative_route:
                logger.error("GenerativeRoute no está disponible")
                return self._process_classic_fallback(user_text)
            
            # Obtener contexto clásico si está disponible
            classic_context = route_decision.get('classic_analysis', {})
            
            # Procesar con la ruta generativa
            generative_result = self.generative_route.process_query(user_text, classic_context)
            
            # Si la ruta generativa falló, usar fallback clásico
            if not generative_result.get('success', False):
                logger.warning("Ruta generativa falló, usando fallback clásico")
                return self._process_classic_fallback(user_text)
            
            # Enriquecer resultado con metadatos del router
            generative_result['router_metadata'] = {
                **generative_result.get('router_metadata', {}),
                'decision_reason': route_decision.get('reason'),
                'classic_confidence': route_decision.get('classic_confidence'),
                'router_timestamp': datetime.now().isoformat()
            }
            
            logger.info(f"Procesamiento generativo exitoso: {generative_result.get('route')}")
            
            # ⚡ Log de uso de IA generativa en Firestore ASÍNCRONO (no bloquea respuesta)
            self._log_ai_usage_async(user_text, generative_result, route_decision)
            
            return generative_result
            
        except Exception as e:
            logger.error(f"Error en procesamiento generativo: {e}")
            # Fallback a sistema clásico en caso de error
            return self._process_classic_fallback(user_text)
    
    def _process_classic_fallback(self, user_text: str) -> Dict[str, Any]:
        """Procesamiento de fallback cuando hay errores"""
        try:
            # Respuesta genérica segura
            return {
                'success': True,
                'route': 'classic_fallback',
                'response': 'Lo siento, no pude procesar tu solicitud. ¿Podrías repetirla?',
                'intent': 'fallback',
                'confidence': 0.0,
                'router_metadata': {
                    'is_fallback': True,
                    'timestamp': datetime.now().isoformat()
                }
            }
        except Exception as e:
            logger.error(f"Error en fallback: {e}")
            return self._create_error_response("Error crítico en el sistema")
    
    def _create_error_response(self, error_message: str) -> Dict[str, Any]:
        """Crea una respuesta de error estandarizada"""
        return {
            'success': False,
            'route': 'error',
            'response': 'Disculpa, hay un problema técnico. Intenta de nuevo.',
            'error': error_message,
            'router_metadata': {
                'is_error': True,
                'timestamp': datetime.now().isoformat()
            }
        }
    
    def _record_decision_metrics(self, user_text: str, route_decision: Dict, 
                               result: Dict, processing_time: float, 
                               success: bool, error_message: str = None):
        """Registra métricas de decisión para análisis"""
        try:
            metrics = DecisionMetrics(
                timestamp=datetime.now(),
                input_text=user_text[:100],  # Truncar para privacidad
                classic_confidence=route_decision.get('classic_confidence', 0.0),
                classic_intent=route_decision.get('classic_intent'),
                decision_route=route_decision.get('route', 'unknown'),
                decision_reason=route_decision.get('reason', 'unknown'),
                processing_time_ms=processing_time,
                success=success,
                error_message=error_message
            )
            
            self.decision_metrics.append(metrics)
            
            # Mantener solo las últimas 1000 métricas
            if len(self.decision_metrics) > 1000:
                self.decision_metrics = self.decision_metrics[-1000:]
            
            # Actualizar estadísticas promedio
            self._update_stats(processing_time)
            
        except Exception as e:
            logger.error(f"Error registrando métricas: {e}")
    
    def _update_stats(self, processing_time: float):
        """Actualiza estadísticas de rendimiento"""
        try:
            # Calcular promedio de tiempo de procesamiento
            total_time = self.stats['avg_processing_time'] * (self.stats['total_requests'] - 1)
            self.stats['avg_processing_time'] = (total_time + processing_time) / self.stats['total_requests']
            
        except Exception as e:
            logger.error(f"Error actualizando estadísticas: {e}")
    
    def _log_ai_usage_async(self, user_text: str, generative_result: Dict[str, Any], route_decision: Dict[str, Any]):
        """
        Log asíncrono de uso de IA generativa a Firestore (no bloquea respuesta)
        
        Args:
            user_text: Texto de entrada del usuario  
            generative_result: Resultado de la IA generativa
            route_decision: Decisión del router
        """
        def _async_firestore_log():
            try:
                # Importar firestore_logger (solo cuando sea necesario)
                import sys
                sys.path.append(os.path.join(os.path.dirname(__file__), '../..'))
                import firestore_logger
                
                # Registrar uso de IA generativa con detalles
                firestore_logger.log_interaction("ai_generative_used", details={
                    'input_text_preview': user_text[:100],  # Solo primeros 100 caracteres
                    'route_type': generative_result.get('route'),
                    'domain_detected': generative_result.get('router_metadata', {}).get('personalization', {}).get('domain'),
                    'processing_time_ms': round(generative_result.get('router_metadata', {}).get('response_time', 0) * 1000, 2),
                    'model_used': generative_result.get('router_metadata', {}).get('model', 'unknown'),
                    'tokens_used': generative_result.get('router_metadata', {}).get('tokens_used', 0),
                    'decision_reason': route_decision.get('reason')
                })
                
                logger.debug("Firestore logging completado asíncronamente")
                
            except Exception as log_error:
                # No fallar si hay error en logging asíncrono
                logger.warning(f"Error en logging asíncrono de Firestore: {log_error}")
        
        # Ejecutar en thread separado para no bloquear
        thread = threading.Thread(target=_async_firestore_log, daemon=True)
        thread.start()
        logger.debug("Firestore logging iniciado asíncronamente")
    
    def get_stats(self) -> Dict[str, Any]:
        """Retorna estadísticas del router"""
        return {
            **self.stats,
            'generative_enabled': self.generative_enabled,
            'min_classic_confidence': self.min_classic_confidence,
            'recent_metrics_count': len(self.decision_metrics)
        }
    
    def get_recent_decisions(self, limit: int = 10) -> list:
        """Retorna las decisiones más recientes para debugging"""
        return [
            {
                'timestamp': m.timestamp.isoformat(),
                'input_preview': m.input_text[:50] + '...' if len(m.input_text) > 50 else m.input_text,
                'route': m.decision_route,
                'reason': m.decision_reason,
                'classic_confidence': m.classic_confidence,
                'processing_time_ms': round(m.processing_time_ms, 2),
                'success': m.success
            }
            for m in self.decision_metrics[-limit:]
        ]
    
    def reload_user_context(self):
        """
        Recarga el contexto del usuario cuando cambia el usuario activo.
        
        Este método actualiza las preferencias del usuario y recarga el contexto
        en la ruta generativa para asegurar personalización correcta.
        """
        try:
            # Recargar preferencias del usuario
            self.user_preferences = self._load_user_preferences()
            logger.info("RouterCentral: Preferencias de usuario recargadas")
            
            # Recargar contexto en la ruta generativa si está disponible
            if self.generative_route and hasattr(self.generative_route, 'reload_user_context'):
                self.generative_route.reload_user_context()
                logger.info("RouterCentral: Contexto de ruta generativa recargado")
            
            # Reinicializar memoria conversacional para el nuevo usuario
            self._initialize_conversation_memory()
            
            logger.info("RouterCentral: Recarga de contexto de usuario completada")
            
        except Exception as e:
            logger.error(f"RouterCentral: Error recargando contexto de usuario: {e}")
    
    def _process_message_command(self, user_text: str) -> Dict[str, Any]:
        """
        Procesa comandos de mensaje usando IA especializada
        
        Args:
            user_text: Comando de mensaje del usuario
            
        Returns:
            Dict con resultado del procesamiento
        """
        try:
            # Obtener nombre del usuario actual dinámicamente
            user_name = "Usuario"
            try:
                # Método 1: Desde user_manager (más confiable)
                import sys
                sys.path.append(os.path.join(os.path.dirname(__file__), '../../database'))
                from models.user_manager import user_manager
                current_user = user_manager.current_user
                if current_user:
                    user_name = current_user.capitalize()  # francisca → Francisca
                
                # Método 2: Fallback desde generative_route
                if user_name == "Usuario" and hasattr(self.generative_route, 'user_preferences_adapter'):
                    prefs = self.generative_route.user_preferences_adapter.get_user_preferences()
                    user_info = prefs.get('usuario', {})
                    user_name = user_info.get('nombre', 'Usuario')
                    
            except Exception as e:
                logger.debug(f"RouterCentral: Error obteniendo nombre usuario: {e}")
                pass
            
            # Procesar comando con VoiceMessageSender si está disponible
            if hasattr(self, 'voice_message_sender') and self.voice_message_sender:
                success = self.voice_message_sender.process_voice_message(user_text, user_name)
                # VoiceMessageSender ya maneja su propio TTS, no retornamos respuesta de audio
                return {
                    'success': True,
                    'response': None,  # Sin respuesta de audio - VoiceMessageSender la maneja
                    'intent': 'send_message',
                    'confidence': 1.0,
                    'silent': True  # Indicar que no debe reproducir audio adicional
                }
            else:
                # Fallback - sistema no disponible
                return {
                    'success': False,
                    'response': 'Sistema de envío de mensajes no disponible',
                    'intent': 'send_message_error',
                    'confidence': 1.0
                }
                
        except Exception as e:
            logger.error(f"MESSAGE_AI: Error crítico procesando comando: {e}")
            return {
                'success': False,
                'intent': 'system_error',
                'response': "Hubo un error procesando el comando de mensaje.",
                'processing_method': 'message_ai',
                'error': str(e)
            }