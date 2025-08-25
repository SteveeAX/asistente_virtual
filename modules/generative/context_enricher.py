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
                'chuleta', 'ingredientes', 'cómo hacer', 'cómo preparar'
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
        
        logger.info("ContextEnricher inicializado correctamente")
    
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
    
    def detect_domain(self, query: str) -> tuple[str, float]:
        """
        Detecta el dominio de la consulta basado en palabras clave
        
        Args:
            query (str): Consulta del usuario
            
        Returns:
            tuple[str, float]: (dominio, confianza)
        """
        query_lower = query.lower()
        domain_scores = {}
        
        # Calcular puntajes para cada dominio
        for domain, keywords in self.domain_keywords.items():
            score = 0
            matches = 0
            
            for keyword in keywords:
                if keyword in query_lower:
                    matches += 1
                    # Puntaje mayor si la palabra clave está al inicio
                    if query_lower.startswith(keyword):
                        score += 2
                    else:
                        score += 1
            
            if matches > 0:
                # Normalizar puntaje por longitud de la consulta
                normalized_score = score / len(query_lower.split())
                domain_scores[domain] = min(normalized_score, 1.0)
        
        # Seleccionar dominio con mayor puntaje
        if domain_scores:
            best_domain = max(domain_scores, key=domain_scores.get)
            confidence = domain_scores[best_domain]
            
            logger.debug(f"Dominio detectado: {best_domain} (confianza: {confidence:.2f})")
            return best_domain, confidence
        else:
            # Dominio por defecto
            logger.debug("Dominio por defecto: general")
            return 'general', 0.3
    
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
        """Analiza características de la consulta"""
        query_lower = query.lower()
        
        # Detectar tipo de pregunta
        question_types = {
            'que': ['qué', 'que'],
            'como': ['cómo', 'como'],
            'cuando': ['cuándo', 'cuando'],
            'donde': ['dónde', 'donde'],
            'quien': ['quién', 'quien'],
            'por_que': ['por qué', 'porque'],
            'cuanto': ['cuánto', 'cuanto', 'cuánta', 'cuanta']
        }
        
        question_type = 'declaracion'
        for q_type, keywords in question_types.items():
            if any(keyword in query_lower for keyword in keywords):
                question_type = q_type
                break
        
        # Detectar tono/intención
        emotional_indicators = {
            'positivo': ['gracias', 'bien', 'bueno', 'excelente', 'perfecto'],
            'negativo': ['mal', 'problema', 'error', 'falla', 'no funciona'],
            'neutral': ['información', 'datos', 'consulta', 'pregunta'],
            'urgente': ['urgente', 'rápido', 'ahora', 'inmediato', 'ya']
        }
        
        tone = 'neutral'
        for emotion, indicators in emotional_indicators.items():
            if any(indicator in query_lower for indicator in indicators):
                tone = emotion
                break
        
        return {
            'longitud': len(query),
            'palabras': len(query.split()),
            'tipo_pregunta': question_type,
            'tono_detectado': tone,
            'es_pregunta': query.strip().endswith('?'),
            'es_comando': any(cmd in query_lower for cmd in ['enciende', 'apaga', 'activa', 'desactiva']),
            'menciona_tiempo': any(t in query_lower for t in ['hoy', 'ayer', 'mañana', 'ahora'])
        }
    
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
        
        Args:
            query (str): Consulta del usuario
            
        Returns:
            QueryContext: Contexto enriquecido
        """
        try:
            # Detectar dominio
            domain, confidence = self.detect_domain(query)
            
            # Obtener contextos
            temporal_context = self._get_temporal_context()
            query_characteristics = self._analyze_query_characteristics(query)
            personalization_data = self._extract_personalization_data(domain)
            
            # Crear contexto enriquecido
            context = QueryContext(
                domain=domain,
                confidence=confidence,
                user_preferences=self.user_preferences,
                personalization_data=personalization_data,
                temporal_context=temporal_context,
                query_characteristics=query_characteristics
            )
            
            logger.debug(f"Contexto enriquecido para dominio '{domain}' (confianza: {confidence:.2f})")
            return context
            
        except Exception as e:
            logger.error(f"Error enriqueciendo contexto: {e}")
            # Contexto mínimo en caso de error
            return QueryContext(
                domain='general',
                confidence=0.1,
                user_preferences=self.user_preferences,
                personalization_data=self._extract_personalization_data('general'),
                temporal_context=self._get_temporal_context(),
                query_characteristics={'error': str(e)}
            )
    
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