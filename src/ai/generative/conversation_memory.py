#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
ConversationMemory - Gestor de memoria conversacional ligera

Gestiona el almacenamiento y recuperación selectiva del último intercambio
conversacional para mejorar la coherencia de las respuestas.

Autor: Asistente Kata
Fecha: 2025-01-20
Versión: 1.0.0
"""

import sqlite3
import logging
import uuid
import re
from datetime import datetime, timedelta
from typing import Dict, Any, Optional, Tuple
from dataclasses import dataclass

logger = logging.getLogger(__name__)

@dataclass
class LastInteraction:
    """Representa el último intercambio conversacional"""
    user_query: str
    ai_response: str
    domain_detected: str
    confidence: float
    timestamp: datetime
    minutes_ago: int

class ConversationMemory:
    """
    Gestor de memoria conversacional que almacena y recupera selectivamente
    el último intercambio para mejorar la coherencia de las respuestas.
    """
    
    def __init__(self, db_path: str):
        """
        Inicializa el gestor de memoria conversacional.
        
        Args:
            db_path: Ruta a la base de datos del usuario actual
        """
        self.db_path = db_path
        self.session_id = str(uuid.uuid4())[:8]  # ID de sesión corto
        
        # Configuración
        self.memory_window_minutes = 10  # Ventana de memoria activa
        self.strict_window_minutes = 2   # Ventana estricta para contexto automático
        self.max_query_length = 200      # Máximo tamaño de consulta a recordar
        self.max_response_length = 300   # Máximo tamaño de respuesta a recordar
        
        # Palabras clave que indican referencia al intercambio anterior
        self.reference_keywords = [
            'eso', 'esto', 'también', 'además', 'igual', 'parecido',
            'lo mismo', 'otra vez', 'de nuevo', 'como antes',
            'y eso', 'eso cómo', 'eso cuándo', 'eso dónde'
        ]
        
        # Palabras que indican continuación de tema
        self.continuation_keywords = [
            'más información', 'más detalles', 'cuéntame más',
            'explica mejor', 'dime más', 'otro ejemplo',
            'otra forma', 'alternativa', 'diferente manera'
        ]
        
        # Palabras que indican cambio de tema explícito
        self.topic_change_keywords = [
            'cambiando de tema', 'otra cosa', 'ahora pregunto',
            'por cierto', 'y otra pregunta', 'algo diferente',
            'cambiemos', 'dejemos eso', 'otra consulta',
            'ahora quiero saber', 'pregunta diferente'
        ]
        
        # Dominios que son cambios "fuertes" (muy diferentes entre sí)
        self.strong_domain_changes = {
            'plantas': ['dispositivos', 'tiempo', 'personal'],
            'cocina': ['dispositivos', 'tiempo', 'personal'], 
            'tiempo': ['plantas', 'cocina', 'mascotas', 'dispositivos', 'personal'],
            'dispositivos': ['plantas', 'cocina', 'entretenimiento', 'tiempo', 'personal'],
            'personal': ['plantas', 'cocina', 'dispositivos', 'tiempo'],
            'mascotas': ['dispositivos', 'tiempo', 'personal'],
            'entretenimiento': ['dispositivos', 'tiempo', 'personal'],
            'informacion': [],  # Información es neutral, no bloquea
            'conversacional': [],  # Conversacional es neutral
            'general': []  # General es neutral
        }
        
        logger.info(f"ConversationMemory inicializada (sesión: {self.session_id})")
    
    def save_interaction(self, user_query: str, ai_response: str, 
                        domain: str = None, confidence: float = 0.0):
        """
        Guarda un intercambio conversacional en la base de datos.
        
        Args:
            user_query: Consulta del usuario
            ai_response: Respuesta del asistente
            domain: Dominio detectado
            confidence: Confianza de la respuesta
        """
        try:
            # Truncar textos si son muy largos
            truncated_query = user_query[:self.max_query_length]
            truncated_response = ai_response[:self.max_response_length]
            
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                cursor.execute("""
                    INSERT INTO conversation_memory 
                    (session_id, user_query, ai_response, domain_detected, confidence)
                    VALUES (?, ?, ?, ?, ?)
                """, (
                    self.session_id,
                    truncated_query,
                    truncated_response,
                    domain or 'unknown',
                    confidence
                ))
                conn.commit()
            
            logger.debug(f"Intercambio guardado: {truncated_query[:50]}...")
            
        except Exception as e:
            logger.error(f"Error guardando intercambio: {e}")
    
    def get_last_interaction(self) -> Optional[LastInteraction]:
        """
        Obtiene el último intercambio dentro de la ventana de memoria.
        
        Returns:
            LastInteraction o None si no hay intercambio reciente
        """
        try:
            # Calcular límite de tiempo
            time_limit = datetime.now() - timedelta(minutes=self.memory_window_minutes)
            
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                cursor.execute("""
                    SELECT user_query, ai_response, domain_detected, confidence, timestamp
                    FROM conversation_memory 
                    WHERE session_id = ? AND timestamp > ?
                    ORDER BY timestamp DESC 
                    LIMIT 1
                """, (self.session_id, time_limit.isoformat()))
                
                result = cursor.fetchone()
                
                if result:
                    user_query, ai_response, domain, confidence, timestamp_str = result
                    timestamp = datetime.fromisoformat(timestamp_str)
                    minutes_ago = int((datetime.now() - timestamp).total_seconds() / 60)
                    
                    return LastInteraction(
                        user_query=user_query,
                        ai_response=ai_response,
                        domain_detected=domain,
                        confidence=confidence,
                        timestamp=timestamp,
                        minutes_ago=minutes_ago
                    )
        
        except Exception as e:
            logger.error(f"Error obteniendo último intercambio: {e}")
        
        return None
    
    def should_use_memory(self, current_query: str) -> Tuple[bool, str]:
        """
        Determina si se debe usar la memoria conversacional usando estrategia híbrida mejorada.
        
        Args:
            current_query: Consulta actual del usuario
            
        Returns:
            Tuple[bool, str]: (usar_memoria, razón)
        """
        # Obtener último intercambio
        last = self.get_last_interaction()
        if not last:
            return False, "no_previous_interaction"
        
        current_lower = current_query.lower()
        
        # 1. BLOQUEO: Cambio de tema explícito por el usuario
        if any(keyword in current_lower for keyword in self.topic_change_keywords):
            return False, "explicit_topic_change"
        
        # 2. ALTA PRIORIDAD: Referencias explícitas (siempre válidas)
        if any(keyword in current_lower for keyword in self.reference_keywords):
            return True, "explicit_reference"
        
        # 3. ALTA PRIORIDAD: Solicitudes de continuación (siempre válidas)
        if any(keyword in current_lower for keyword in self.continuation_keywords):
            return True, "continuation_request"
        
        # 4. BLOQUEO: Cambio de dominio fuerte (solo si no hay referencias explícitas)
        current_domain = self._detect_query_domain(current_query)
        if self._is_strong_domain_change(current_domain, last.domain_detected):
            return False, "strong_domain_change"
        
        # 5. PRIORIDAD MEDIA: Ventana temporal estricta (ya pasó filtro de dominio)
        if last.minutes_ago <= self.strict_window_minutes:
            return True, "active_conversation_window"
        
        # 6. PRIORIDAD BAJA: Mismo dominio y consulta corta
        if (len(current_query.split()) <= 5 and 
            self._is_same_domain(current_query, last.domain_detected) and
            last.minutes_ago <= 5):  # Máximo 5 minutos para esta regla
            return True, "same_domain_short_query"
        
        # 7. PRIORIDAD BAJA: Consulta incompleta sin contexto
        if (self._seems_incomplete_without_context(current_query) and 
            last.minutes_ago <= 3):  # Solo si es muy reciente
            return True, "incomplete_without_context"
        
        return False, "no_memory_needed"
    
    def _is_same_domain(self, current_query: str, last_domain: str) -> bool:
        """Verifica si la consulta actual es del mismo dominio que la anterior"""
        if not last_domain or last_domain == 'unknown':
            return False
        
        # Mapeo simple de dominios a palabras clave
        domain_keywords = {
            'plantas': ['planta', 'sábila', 'regar', 'cuidar'],
            'cocina': ['receta', 'cocinar', 'comida', 'preparar'],
            'mascotas': ['perro', 'mascota', 'coco', 'troy'],
            'tiempo': ['clima', 'lluvia', 'temperatura'],
            'dispositivos': ['enchufe', 'luz', 'encender', 'apagar']
        }
        
        if last_domain in domain_keywords:
            keywords = domain_keywords[last_domain]
            return any(keyword in current_query.lower() for keyword in keywords)
        
        return False
    
    def _seems_incomplete_without_context(self, query: str) -> bool:
        """Verifica si la consulta parece incompleta sin contexto previo"""
        query_lower = query.lower()
        
        # Consultas que típicamente necesitan contexto
        incomplete_patterns = [
            r'^(y|pero|entonces|así|por eso)',  # Conectores al inicio
            r'^(cómo|cuándo|dónde|qué)\s+\w{1,3}\s*\?*$',  # Preguntas muy cortas
            r'^(sí|si|no|tal vez|puede ser)',  # Respuestas a preguntas previas
            r'^(otra|otro|más|menos)\s+\w*$'   # Referencias comparativas
        ]
        
        return any(re.match(pattern, query_lower) for pattern in incomplete_patterns)
    
    def _detect_query_domain(self, query: str) -> str:
        """
        Detecta el dominio de la consulta actual usando las mismas palabras clave
        que ContextEnricher pero de forma simplificada.
        """
        query_lower = query.lower()
        
        # Mapeo simple de palabras clave a dominios (versión reducida)
        domain_keywords = {
            'plantas': ['planta', 'sábila', 'regar', 'jardín', 'hierba'],
            'cocina': ['cocina', 'receta', 'comida', 'cocinar', 'preparar', 'paella', 'ingredientes', 'plato', 'arroz'],
            'mascotas': ['perro', 'mascota', 'coco', 'troy'],
            'tiempo': ['tiempo', 'clima', 'lluvia', 'temperatura', 'hora', 'qué hora'],
            'dispositivos': ['enchufe', 'luz', 'encender', 'apagar'],
            'personal': ['nombre', 'quién eres', 'familia', 'cómo te llamas', 'te llamas'],
            'informacion': ['qué es', 'cómo se', 'explica', 'cuéntame', 'dime']
        }
        
        # Buscar coincidencias
        for domain, keywords in domain_keywords.items():
            if any(keyword in query_lower for keyword in keywords):
                return domain
        
        return 'general'
    
    def _is_strong_domain_change(self, current_domain: str, last_domain: str) -> bool:
        """
        Verifica si hay un cambio de dominio fuerte que debería resetear la memoria.
        """
        if not last_domain or last_domain in ['general', 'informacion', 'conversacional']:
            return False  # Dominios neutrales no bloquean
        
        if current_domain in ['general', 'informacion', 'conversacional']:
            return False  # Hacia dominios neutrales no es bloqueo fuerte
        
        # Verificar si es un cambio fuerte según la configuración
        blocked_domains = self.strong_domain_changes.get(last_domain, [])
        return current_domain in blocked_domains
    
    def get_memory_context(self, current_query: str) -> Optional[Dict[str, Any]]:
        """
        Obtiene el contexto de memoria si es apropiado para la consulta actual.
        
        Args:
            current_query: Consulta actual del usuario
            
        Returns:
            Dict con contexto de memoria o None si no se debe usar
        """
        should_use, reason = self.should_use_memory(current_query)
        
        if not should_use:
            logger.debug(f"Memoria no usada: {reason}")
            return None
        
        last = self.get_last_interaction()
        if not last:
            return None
        
        # Truncar respuesta anterior para el contexto (máximo 100 caracteres)
        truncated_response = last.ai_response
        if len(truncated_response) > 100:
            truncated_response = truncated_response[:97] + "..."
        
        context = {
            'has_memory': True,
            'memory_reason': reason,
            'last_query': last.user_query,
            'last_response': truncated_response,
            'last_domain': last.domain_detected,
            'minutes_ago': last.minutes_ago,
            'confidence': last.confidence
        }
        
        logger.info(f"Usando memoria conversacional: {reason} (hace {last.minutes_ago} min)")
        return context
    
    def cleanup_old_conversations(self, days_to_keep: int = 7):
        """
        Limpia conversaciones antiguas para mantener la base de datos ligera.
        
        Args:
            days_to_keep: Días de conversaciones a mantener
        """
        try:
            cutoff_date = datetime.now() - timedelta(days=days_to_keep)
            
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                cursor.execute("""
                    DELETE FROM conversation_memory 
                    WHERE timestamp < ?
                """, (cutoff_date.isoformat(),))
                
                deleted_count = cursor.rowcount
                conn.commit()
            
            if deleted_count > 0:
                logger.info(f"Limpieza completada: {deleted_count} conversaciones antiguas eliminadas")
        
        except Exception as e:
            logger.error(f"Error en limpieza de conversaciones: {e}")
    
    def get_stats(self) -> Dict[str, Any]:
        """Obtiene estadísticas de la memoria conversacional"""
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                
                # Total de intercambios
                cursor.execute("SELECT COUNT(*) FROM conversation_memory")
                total_interactions = cursor.fetchone()[0]
                
                # Intercambios en sesión actual
                cursor.execute("""
                    SELECT COUNT(*) FROM conversation_memory 
                    WHERE session_id = ?
                """, (self.session_id,))
                session_interactions = cursor.fetchone()[0]
                
                # Último intercambio
                last = self.get_last_interaction()
                
                return {
                    'total_interactions': total_interactions,
                    'session_interactions': session_interactions,
                    'session_id': self.session_id,
                    'has_recent_memory': last is not None,
                    'memory_window_minutes': self.memory_window_minutes,
                    'last_interaction_minutes_ago': last.minutes_ago if last else None
                }
        
        except Exception as e:
            logger.error(f"Error obteniendo estadísticas: {e}")
            return {'error': str(e)}