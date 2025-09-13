#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
ContextEnricher - Analizador de contexto personalizado para GenerativeRoute

Analiza las consultas del usuario y enriquece el contexto usando datos
del user_preferences.json para generar respuestas más personalizadas.

Autor: Asistente Kata
Fecha: 2024-08-16
Versión: 1.0.0
"""

import json
import os
import logging
import re
from datetime import datetime
from typing import Dict, Any, List, Optional
from dataclasses import dataclass

# Importar adaptador para BD multi-usuario
try:
    import sys
    sys.path.append(os.path.join(os.path.dirname(__file__), '..', '..'))
    from database.user_preferences_adapter import user_preferences_adapter
    USE_DATABASE_ADAPTER = True
except ImportError as e:
    logging.warning(f"No se pudo importar adaptador de BD: {e}. Usando archivo JSON.")
    USE_DATABASE_ADAPTER = False

logger = logging.getLogger(__name__)

@dataclass
class QueryContext:
    """Contexto enriquecido de una consulta"""
    domain: str
    confidence: float
    user_preferences: Dict[str, Any]
    personalization_data: Dict[str, Any]
    temporal_context: Dict[str, Any]
    query_characteristics: Dict[str, Any]

class ContextEnricher:
    """
    Enriquecedor de contexto que analiza consultas y extrae información
    personalizada basada en las preferencias del usuario.
    """
    
    def __init__(self, preferences_path: str = None):
        """
        Inicializa el enriquecedor de contexto
        
        Args:
            preferences_path (str): Ruta al archivo user_preferences.json
        """
        if preferences_path is None:
            # Ruta por defecto relativa al módulo
            preferences_path = os.path.join(
                os.path.dirname(__file__), 
                '../../data/preferences/user_preferences.json'
            )
        
        self.preferences_path = preferences_path
        self.user_preferences = self._load_preferences()
        
        # Definir dominios detectables con palabras clave (mejorados para Francisca)
        self.domain_keywords = {
            'plantas': [
                'planta', 'plantas', 'sábila', 'toronjil', 'hierbaluisa', 'orégano',
                'perejil', 'jamaica', 'hoja de aire', 'regar', 'cuidar plantas',
                'jardín', 'medicina natural', 'hierba', 'remedio casero'
            ],
            'cocina': [
                'cocina', 'receta', 'comida', 'cocinar', 'preparar', 'caldo de bola',
                'chupe de pescado', 'menestrón', 'tallarín', 'locro', 'sopa',
                'chuleta', 'ingredientes', 'cómo hacer', 'cómo preparar', 'merienda',
                'merendar', 'almorzar', 'almuerzo', 'desayuno', 'desayunar', 'cena',
                'cenar', 'sancocho', 'seco de pollo', 'empanadas', 'humitas',
                'quimbolitos', 'colada morada', 'tostado', 'café', 'idea nueva'
            ],
            'mascotas': [
                'perro', 'perros', 'coco', 'troy', 'mascota', 'mascotas',
                'cuidar perro', 'alimentar', 'pasear', 'veterinario'
            ],
            'entretenimiento': [
                'telenovela', 'telenovelas', 'noticias', 'música', 'canción',
                'chiste', 'cuento', 'historia', 'divertido', 'entretenimiento',
                'boleros', 'baladas', 'pasillos', 'naipes', 'jugar'
            ],
            'tiempo': [
                'tiempo', 'clima', 'lluvia', 'sol', 'calor', 'frío', 'temperatura',
                'viento', 'nublado', 'despejado', 'pronóstico'
            ],
            'personal': [
                'nombre', 'cómo te llamas', 'quién eres', 'tú', 'familia',
                'personal', 'acerca de ti', 'sobre ti', 'nietos', 'juventud'
            ],
            'dispositivos': [
                'enchufe', 'luz', 'dispositivo', 'casa', 'hogar', 'control',
                'encender', 'apagar', 'activar', 'desactivar'
            ],
            'conversacional': [
                'hola', 'buenos días', 'buenas tardes', 'buenas noches',
                'cómo está', 'cómo estás', 'qué tal', 'saludos'
            ],
            'religion': [
                'dios', 'iglesia', 'misa', 'oración', 'rezar', 'bendición',
                'católica', 'religión', 'fe', 'santo'
            ],
            'informacion': [
                'qué es', 'cómo se', 'por qué', 'explica', 'información',
                'cuéntame', 'dime', 'pregunta', 'consulta'
            ]
        }
        
        # ⚡ OPTIMIZACIONES ULTRARRÁPIDAS
        self._build_lookup_tables()
        self._init_optimization_cache()
        
        logger.info("ContextEnricher inicializado correctamente con optimizaciones ultrarrápidas")
    
    def _load_preferences(self) -> Dict[str, Any]:
        """Carga las preferencias del usuario desde BD multi-usuario o archivo JSON de fallback"""
        try:
            # Priorizar adaptador de BD multi-usuario
            if USE_DATABASE_ADAPTER:
                try:
                    preferences = user_preferences_adapter.get_user_preferences_for_ai()
                    if preferences:
                        logger.info("Preferencias de usuario cargadas desde BD multi-usuario")
                        return preferences
                    else:
                        logger.warning("BD multi-usuario no devolvió preferencias, usando fallback")
                except Exception as db_error:
                    logger.error(f"Error usando adaptador BD: {db_error}, fallback a JSON")
            
            # Fallback: usar archivo JSON original
            if os.path.exists(self.preferences_path):
                with open(self.preferences_path, 'r', encoding='utf-8') as f:
                    preferences = json.load(f)
                logger.info("Preferencias de usuario cargadas desde archivo JSON (fallback)")
                return preferences
            else:
                logger.warning(f"Archivo de preferencias no encontrado: {self.preferences_path}")
                return self._get_default_preferences()
                
        except Exception as e:
            logger.error(f"Error cargando preferencias: {e}")
            return self._get_default_preferences()
    
    def _get_default_preferences(self) -> Dict[str, Any]:
        """Retorna preferencias por defecto si no se puede cargar el archivo"""
        return {
            'usuario': {
                'nombre': 'Usuario',
                'timezone': 'America/Guayaquil',
                'idioma_preferido': 'es'
            },
            'asistente': {
                'personalidad': 'amigable_profesional',
                'usar_emojis': False,
                'respuestas_cortas': True
            },
            'contexto_asistente': {
                'soy_asistente_kata': True,
                'ubicacion': 'hogar_usuario',
                'proposito': 'asistencia_personal_integral'
            }
        }
    
    # ⚡ === MÉTODOS DE OPTIMIZACIÓN ULTRARRÁPIDA ===
    
    def _build_lookup_tables(self):
        """Construye tablas de lookup invertidas para acceso O(1) en lugar de O(n*m)"""
        import time
        start_time = time.time()
        
        # Tabla invertida: keyword -> [dominios] para acceso ultrarrápido
        self.keyword_to_domains = {}
        
        for domain, keywords in self.domain_keywords.items():
            for keyword in keywords:
                keyword_lower = keyword.lower().strip()
                if keyword_lower not in self.keyword_to_domains:
                    self.keyword_to_domains[keyword_lower] = []
                self.keyword_to_domains[keyword_lower].append(domain)
        
        # Set de palabras clave para búsqueda ultrarrápida O(1)
        self.all_keywords_set = set(self.keyword_to_domains.keys())
        
        # Precompilar patrones simples/conversacionales para bypass
        self.simple_patterns = {
            'hola', 'gracias', 'bien', 'mal', 'sí', 'no', 'ok', 'adiós',
            'buenos días', 'buenas tardes', 'buenas noches', 'que tal'
        }
        
        build_time = time.time() - start_time
        logger.info(f"Lookup tables construidas: {len(self.keyword_to_domains)} keywords → {build_time*1000:.1f}ms")
    
    def _init_optimization_cache(self):
        """Inicializa caches para resultados frecuentes"""
        self.domain_cache = {}  # Cache para dominios detectados
        self.query_characteristics_cache = {}  # Cache para análisis de queries
        self.simple_context_cache = {}  # Cache para queries simples
        
        # Límites de cache para evitar memory leaks
        self.max_cache_size = 1000
        
        logger.debug("Caches de optimización inicializados")
    
    def _normalize_query_for_cache(self, query: str) -> str:
        """Normaliza query para usar como key en cache"""
        # Normalizar espacios y caracteres especiales manteniendo esencia
        normalized = ' '.join(query.lower().strip().split())
        return normalized[:100]  # Limitar longitud para evitar keys muy largas
    
    def _is_ultra_simple_query(self, query: str) -> bool:
        """Detecta queries ultra-simples que pueden usar bypass completo"""
        query_lower = query.lower().strip()
        
        # Queries de una palabra o frases muy comunes
        if len(query.split()) <= 2:
            words = set(query_lower.split())
            if words.intersection(self.simple_patterns):
                return True
        
        return False
    
    def _should_skip_heavy_analysis(self, query: str) -> bool:
        """Determina si query puede saltar análisis pesado manteniendo calidad"""
        if self._is_ultra_simple_query(query):
            return True
        
        # Queries muy cortas generalmente son simples
        if len(query.split()) <= 3 and len(query) < 20:
            return True
        
        return False
    
    def detect_domain_ultrafast(self, query: str) -> tuple[str, float]:
        """Versión ultrarrápida de detect_domain usando lookup tables"""
        query_key = self._normalize_query_for_cache(query)
        
        # CACHE HIT: O(1)
        if query_key in self.domain_cache:
            return self.domain_cache[query_key]
        
        # ANÁLISIS OPTIMIZADO: O(n) en lugar de O(n*m)
        query_words = set(query.lower().split())
        domain_scores = {}
        
        # Solo analizar palabras que están en nuestras keywords (intersección)
        relevant_words = query_words.intersection(self.all_keywords_set)
        
        for word in relevant_words:
            # Acceso O(1) a dominios por palabra
            for domain in self.keyword_to_domains[word]:
                if domain not in domain_scores:
                    domain_scores[domain] = 0
                
                # Puntaje mayor si la palabra está al inicio
                if query.lower().startswith(word):
                    domain_scores[domain] += 2
                else:
                    domain_scores[domain] += 1
        
        # Determinar mejor dominio
        if not domain_scores:
            result = ('informacion', 0.1)  # Default
        else:
            best_domain = max(domain_scores.items(), key=lambda x: x[1])
            # Normalizar por longitud de query
            confidence = min(best_domain[1] / len(query.split()), 1.0)
            result = (best_domain[0], confidence)
        
        # GUARDAR EN CACHE
        if len(self.domain_cache) < self.max_cache_size:
            self.domain_cache[query_key] = result
        
        return result
    
    def _analyze_query_characteristics_ultrafast(self, query: str) -> Dict[str, Any]:
        """Versión ultrarrápida del análisis de características con cache"""
        query_key = self._normalize_query_for_cache(query)
        
        # CACHE HIT
        if query_key in self.query_characteristics_cache:
            return self.query_characteristics_cache[query_key]
        
        # ANÁLISIS OPTIMIZADO: Solo elementos esenciales
        query_lower = query.lower()
        words = query_lower.split()
        
        # Análisis rápido usando sets pre-compilados
        question_words = {'qué', 'que', 'cómo', 'como', 'cuándo', 'cuando', 'dónde', 'donde', 'quién', 'quien', 'por', 'cuánto', 'cuanto'}
        positive_words = {'gracias', 'bien', 'bueno', 'excelente', 'perfecto'}
        negative_words = {'mal', 'problema', 'error', 'falla', 'no'}
        urgent_words = {'urgente', 'rápido', 'ahora', 'inmediato', 'ya'}
        
        # Análisis en una sola pasada O(n)
        word_set = set(words)
        
        # Tipo de pregunta (primera palabra que coincida)
        question_type = 'declaracion'
        if word_set.intersection(question_words):
            if 'qué' in word_set or 'que' in word_set:
                question_type = 'que'
            elif 'cómo' in word_set or 'como' in word_set:
                question_type = 'como'
            elif 'cuándo' in word_set or 'cuando' in word_set:
                question_type = 'cuando'
            elif 'dónde' in word_set or 'donde' in word_set:
                question_type = 'donde'
            elif 'quién' in word_set or 'quien' in word_set:
                question_type = 'quien'
        
        # Tono emocional (prioridad: urgente > negativo > positivo > neutral)
        tone = 'neutral'
        if word_set.intersection(urgent_words):
            tone = 'urgente'
        elif word_set.intersection(negative_words):
            tone = 'negativo'
        elif word_set.intersection(positive_words):
            tone = 'positivo'
        
        # Complejidad simple basada en longitud
        complexity = 'simple' if len(words) <= 5 else 'media' if len(words) <= 10 else 'compleja'
        
        result = {
            'longitud': len(query),
            'palabras': len(words),
            'tipo_pregunta': question_type,
            'tono': tone,
            'complejidad': complexity,
            'es_pregunta': question_type != 'declaracion'
        }
        
        # GUARDAR EN CACHE
        if len(self.query_characteristics_cache) < self.max_cache_size:
            self.query_characteristics_cache[query_key] = result
        
        return result
    
    def _create_simple_context(self, query: str) -> QueryContext:
        """Crea contexto ultrarrápido para queries simples"""
        query_key = self._normalize_query_for_cache(query)
        
        # CACHE para contexts simples
        if query_key in self.simple_context_cache:
            return self.simple_context_cache[query_key]
        
        # Context básico ultra-minimalista
        context = QueryContext(
            domain='conversacional',
            confidence=0.9,
            user_preferences=self.user_preferences,
            personalization_data={
                'nombre_usuario': self.user_preferences.get('usuario', {}).get('nombre', 'Usuario'),
                'personalidad': 'amigable_simple'
            },
            temporal_context={
                'periodo_dia': 'cualquiera',
                'saludo_apropiado': 'Hola'
            },
            query_characteristics={
                'tipo_pregunta': 'conversacional',
                'tono': 'neutral',
                'complejidad': 'simple'
            }
        )
        
        # GUARDAR EN CACHE
        if len(self.simple_context_cache) < self.max_cache_size:
            self.simple_context_cache[query_key] = context
        
        return context
    
    def enrich_context_ultrafast(self, query: str) -> QueryContext:
        """
        Enriquece contexto con optimizaciones ultrarrápidas y fast paths
        
        Args:
            query (str): Consulta del usuario
            
        Returns:
            QueryContext: Contexto enriquecido optimizado
        """
        try:
            # ⚡ FAST PATH 1: Queries ultra-simples (0.001s)
            if self._is_ultra_simple_query(query):
                logger.debug(f"Fast path ultra-simple para: '{query[:20]}...'")
                return self._create_simple_context(query)
            
            # ⚡ FAST PATH 2: Skip análisis pesado para queries cortas (0.01s)  
            if self._should_skip_heavy_analysis(query):
                logger.debug(f"Fast path simple para: '{query[:30]}...'")
                
                # Solo elementos esenciales
                domain, confidence = self.detect_domain_ultrafast(query)
                
                context = QueryContext(
                    domain=domain,
                    confidence=confidence,
                    user_preferences=self.user_preferences,
                    personalization_data={
                        'nombre_usuario': self.user_preferences.get('usuario', {}).get('nombre', 'Usuario')
                    },
                    temporal_context={'periodo_dia': 'actual'},
                    query_characteristics=self._analyze_query_characteristics_ultrafast(query)
                )
                return context
            
            # ⚡ FULL PATH: Análisis completo pero optimizado (0.1s)
            logger.debug(f"Full análisis optimizado para: '{query[:30]}...'")
            
            # Usar métodos optimizados
            domain, confidence = self.detect_domain_ultrafast(query)
            temporal_context = self._get_temporal_context()
            query_characteristics = self._analyze_query_characteristics_ultrafast(query)
            personalization_data = self._extract_personalization_data(domain)
            
            context = QueryContext(
                domain=domain,
                confidence=confidence,
                user_preferences=self.user_preferences,
                personalization_data=personalization_data,
                temporal_context=temporal_context,
                query_characteristics=query_characteristics
            )
            
            return context
            
        except Exception as e:
            logger.error(f"Error en enrich_context_ultrafast: {e}")
            # Fallback a contexto mínimo
            return QueryContext(
                domain='general',
                confidence=0.1,
                user_preferences=self.user_preferences,
                personalization_data={'nombre_usuario': 'Usuario'},
                temporal_context={'periodo_dia': 'actual'},
                query_characteristics={'error': str(e)}
            )

    def detect_domain(self, query: str) -> tuple[str, float]:
        """
        Detecta el dominio de la consulta basado en palabras clave
        
        Args:
            query (str): Consulta del usuario
            
        Returns:
            tuple[str, float]: (dominio, confianza)
        """
        # ⚡ USAR VERSIÓN ULTRARRÁPIDA OPTIMIZADA
        return self.detect_domain_ultrafast(query)
    
    def _get_temporal_context(self) -> Dict[str, Any]:
        """Obtiene contexto temporal actual"""
        now = datetime.now()
        
        # Determinar período del día
        hour = now.hour
        if 5 <= hour < 12:
            period = 'mañana'
            greeting = 'Buenos días'
        elif 12 <= hour < 18:
            period = 'tarde'
            greeting = 'Buenas tardes'
        elif 18 <= hour < 22:
            period = 'noche'
            greeting = 'Buenas noches'
        else:
            period = 'madrugada'
            greeting = 'Buenas noches'
        
        return {
            'fecha': now.strftime('%Y-%m-%d'),
            'hora': now.strftime('%H:%M'),
            'dia_semana': now.strftime('%A').lower(),
            'periodo_dia': period,
            'saludo_apropiado': greeting,
            'timestamp': now.isoformat()
        }
    
    def _analyze_query_characteristics(self, query: str) -> Dict[str, Any]:
        """Analiza características de la consulta - VERSIÓN ULTRARRÁPIDA"""
        # ⚡ USAR VERSIÓN OPTIMIZADA CON CACHE
        return self._analyze_query_characteristics_ultrafast(query)
    
    def _extract_personalization_data(self, domain: str) -> Dict[str, Any]:
        """Extrae datos de personalización relevantes según el dominio (mejorado para Francisca)"""
        prefs = self.user_preferences
        
        # Datos base siempre incluidos
        base_data = {
            'nombre_usuario': prefs.get('usuario', {}).get('nombre', 'Usuario'),
            'edad': prefs.get('usuario', {}).get('edad'),
            'ciudad': prefs.get('usuario', {}).get('ciudad'),
            'personalidad': prefs.get('comunicacion', {}).get('estilo_respuesta', 'amigable_personal'),
            'usar_emojis': prefs.get('asistente', {}).get('usar_emojis', False),
            'respuestas_cortas': prefs.get('asistente', {}).get('respuestas_cortas', True),
            'incluir_referencias': prefs.get('comunicacion', {}).get('incluir_referencias_personales', True),
            'estilo_conversacion': prefs.get('configuracion_ai', {}).get('estilo_conversacion', 'cercano_respetuoso'),
            'soy_kata': prefs.get('contexto_asistente', {}).get('soy_asistente_kata', True),
            'ubicacion': prefs.get('contexto_asistente', {}).get('ubicacion', 'hogar_usuario'),
            'mis_capacidades': prefs.get('contexto_asistente', {}).get('mis_capacidades', [])
        }
        
        # Datos específicos por dominio
        domain_specific = {}
        
        if domain == 'plantas':
            domain_specific.update({
                'plantas_conoce': prefs.get('intereses', {}).get('plantas_conoce', []),
                'ejemplos_plantas': prefs.get('ejemplos_personalizacion', {}).get('cuando_hablar_plantas', {}).get('incluir', []),
                'hobby_principal': 'cuidar_plantas_interior' in prefs.get('intereses', {}).get('hobbies_principales', [])
            })
        
        elif domain == 'cocina':
            domain_specific.update({
                'comidas_favoritas': prefs.get('intereses', {}).get('comidas_favoritas', []),
                'ejemplos_comida': prefs.get('ejemplos_personalizacion', {}).get('cuando_hablar_comida', {}).get('incluir', []),
                'tradiciones_cocina': prefs.get('contexto_cultural', {}).get('tradiciones_conoce', [])
            })
        
        elif domain == 'mascotas':
            mascotas_info = prefs.get('mascotas', {})
            domain_specific.update({
                'tiene_mascotas': mascotas_info.get('tiene_mascotas', False),
                'nombres_mascotas': mascotas_info.get('nombres', []),
                'tipo_mascotas': mascotas_info.get('tipo', ''),
                'ejemplos_mascotas': prefs.get('ejemplos_personalizacion', {}).get('cuando_hablar_mascotas', {}).get('incluir', [])
            })
        
        elif domain == 'entretenimiento':
            domain_specific.update({
                'entretenimiento_preferido': prefs.get('intereses', {}).get('entretenimiento', []),
                'musica_preferida': prefs.get('intereses', {}).get('musica_preferida', []),
                'actividades_sociales': prefs.get('intereses', {}).get('actividades_sociales', []),
                'ejemplos_entretenimiento': prefs.get('ejemplos_personalizacion', {}).get('cuando_hablar_entretenimiento', {}).get('incluir', [])
            })
        
        elif domain == 'personal':
            domain_specific.update({
                'temas_favoritos': prefs.get('comunicacion', {}).get('temas_conversacion_favoritos', []),
                'region': prefs.get('contexto_cultural', {}).get('region', ''),
                'proposito': prefs.get('contexto_asistente', {}).get('proposito', 'asistencia_personal'),
                'dispositivo': prefs.get('contexto_asistente', {}).get('ejecuto_en', 'raspberry_pi'),
                'timezone': prefs.get('usuario', {}).get('timezone', 'America/Guayaquil')
            })
        
        elif domain == 'religion':
            religion_info = prefs.get('religion', {})
            domain_specific.update({
                'practica_religion': religion_info.get('practica', False),
                'tipo_religion': religion_info.get('tipo', ''),
                'incluir_referencias_religiosas': religion_info.get('practica', False)
            })
        
        elif domain == 'dispositivos':
            domain_specific.update({
                'capacidades_control': [cap for cap in base_data['mis_capacidades'] 
                                      if 'control' in cap or 'dispositivo' in cap],
                'confirmacion_requerida': prefs.get('asistente', {}).get('confirmacion_antes_acciones', True)
            })
        
        # Agregar frases cercanas disponibles
        frases_cercanas = prefs.get('ejemplos_personalizacion', {}).get('frases_cercanas', [])
        if frases_cercanas:
            domain_specific['frases_cercanas'] = frases_cercanas
        
        return {**base_data, **domain_specific}
    
    def enrich_context(self, query: str) -> QueryContext:
        """
        Enriquece el contexto de una consulta con información personalizada
        AHORA OPTIMIZADO: Usa fast paths ultrarrápidos
        
        Args:
            query (str): Consulta del usuario
            
        Returns:
            QueryContext: Contexto enriquecido optimizado
        """
        # ⚡ USAR VERSIÓN ULTRARRÁPIDA CON FAST PATHS
        return self.enrich_context_ultrafast(query)
    
    def get_domain_summary(self, query: str) -> Dict[str, Any]:
        """
        Obtiene un resumen del análisis de dominio para debugging
        
        Args:
            query (str): Consulta a analizar
            
        Returns:
            Dict[str, Any]: Resumen del análisis
        """
        context = self.enrich_context(query)
        
        return {
            'query': query,
            'domain': context.domain,
            'confidence': context.confidence,
            'period': context.temporal_context['periodo_dia'],
            'question_type': context.query_characteristics.get('tipo_pregunta'),
            'user_name': context.personalization_data.get('nombre_usuario'),
            'personality': context.personalization_data.get('personalidad'),
            'capabilities': len(context.personalization_data.get('mis_capacidades', []))
        }
    
    def reload_user_preferences(self):
        """
        Recarga las preferencias del usuario. Útil cuando cambia el usuario activo.
        
        Este método limpia el cache del adaptador BD y recarga las preferencias
        del usuario actualmente activo.
        """
        try:
            if USE_DATABASE_ADAPTER:
                # Limpiar cache del adaptador para forzar recarga
                user_preferences_adapter.clear_cache()
                logger.info("Cache del adaptador BD limpiado")
            
            # Recargar preferencias
            self.user_preferences = self._load_preferences()
            logger.info("Preferencias de usuario recargadas después de cambio de usuario")
            
        except Exception as e:
            logger.error(f"Error recargando preferencias de usuario: {e}")
    
    def get_current_user_info(self) -> Dict[str, Any]:
        """
        Obtiene información del usuario actual para debugging.
        
        Returns:
            Dict: Información básica del usuario actual
        """
        try:
            if USE_DATABASE_ADAPTER:
                return user_preferences_adapter.get_user_summary()
            else:
                # Fallback para modo JSON
                user_data = self.user_preferences.get('usuario', {})
                return {
                    'usuario': user_data.get('nombre', 'N/A'),
                    'modo': 'archivo_json',
                    'categorias_totales': len(self.user_preferences),
                    'ultima_carga': 'N/A'
                }
        except Exception as e:
            logger.error(f"Error obteniendo info del usuario actual: {e}")
            return {'error': str(e)}