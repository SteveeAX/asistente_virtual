#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
MessageAI - Sistema de mensajes inteligentes para Asistente Kata

Utiliza IA generativa para procesar comandos de mensajes de forma
inteligente, extrayendo contactos, contenido y acciones.

Autor: Asistente Kata
"""

import logging
import re
from typing import Dict, Any, Optional, List

logger = logging.getLogger(__name__)

class MessageAI:
    """Sistema de mensajes inteligentes con IA"""
    
    def __init__(self, gemini_client, db_service):
        """
        Inicializa el sistema de mensajes con IA
        
        Args:
            gemini_client: Cliente de Gemini API
            db_service: Servicio de base de datos
        """
        self.gemini_client = gemini_client
        self.db_service = db_service
        
        # Patrones de comandos de mensajes
        self.message_patterns = [
            r"envía\s+.*mensaje.*a.*",
            r"manda\s+.*mensaje.*a.*", 
            r"enviar\s+mensaje.*",
            r"mandar\s+mensaje.*",
            r"dile\s+a.*que.*",
            r"avísale\s+a.*",
            r"comunícale\s+a.*"
        ]
        
        logger.info("MESSAGE_AI: Sistema de mensajes inteligente inicializado")
    
    def is_message_command(self, text: str) -> bool:
        """
        Verifica si el texto es un comando de mensaje
        
        Args:
            text (str): Texto a verificar
            
        Returns:
            bool: True si es comando de mensaje
        """
        text_lower = text.lower()
        
        for pattern in self.message_patterns:
            if re.search(pattern, text_lower):
                return True
        
        return False
    
    def process_message_to_first_person(self, message_body: str, command_type: str = "dice", user_name: str = "Usuario") -> str:
        """
        Procesa el cuerpo del mensaje para convertirlo a primera persona.
        
        Args:
            message_body (str): Cuerpo del mensaje ("que llegué bien", "si ya comió")
            command_type (str): Tipo de comando ("dice", "pregunta") 
            user_name (str): Nombre del usuario que envía
            
        Returns:
            str: Mensaje procesado en primera persona
            
        Ejemplos:
            "que llegué bien" + "dice" → "Marina dice: Llegué bien"
            "si ya comió" + "pregunta" → "Marina pregunta: ¿Ya comiste?"
        """
        try:
            logger.info(f"MESSAGE_AI: Procesando mensaje a primera persona - '{message_body}'")
            
            # Limpiar "que" al inicio si existe
            clean_message = self._clean_message_start(message_body)
            
            # Convertir a primera persona usando reglas simples
            first_person_message = self._convert_to_first_person(clean_message)
            
            # Determinar formato según tipo de comando - MEJORADO FASE 1
            if command_type == "pregunta" or self._is_question(message_body, command_type):
                # Para preguntas, convertir a formato de pregunta
                question_message = self._convert_to_question_format(first_person_message)
                final_message = f"{user_name} pregunta: {question_message}"
            else:
                # Para declaraciones, usar formato tradicional
                final_message = f"{user_name} dice: {first_person_message}"
            
            logger.info(f"MESSAGE_AI: Mensaje procesado - '{final_message}'")
            return final_message
            
        except Exception as e:
            logger.error(f"MESSAGE_AI: Error procesando a primera persona: {e}")
            # Fallback simple
            return f"{user_name} dice: {message_body}"
    
    def _is_question(self, message_body: str, command_type: str) -> bool:
        """Detecta si el mensaje es una pregunta"""
        # Comandos que implican pregunta
        question_commands = ["preguntale", "pregúntale"]
        if command_type.lower() in [cmd.replace(" a", "") for cmd in question_commands]:
            return True
        
        # Palabras que indican pregunta
        question_words = ["qué", "que", "cuándo", "cuando", "dónde", "donde", 
                         "cómo", "como", "por qué", "por que", "si", "acaso"]
        
        message_lower = message_body.lower()
        for word in question_words:
            if word in message_lower:
                return True
                
        return message_body.strip().endswith('?')
    
    def _clean_message_start(self, message_body: str) -> str:
        """Limpia el inicio del mensaje removiendo 'que' innecesario"""
        message = message_body.strip()
        
        # Remover "que" al inicio
        if message.lower().startswith("que "):
            message = message[4:]
        
        return message.strip()
    
    def _convert_to_first_person(self, message: str) -> str:
        """
        Convierte mensaje a primera persona usando reglas simples.
        En el futuro se puede expandir con IA.
        """
        # Conversiones comunes de segunda/tercera persona a primera
        conversions = {
            # Verbos comunes
            'llegaste': 'llegué',
            'comiste': 'comí', 
            'dormiste': 'dormí',
            'saliste': 'salí',
            'viniste': 'vine',
            'fuiste': 'fui',
            'hiciste': 'hice',
            'dijiste': 'dije',
            
            # Formas reflexivas
            'te levantaste': 'me levanté',
            'te acostaste': 'me acosté',
            'te bañaste': 'me bañé',
            
            # Posesivos
            'tu casa': 'mi casa',
            'tus cosas': 'mis cosas',
            'tu familia': 'mi familia',
            
            # Casos especiales para preguntas
            'ya comió': 'ya comí',
            'ya llegó': 'ya llegué',
            'está bien': 'estoy bien',
            'se siente': 'me siento'
        }
        
        result = message
        
        # Aplicar conversiones
        for original, converted in conversions.items():
            result = re.sub(r'\b' + re.escape(original) + r'\b', converted, result, flags=re.IGNORECASE)
        
        return result
    
    def _convert_to_question_format(self, message: str) -> str:
        """
        Convierte mensaje a formato de pregunta para segunda persona.
        
        Args:
            message (str): Mensaje en primera persona
            
        Returns:
            str: Pregunta en segunda persona
        """
        # Conversiones de primera persona a pregunta (segunda persona)
        question_conversions = {
            'ya comí': '¿ya comiste?',
            'ya llegué': '¿ya llegaste?', 
            'estoy bien': '¿estás bien?',
            'me siento': '¿te sientes',
            'tengo': '¿tienes',
            'puedo': '¿puedes',
            'voy': '¿vas',
            'vine': '¿viniste?',
            'salí': '¿saliste?',
            'hice': '¿hiciste?'
        }
        
        result = message.lower().strip()
        
        # Aplicar conversiones específicas
        for first_person, question in question_conversions.items():
            if first_person in result:
                result = result.replace(first_person, question)
                return result
        
        # Si no hay conversión específica, agregar ¿ y ? si no los tiene
        if not result.startswith('¿'):
            result = '¿' + result
        if not result.endswith('?'):
            result = result + '?'
            
        return result
    
    def _extract_message_info(self, text: str) -> Dict[str, Any]:
        """
        Extrae información del comando de mensaje
        
        Args:
            text (str): Texto del comando
            
        Returns:
            Dict con información extraída
        """
        try:
            text_lower = text.lower()
            
            # Buscar patrones comunes
            if "hijo" in text_lower:
                contact = "hijo"
                # Extraer mensaje después de "dile que" o similar
                content_match = re.search(r"dile?\s+que\s+(.+)", text_lower)
                content = content_match.group(1) if content_match else "mensaje"
                
                return {
                    'success': True,
                    'contact': contact,
                    'content': content
                }
            
            # Más patrones aquí...
            
            return {
                'success': False,
                'contact': None,
                'content': None
            }
            
        except Exception as e:
            logger.error(f"MESSAGE_AI: Error extrayendo información: {e}")
            return {
                'success': False,
                'contact': None,
                'content': None
            }