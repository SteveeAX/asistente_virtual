#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
PromptBuilder - Constructor de prompts personalizados para GenerativeRoute

Construye prompts específicos usando el contexto enriquecido del ContextEnricher
para generar respuestas más personalizadas y empáticas.

Autor: Asistente Kata
Fecha: 2024-08-16
Versión: 1.0.0
"""

import logging
from typing import Dict, Any, Optional
from .context_enricher import QueryContext

logger = logging.getLogger(__name__)

class PromptBuilder:
    """
    Constructor de prompts personalizados que usa el contexto enriquecido
    para crear prompts específicos según el dominio y preferencias del usuario.
    """
    
    def __init__(self):
        """Inicializa el constructor de prompts"""
        self.domain_templates = self._init_domain_templates()
        
        logger.info("PromptBuilder inicializado correctamente")
    
    def _get_base_system_prompt(self, user_name: str = None) -> str:
        """Prompt base del sistema para todas las respuestas"""
        nombre_usuario = user_name if user_name else "{nombre_usuario}"
        return f"""Eres Kata, un asistente virtual cercano y amigable para {nombre_usuario}.

REGLAS FUNDAMENTALES:
- Máximo 40 palabras por respuesta (muy importante)
- Usa un tono cercano pero respetuoso (no formal)
- Sé empática, clara y cálida
- Para temas de salud: sugiere consultar médico
- Si no entiendes, pide que repita

Tu objetivo es ser útil y hacer que {nombre_usuario} se sienta acompañada."""
    
    def _init_domain_templates(self) -> Dict[str, str]:
        """Inicializa plantillas específicas por dominio (dinámicas para cualquier usuario)"""
        return {
            'plantas': """
CONTEXTO PERSONAL DE {nombre_usuario}:
- Le encantan las plantas medicinales: {plantas_conoce}
- Es experta en cuidado de plantas de interior
- Conoce remedios caseros: {ejemplos_plantas}
- Vive en {ciudad}
{frase_cercana_plantas}

ESTILO: Reconoce su conocimiento y experiencia""",

            'cocina': """
CONTEXTO PERSONAL DE {nombre_usuario}:
- Sus comidas favoritas: {comidas_favoritas}
- Conoce recetas tradicionales ecuatorianas
- Ejemplos: {ejemplos_comida}
- De la región de {ciudad}
{frase_cercana_cocina}

ESTILO: Reconoce su experiencia culinaria""",

            'mascotas': """
CONTEXTO PERSONAL DE {nombre_usuario}:
- Tiene mascotas: {nombres_mascotas}
- Le encantan sus mascotas
- Ejemplos de conversación: {ejemplos_mascotas}
{frase_cercana_mascotas}

ESTILO: Muestra interés por sus mascotas""",

            'entretenimiento': """
CONTEXTO PERSONAL DE {nombre_usuario}:
- Le gustan: {entretenimiento_preferido}
- Música preferida: {musica_preferida}
- Actividades: {actividades_sociales}
- Ejemplos: {ejemplos_entretenimiento}

ESTILO: Conecta con sus gustos personales""",
            
            'tiempo': """
CONTEXTO ADICIONAL:
- {nombre_usuario} vive en {ciudad}, Ecuador
- Responde de manera práctica y útil
- Sugiere acciones apropiadas según el clima

ESTILO: Informativo pero cálido""",
            
            'personal': """
CONTEXTO PERSONAL DE {nombre_usuario}:
- Es {nombre_usuario} de {ciudad}, {edad} años
- Temas favoritos: {temas_favoritos}
- Región: {region}
- Menciona que eres Kata si preguntan

ESTILO: Cercano y familiar""",

            'religion': """
CONTEXTO PERSONAL DE {nombre_usuario}:
- Es católica practicante
- Puedes hacer referencias respetuosas a la fe
- Valores tradicionales ecuatorianos

ESTILO: Respetuoso y comprensivo""",
            
            'dispositivos': """
CONTEXTO ADICIONAL:
- Control de dispositivos del hogar
- Capacidades: {capacidades_dispositivos}
{confirmacion_nota}

ESTILO: Técnico pero accesible""",
            
            'conversacional': """
CONTEXTO ADICIONAL:
- Saludo o conversación casual con {nombre_usuario}
- Hora actual: {hora_actual}
- Período del día: {periodo_dia}
- Saludo apropiado: {saludo}

ESTILO: Cálido y conversacional""",
            
            'informacion': """
CONTEXTO ADICIONAL:
- Consulta informativa
- Explicar de manera simple y clara
- Relacionar con contexto ecuatoriano cuando sea relevante

ESTILO: Educativo pero amigable""",
            
            'general': """
CONTEXTO ADICIONAL:
- Consulta general para {nombre_usuario}
- Responder de manera útil y empática
- Adaptarse al tono de la consulta

ESTILO: Adaptativo y amigable"""
        }
    
    def _personalize_template(self, template: str, context: QueryContext) -> str:
        """
        Personaliza una plantilla con datos del contexto
        
        Args:
            template (str): Plantilla base
            context (QueryContext): Contexto enriquecido
            
        Returns:
            str: Plantilla personalizada
        """
        # Obtener frases cercanas disponibles
        frases_cercanas = context.personalization_data.get('frases_cercanas', [])
        
        personalization_vars = {
            # Datos del usuario
            'nombre_usuario': context.personalization_data.get('nombre_usuario', 'Usuario'),
            'edad': context.personalization_data.get('edad', ''),
            'ciudad': context.personalization_data.get('ciudad', ''),
            'nombre_asistente': 'Kata',
            
            # Ubicación y contexto
            'ubicacion': context.personalization_data.get('ubicacion', 'hogar'),
            'region': context.personalization_data.get('region', ''),
            'proposito': context.personalization_data.get('proposito', 'asistencia personal'),
            
            # Temporal
            'hora_actual': context.temporal_context.get('hora', ''),
            'periodo_dia': context.temporal_context.get('periodo_dia', 'día'),
            'saludo': context.temporal_context.get('saludo_apropiado', 'Hola'),
            
            # Datos específicos por dominio
            'plantas_conoce': ', '.join(context.personalization_data.get('plantas_conoce', [])),
            'ejemplos_plantas': ', '.join(context.personalization_data.get('ejemplos_plantas', [])),
            'comidas_favoritas': ', '.join(context.personalization_data.get('comidas_favoritas', [])),
            'ejemplos_comida': ', '.join(context.personalization_data.get('ejemplos_comida', [])),
            'nombres_mascotas': ', '.join(context.personalization_data.get('nombres_mascotas', [])),
            'ejemplos_mascotas': ', '.join(context.personalization_data.get('ejemplos_mascotas', [])),
            'entretenimiento_preferido': ', '.join(context.personalization_data.get('entretenimiento_preferido', [])),
            'musica_preferida': ', '.join(context.personalization_data.get('musica_preferida', [])),
            'actividades_sociales': ', '.join(context.personalization_data.get('actividades_sociales', [])),
            'ejemplos_entretenimiento': ', '.join(context.personalization_data.get('ejemplos_entretenimiento', [])),
            'temas_favoritos': ', '.join(context.personalization_data.get('temas_favoritos', [])),
            
            # Frases cercanas específicas por contexto
            'frase_cercana_plantas': f"- Puedes usar: '{frases_cercanas[0]}'" if frases_cercanas and 'plantas' in frases_cercanas[0] else '',
            'frase_cercana_cocina': f"- Puedes usar: '{frases_cercanas[1]}'" if len(frases_cercanas) > 1 and 'cocina' in frases_cercanas[1] else '',
            'frase_cercana_mascotas': f"- Puedes preguntar: '{frases_cercanas[2]}'" if len(frases_cercanas) > 2 and 'Coco' in frases_cercanas[2] else '',
            
            # Capacidades
            'capacidades_dispositivos': ', '.join(
                cap for cap in context.personalization_data.get('mis_capacidades', [])
                if 'control' in cap or 'dispositivo' in cap
            ) or 'control básico de dispositivos',
            
            # Confirmación para dispositivos
            'confirmacion_nota': '- Siempre confirma antes de ejecutar acciones' 
                if context.personalization_data.get('confirmacion_requerida', True)
                else '- Ejecuta acciones directamente',
            
            # Entretenimiento
            'personalidad_humor': 'Usa humor familiar y apropiado'
                if context.personalization_data.get('nivel_humor') == 'familiar'
                else 'Mantén un tono divertido pero respetuoso',
            
            'estilo_entretenimiento': 'Divertido y expresivo'
                if context.personalization_data.get('personalidad_entretenimiento') == 'divertida'
                else 'Amigable y educado'
        }
        
        # Reemplazar variables en la plantilla
        try:
            return template.format(**personalization_vars)
        except KeyError as e:
            logger.warning(f"Variable no encontrada en plantilla: {e}")
            return template
    
    def _adapt_for_preferences(self, prompt: str, context: QueryContext) -> str:
        """
        Adapta el prompt según las preferencias del usuario
        
        Args:
            prompt (str): Prompt base
            context (QueryContext): Contexto con preferencias
            
        Returns:
            str: Prompt adaptado
        """
        adaptations = []
        
        # Respuestas cortas
        if context.personalization_data.get('respuestas_cortas', True):
            adaptations.append("IMPORTANTE: Mantén respuestas MUY cortas (máximo 40 palabras).")
        
        # Emojis
        if context.personalization_data.get('usar_emojis', False):
            adaptations.append("Puedes usar emojis apropiados para adultos mayores.")
        else:
            adaptations.append("NO uses emojis en las respuestas.")
        
        # Estilo de conversación
        estilo = context.personalization_data.get('estilo_conversacion', 'cercano_respetuoso')
        if estilo == 'cercano_respetuoso':
            adaptations.append("Tono: Cercano pero respetuoso, como una buena amistad.")
        elif estilo == 'formal_profesional':
            adaptations.append("Tono: Formal y profesional.")
        elif estilo == 'familiar_cariñoso':
            adaptations.append("Tono: Familiar y cariñoso.")
        
        # Referencias personales
        if context.personalization_data.get('incluir_referencias', True):
            adaptations.append("Incluye referencias personales cuando sea apropiado.")
        
        # Agregar adaptaciones al prompt
        if adaptations:
            adaptation_text = "\n\nADAPTACIONES ESPECÍFICAS:\n" + "\n".join(f"- {a}" for a in adaptations)
            return prompt + adaptation_text
        
        return prompt
    
    def _add_query_context(self, prompt: str, context: QueryContext, user_query: str) -> str:
        """
        Añade contexto específico de la consulta al prompt
        
        Args:
            prompt (str): Prompt base
            context (QueryContext): Contexto de la consulta
            user_query (str): Consulta original del usuario
            
        Returns:
            str: Prompt con contexto de consulta
        """
        query_info = []
        
        # Tipo de pregunta
        question_type = context.query_characteristics.get('tipo_pregunta')
        if question_type and question_type != 'declaracion':
            type_names = {
                'que': 'pregunta sobre qué',
                'como': 'pregunta sobre cómo',
                'cuando': 'pregunta sobre cuándo',
                'donde': 'pregunta sobre dónde',
                'quien': 'pregunta sobre quién',
                'por_que': 'pregunta sobre por qué',
                'cuanto': 'pregunta sobre cantidad'
            }
            query_info.append(f"Tipo: {type_names.get(question_type, question_type)}")
        
        # Tono detectado
        tone = context.query_characteristics.get('tono_detectado', 'neutral')
        if tone != 'neutral':
            tone_guidance = {
                'positivo': 'El usuario parece estar de buen ánimo',
                'negativo': 'El usuario puede estar frustrado, responde con extra empatía',
                'urgente': 'El usuario necesita una respuesta rápida y directa'
            }
            if tone in tone_guidance:
                query_info.append(tone_guidance[tone])
        
        # Menciones de tiempo
        if context.query_characteristics.get('menciona_tiempo', False):
            query_info.append(f"Contexto temporal relevante: {context.temporal_context['periodo_dia']}")
        
        # Añadir información al prompt
        if query_info:
            context_text = "\n\nCONTEXTO DE LA CONSULTA:\n" + "\n".join(f"- {info}" for info in query_info)
            return prompt + context_text
        
        return prompt
    
    def _add_memory_context(self, prompt: str, memory_context: Dict[str, Any] = None) -> str:
        """
        Añade contexto de memoria conversacional al prompt si está disponible
        
        Args:
            prompt (str): Prompt base
            memory_context (Dict): Contexto de memoria conversacional
            
        Returns:
            str: Prompt con contexto de memoria
        """
        if not memory_context or not memory_context.get('has_memory'):
            return prompt
        
        memory_reason = memory_context.get('memory_reason', 'unknown')
        minutes_ago = memory_context.get('minutes_ago', 0)
        last_query = memory_context.get('last_query', '')
        last_response = memory_context.get('last_response', '')
        
        # Crear contexto de memoria conciso
        memory_text = f"""
CONTEXTO CONVERSACIONAL (hace {minutes_ago} min):
Usuario preguntó: "{last_query}"
Yo respondí: "{last_response}"

NOTA: La consulta actual parece relacionada ({memory_reason}). 
Usa este contexto para dar una respuesta coherente y conectada."""
        
        return prompt + "\n\n" + memory_text
    
    def build_personalized_prompt(self, user_query: str, context: QueryContext, memory_context: Dict[str, Any] = None) -> str:
        """
        Construye un prompt personalizado completo con memoria conversacional opcional
        
        Args:
            user_query (str): Consulta del usuario
            context (QueryContext): Contexto enriquecido
            memory_context (Dict): Contexto de memoria conversacional opcional
            
        Returns:
            str: Prompt personalizado listo para usar
        """
        try:
            # 1. Empezar con el prompt base del sistema (personalizado)
            user_name = context.personalization_data.get('nombre_usuario', 'Usuario')
            prompt = self._get_base_system_prompt(user_name)
            
            # 2. Agregar plantilla específica del dominio
            domain_template = self.domain_templates.get(context.domain, self.domain_templates['general'])
            personalized_template = self._personalize_template(domain_template, context)
            prompt += "\n\n" + personalized_template
            
            # 3. Adaptar según preferencias del usuario
            prompt = self._adapt_for_preferences(prompt, context)
            
            # 4. Añadir contexto específico de la consulta
            prompt = self._add_query_context(prompt, context, user_query)
            
            # 5. Añadir memoria conversacional si está disponible
            prompt = self._add_memory_context(prompt, memory_context)
            
            # 6. Añadir la consulta del usuario al final
            prompt += f"\n\nCONSULTA DEL USUARIO:\n{user_query}\n\nRESPUESTA:"
            
            logger.debug(f"Prompt personalizado construido para dominio '{context.domain}' (memoria: {bool(memory_context)})")
            return prompt
            
        except Exception as e:
            logger.error(f"Error construyendo prompt personalizado: {e}")
            # Fallback a prompt básico
            fallback_prompt = self._get_base_system_prompt("Usuario")
            return f"{fallback_prompt}\n\nUsuario: {user_query}\nAsistente:"
    
    def build_simple_prompt(self, user_query: str, system_context: str = None) -> str:
        """
        Construye un prompt simple sin personalización (para compatibilidad)
        
        Args:
            user_query (str): Consulta del usuario
            system_context (str): Contexto del sistema opcional
            
        Returns:
            str: Prompt simple
        """
        if system_context:
            return f"{system_context}\n\nUsuario: {user_query}\nAsistente:"
        else:
            base_prompt = self._get_base_system_prompt("Usuario")
            return f"{base_prompt}\n\nUsuario: {user_query}\nAsistente:"
    
    def get_prompt_summary(self, user_query: str, context: QueryContext) -> Dict[str, Any]:
        """
        Obtiene un resumen del prompt construido para debugging
        
        Args:
            user_query (str): Consulta del usuario
            context (QueryContext): Contexto enriquecido
            
        Returns:
            Dict[str, Any]: Resumen del prompt
        """
        prompt = self.build_personalized_prompt(user_query, context)
        
        return {
            'domain': context.domain,
            'prompt_length': len(prompt),
            'personalization_applied': {
                'user_name': context.personalization_data.get('nombre_usuario'),
                'personality': context.personalization_data.get('personalidad'),
                'short_responses': context.personalization_data.get('respuestas_cortas'),
                'use_emojis': context.personalization_data.get('usar_emojis'),
                'period_of_day': context.temporal_context.get('periodo_dia')
            },
            'query_characteristics': {
                'type': context.query_characteristics.get('tipo_pregunta'),
                'tone': context.query_characteristics.get('tono_detectado'),
                'is_question': context.query_characteristics.get('es_pregunta')
            },
            'template_used': context.domain
        }