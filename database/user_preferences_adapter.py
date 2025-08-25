#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
UserPreferencesAdapter - Adaptador para sistema de IA generativa

Convierte los datos de la base de datos multi-usuario al formato JSON
que espera el sistema ContextEnricher para personalización de IA.

Combina las 6 categorías personales del usuario con las 13 categorías
técnicas de configuración por defecto.

Autor: Asistente Kata
Fecha: 2024-08-18
Versión: 1.0.0
"""

import logging
import json
from typing import Dict, Any, Optional
from datetime import datetime

from .models.user_manager import user_manager

logger = logging.getLogger(__name__)

class UserPreferencesAdapter:
    """
    Adaptador que convierte datos de BD multi-usuario al formato
    JSON esperado por el sistema de IA generativa.
    """
    
    def __init__(self):
        """Inicializa el adaptador con cache para optimización."""
        self._cached_user = None
        self._cached_preferences = None
        self._last_update = None
        
        logger.info("UserPreferencesAdapter inicializado")
    
    def get_user_preferences_for_ai(self, username: str = None) -> Dict[str, Any]:
        """
        Obtiene las preferencias del usuario en formato compatible con IA generativa.
        
        Args:
            username: Usuario específico. Si None, usa el usuario activo.
            
        Returns:
            Dict: Preferencias en formato JSON compatible con ContextEnricher
        """
        try:
            # Determinar usuario a usar
            target_user = username or user_manager.current_user
            
            if not target_user:
                logger.warning("No hay usuario activo, usando configuración por defecto")
                return self._get_fallback_preferences()
            
            # Verificar cache
            if self._is_cache_valid(target_user):
                logger.debug(f"Usando cache para usuario: {target_user}")
                return self._cached_preferences
            
            # Cargar y procesar preferencias
            user_preferences = self._load_and_convert_preferences(target_user)
            
            # Actualizar cache
            self._update_cache(target_user, user_preferences)
            
            return user_preferences
            
        except Exception as e:
            logger.error(f"Error obteniendo preferencias para IA: {e}")
            return self._get_fallback_preferences()
    
    def _is_cache_valid(self, username: str) -> bool:
        """Verifica si el cache es válido para el usuario dado."""
        return (
            self._cached_user == username and 
            self._cached_preferences is not None and
            self._last_update is not None
        )
    
    def _update_cache(self, username: str, preferences: Dict[str, Any]):
        """Actualiza el cache con nuevas preferencias."""
        self._cached_user = username
        self._cached_preferences = preferences
        self._last_update = datetime.now()
        logger.debug(f"Cache actualizado para usuario: {username}")
    
    def clear_cache(self):
        """Limpia el cache forzando recarga en próxima consulta."""
        self._cached_user = None
        self._cached_preferences = None
        self._last_update = None
        logger.debug("Cache limpiado")
    
    def _load_and_convert_preferences(self, username: str) -> Dict[str, Any]:
        """
        Carga preferencias del usuario desde BD y las convierte al formato IA.
        
        Args:
            username: Usuario del cual cargar preferencias
            
        Returns:
            Dict: Preferencias en formato JSON para ContextEnricher
        """
        try:
            # Obtener preferencias completas del usuario (6 personales + 13 técnicas)
            user_prefs = user_manager.get_user_preferences(username)
            
            if not user_prefs:
                logger.warning(f"No se encontraron preferencias para usuario: {username}")
                return self._get_fallback_preferences()
            
            # Convertir formato BD → formato IA
            ai_preferences = self._convert_to_ai_format(user_prefs, username)
            
            logger.info(f"Preferencias convertidas para IA - Usuario: {username}")
            return ai_preferences
            
        except Exception as e:
            logger.error(f"Error cargando preferencias de BD para {username}: {e}")
            return self._get_fallback_preferences()
    
    def _convert_to_ai_format(self, user_prefs: Dict[str, Any], username: str) -> Dict[str, Any]:
        """
        Convierte preferencias de BD al formato esperado por ContextEnricher.
        
        Args:
            user_prefs: Preferencias desde BD (6 personales + 13 técnicas)
            username: Nombre del usuario
            
        Returns:
            Dict: Preferencias en formato ContextEnricher
        """
        # Estructura base que espera ContextEnricher
        ai_format = {}
        
        # === MAPEO DE CATEGORÍAS PERSONALES (BD → IA) ===
        
        # 1. usuario → usuario (directo)
        if 'usuario' in user_prefs:
            ai_format['usuario'] = user_prefs['usuario'].copy()
        
        # 2. intereses → intereses (directo)
        if 'intereses' in user_prefs:
            ai_format['intereses'] = user_prefs['intereses'].copy()
        
        # 3. mascotas → mascotas (directo)
        if 'mascotas' in user_prefs:
            ai_format['mascotas'] = user_prefs['mascotas'].copy()
        
        # 4. contexto_cultural → contexto_cultural (directo)
        if 'contexto_cultural' in user_prefs:
            ai_format['contexto_cultural'] = user_prefs['contexto_cultural'].copy()
        
        # 5. religion → religion (directo)
        if 'religion' in user_prefs:
            ai_format['religion'] = user_prefs['religion'].copy()
        
        # 6. ejemplos_personalizacion → ejemplos_personalizacion (directo)
        if 'ejemplos_personalizacion' in user_prefs:
            ai_format['ejemplos_personalizacion'] = user_prefs['ejemplos_personalizacion'].copy()
        
        # === CATEGORÍAS TÉCNICAS (desde default_preferences.json) ===
        
        # Estas categorías vienen del archivo técnico y son iguales para todos los usuarios
        technical_categories = [
            'comunicacion', 'configuracion_ai', 'asistente', 'ia_generativa',
            'comandos_clasicos', 'filtros_contenido', 'aprendizaje',
            'integracion_sistema', 'horarios_disponibilidad', 'contexto_asistente'
        ]
        
        for category in technical_categories:
            if category in user_prefs:
                ai_format[category] = user_prefs[category].copy()
        
        # === CATEGORÍAS DE METADATOS ===
        
        # Agregar metadatos del usuario y sistema
        ai_format.update({
            'version_config': user_prefs.get('version_config', '1.0.0'),
            'fecha_creacion': user_prefs.get('fecha_creacion', datetime.now().strftime('%Y-%m-%d')),
            'ultima_actualizacion': datetime.now().strftime('%Y-%m-%d')
        })
        
        # === VERIFICACIONES Y LIMPIEZA ===
        
        # Asegurar que existen las categorías mínimas requeridas
        ai_format = self._ensure_required_categories(ai_format, username)
        
        # Limpiar y validar datos
        ai_format = self._clean_and_validate(ai_format)
        
        logger.debug(f"Conversión BD→IA completada. Categorías: {len(ai_format)}")
        return ai_format
    
    def _ensure_required_categories(self, prefs: Dict[str, Any], username: str) -> Dict[str, Any]:
        """Asegura que existen las categorías mínimas requeridas por ContextEnricher."""
        
        # Categorías mínimas requeridas por ContextEnricher
        if 'usuario' not in prefs:
            prefs['usuario'] = {
                'nombre': username.title(),
                'edad': 25,
                'ciudad': '',
                'timezone': 'America/Guayaquil',
                'idioma_preferido': 'es',
                'modo_verbose': False
            }
        
        if 'asistente' not in prefs:
            prefs['asistente'] = {
                'personalidad': 'amigable_profesional',
                'usar_emojis': False,
                'respuestas_cortas': True,
                'confirmacion_antes_acciones': True
            }
        
        if 'contexto_asistente' not in prefs:
            prefs['contexto_asistente'] = {
                'soy_asistente_kata': True,
                'ejecuto_en': 'raspberry_pi_5',
                'mis_capacidades': [
                    'recordatorios_medicacion',
                    'gestion_tareas', 
                    'contactos_emergencia',
                    'control_dispositivos',
                    'respuestas_inteligentes'
                ],
                'ubicacion': 'hogar_usuario',
                'proposito': 'asistencia_personal_integral'
            }
        
        if 'comunicacion' not in prefs:
            prefs['comunicacion'] = {
                'temas_conversacion_favoritos': [
                    'recuerdos_juventud',
                    'familia_nietos',
                    'cocina_recetas', 
                    'consejos_vida',
                    'cosas_casa_familia'
                ],
                'estilo_respuesta': 'amigable_personal',
                'incluir_referencias_personales': True,
                'nivel_detalle': 'medio'
            }
        
        return prefs
    
    def _clean_and_validate(self, prefs: Dict[str, Any]) -> Dict[str, Any]:
        """Limpia y valida los datos de preferencias."""
        
        # Asegurar que las listas vacías no sean None
        def clean_lists(obj):
            if isinstance(obj, dict):
                return {k: clean_lists(v) for k, v in obj.items()}
            elif isinstance(obj, list):
                return obj if obj else []
            elif obj is None:
                return ''
            else:
                return obj
        
        cleaned_prefs = clean_lists(prefs)
        
        # Validaciones específicas
        if 'usuario' in cleaned_prefs:
            user_data = cleaned_prefs['usuario']
            # Asegurar que edad es un número
            if 'edad' in user_data:
                try:
                    user_data['edad'] = int(user_data['edad']) if user_data['edad'] else 25
                except (ValueError, TypeError):
                    user_data['edad'] = 25
        
        return cleaned_prefs
    
    def _get_fallback_preferences(self) -> Dict[str, Any]:
        """
        Retorna preferencias por defecto en caso de error.
        Basado en las preferencias mínimas que espera ContextEnricher.
        """
        return {
            'usuario': {
                'nombre': 'Usuario',
                'edad': 25,
                'ciudad': '',
                'timezone': 'America/Guayaquil',
                'idioma_preferido': 'es',
                'modo_verbose': False
            },
            'intereses': {
                'hobbies_principales': [],
                'plantas_conoce': [],
                'comidas_favoritas': [],
                'entretenimiento': [],
                'musica_preferida': [],
                'actividades_sociales': []
            },
            'mascotas': {
                'tiene_mascotas': False,
                'tipo': '',
                'nombres': []
            },
            'contexto_cultural': {
                'pais': '',
                'region': '',
                'tradiciones_conoce': []
            },
            'religion': {
                'practica': False,
                'tipo': ''
            },
            'ejemplos_personalizacion': {
                'frases_cercanas': [],
                'cuando_hablar_comida': {'contexto': '', 'incluir': []},
                'cuando_hablar_entretenimiento': {'contexto': '', 'incluir': []},
                'cuando_hablar_mascotas': {'contexto': '', 'incluir': []},
                'cuando_hablar_plantas': {'contexto': '', 'incluir': []}
            },
            'comunicacion': {
                'temas_conversacion_favoritos': [],
                'estilo_respuesta': 'amigable_personal',
                'incluir_referencias_personales': True,
                'nivel_detalle': 'medio'
            },
            'asistente': {
                'personalidad': 'amigable_profesional',
                'usar_emojis': False,
                'respuestas_cortas': True,
                'confirmacion_antes_acciones': True
            },
            'contexto_asistente': {
                'soy_asistente_kata': True,
                'ejecuto_en': 'raspberry_pi_5',
                'mis_capacidades': [
                    'recordatorios_medicacion',
                    'gestion_tareas',
                    'contactos_emergencia',
                    'control_dispositivos',
                    'respuestas_inteligentes'
                ],
                'ubicacion': 'hogar_usuario',
                'proposito': 'asistencia_personal_integral'
            },
            'configuracion_ai': {
                'usar_generativa': True,
                'personalizar_respuestas': True,
                'incluir_nombres_mascotas': True,
                'mencionar_intereses': True,
                'estilo_conversacion': 'cercano_respetuoso',
                'complejidad_maxima': 3,
                'timeout_respuesta': 30
            },
            'ia_generativa': {
                'habilitada': False,
                'proveedor_preferido': 'gemini',
                'modelo_backup': 'gpt-3.5-turbo',
                'confianza_minima_clasica': 0.85,
                'max_tokens_respuesta': 150,
                'temperatura': 0.3,
                'usar_contexto_conversacion': True,
                'recordar_preferencias': True
            },
            'comandos_clasicos': {
                'siempre_preferir': [
                    'recordatorio', 'medicacion', 'contacto_emergencia',
                    'fecha', 'hora', 'enchufe'
                ],
                'nunca_derivar_ia': [
                    'emergencia', 'medicacion_critica', 'sistema_apagar'
                ]
            },
            'version_config': '1.0.0',
            'fecha_creacion': datetime.now().strftime('%Y-%m-%d'),
            'ultima_actualizacion': datetime.now().strftime('%Y-%m-%d')
        }
    
    def get_user_summary(self, username: str = None) -> Dict[str, Any]:
        """
        Obtiene un resumen de las preferencias del usuario para debugging.
        
        Args:
            username: Usuario a consultar
            
        Returns:
            Dict: Resumen de preferencias del usuario
        """
        try:
            target_user = username or user_manager.current_user
            prefs = self.get_user_preferences_for_ai(target_user)
            
            return {
                'usuario': target_user,
                'nombre': prefs.get('usuario', {}).get('nombre', 'N/A'),
                'categorias_personales': len([k for k in prefs.keys() if k in [
                    'usuario', 'intereses', 'mascotas', 'contexto_cultural', 
                    'religion', 'ejemplos_personalizacion'
                ]]),
                'categorias_totales': len(prefs),
                'tiene_mascotas': prefs.get('mascotas', {}).get('tiene_mascotas', False),
                'practica_religion': prefs.get('religion', {}).get('practica', False),
                'hobbies_count': len(prefs.get('intereses', {}).get('hobbies_principales', [])),
                'cache_activo': self._cached_user == target_user,
                'ultima_actualizacion': prefs.get('ultima_actualizacion', 'N/A')
            }
            
        except Exception as e:
            logger.error(f"Error obteniendo resumen de usuario: {e}")
            return {'error': str(e)}


# Instancia global del adaptador
user_preferences_adapter = UserPreferencesAdapter()