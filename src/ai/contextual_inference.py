#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
ContextualInferenceEngine - Motor de Inferencia Contextual para Asistente Kata

Implementa la Fase 2 del sistema de adaptabilidad:
- Detecta patrones indirectos de comunicación 
- Infiere intención de contacto automáticamente
- Mapea referencias implícitas a comandos explícitos

Autor: Asistente Kata - Fase 2
"""

import logging
import re
from typing import Optional, Tuple, List, Dict, Any

logger = logging.getLogger(__name__)

class ContextualInferenceEngine:
    """
    Motor de inferencia contextual que detecta patrones indirectos 
    y los convierte en comandos explícitos de comunicación.
    """
    
    def __init__(self, db_manager=None, contact_normalizer=None):
        """
        Inicializa el motor de inferencia contextual
        
        Args:
            db_manager: Gestor de base de datos para contactos
            contact_normalizer: Normalizador de nombres de contactos
        """
        self.db_manager = db_manager
        self.contact_normalizer = contact_normalizer
        
        # Patrones de inferencia contextual - detectan intención indirecta
        self.contextual_patterns = [
            # Patrón: "quiero saber de Monica a qué hora viene"
            {
                "pattern": r"(quiero saber|me gustaría saber|quisiera saber|me interesa saber)\s+(?:de\s+|sobre\s+|si\s+)?(.+?)\s+(a qué\s+.+|qué\s+.+|cuándo\s+.+|dónde\s+.+|cómo\s+.+|si\s+.+|cuando\s+.+|donde\s+.+|como\s+.+)",
                "inferred_command": "pregúntale a",
                "confidence": 0.9
            },
            
            # Patrón: "necesito saber si Ana ya llegó"  
            {
                "pattern": r"(necesito saber|tengo que saber|debo saber)\s+(?:si\s+|que\s+)?(.+?)\s+(ya\s+.+|está\s+.+|viene\s+.+|va\s+.+|llegó\s+.+|puede\s+.+|tiene\s+.+|sabe\s+.+)",
                "inferred_command": "pregúntale a", 
                "confidence": 0.8
            },
            
            # Patrón: "me pregunto si Luis está bien"
            {
                "pattern": r"(me pregunto si|no sé si|será que)\s+(.+?)\s+(está\s+.+|se siente\s+.+|ya\s+.+|viene\s+.+|puede\s+.+|tiene\s+.+|llegó\s+.+|va\s+.+)",
                "inferred_command": "pregúntale a",
                "confidence": 0.85
            },
            
            # Patrón: "averigua con Maria si puede venir"
            {
                "pattern": r"(averigua con|consulta con|pregunta a|ve con)\s+(.+?)\s+(si\s+.+|que\s+.+|cuando\s+.+|cómo\s+.+|a qué\s+.+)",
                "inferred_command": "pregúntale a",
                "confidence": 0.95
            }
        ]
        
        logger.info("ContextualInferenceEngine: Motor de inferencia contextual inicializado (Fase 2)")
    
    def can_infer_message_intent(self, text: str) -> bool:
        """
        Determina si el texto contiene una intención de mensaje inferible
        
        Args:
            text (str): Texto del usuario
            
        Returns:
            bool: True si puede inferir intención de mensaje
        """
        if not text:
            return False
            
        text_clean = text.lower().strip()
        
        # Verificar si algún patrón contextual coincide
        for pattern_info in self.contextual_patterns:
            if re.search(pattern_info["pattern"], text_clean):
                logger.debug(f"ContextualInference: Patrón contextual detectado - '{pattern_info['pattern'][:30]}...'")
                return True
        
        return False
    
    def infer_message_command(self, text: str) -> Optional[Tuple[str, str, str, float]]:
        """
        Infiere comando de mensaje desde texto contextual indirecto
        
        Args:
            text (str): Texto contextual del usuario
            
        Returns:
            Tuple[comando, contacto, mensaje, confianza] o None si no puede inferir
            
        Ejemplos:
            "quiero saber de Monica a qué hora viene" → ("pregúntale a", "Monica", "a qué hora vienes", 0.9)
            "necesito saber si Ana ya llegó" → ("pregúntale a", "Ana", "si ya llegaste", 0.8)
        """
        if not text:
            return None
            
        text_clean = text.lower().strip()
        
        # Intentar cada patrón contextual
        for pattern_info in self.contextual_patterns:
            match = re.search(pattern_info["pattern"], text_clean)
            if match:
                try:
                    starter = match.group(1).strip()
                    potential_contact = match.group(2).strip()
                    question_part = match.group(3).strip()
                    
                    logger.debug(f"ContextualInference: Coincidencia - starter='{starter}', contacto='{potential_contact}', pregunta='{question_part}'")
                    
                    # Validar que el contacto potencial existe
                    validated_contact = self._validate_contact_exists(potential_contact)
                    if not validated_contact:
                        logger.debug(f"ContextualInference: Contacto '{potential_contact}' no validado")
                        continue
                    
                    # Transformar mensaje a segunda persona para pregunta
                    transformed_message = self._transform_to_second_person(question_part)
                    
                    # Construir comando inferido
                    inferred_command = pattern_info["inferred_command"]
                    confidence = pattern_info["confidence"]
                    
                    logger.info(f"ContextualInference: INFERIDO - '{text}' → comando='{inferred_command}', contacto='{validated_contact}', mensaje='{transformed_message}', confianza={confidence}")
                    
                    return (inferred_command, validated_contact, transformed_message, confidence)
                    
                except Exception as e:
                    logger.error(f"ContextualInference: Error procesando patrón: {e}")
                    continue
        
        return None
    
    def _validate_contact_exists(self, potential_contact: str) -> Optional[str]:
        """
        Valida que el contacto potencial existe en la base de datos
        
        Args:
            potential_contact (str): Nombre potencial del contacto
            
        Returns:
            str: Nombre validado del contacto o None si no existe
        """
        if not self.db_manager or not self.contact_normalizer:
            logger.warning("ContextualInference: DB o normalizador no disponible para validación")
            return potential_contact  # Asumir válido si no podemos validar
        
        try:
            # Obtener lista de contactos disponibles
            available_contacts = self._get_available_contacts()
            
            # Intentar encontrar coincidencia usando el normalizador existente
            matched_contact = self.contact_normalizer.find_best_match(
                potential_contact, available_contacts
            )
            
            if matched_contact:
                logger.debug(f"ContextualInference: Contacto validado '{potential_contact}' → '{matched_contact}'")
                return matched_contact
            else:
                logger.debug(f"ContextualInference: Contacto '{potential_contact}' no encontrado en BD")
                return None
                
        except Exception as e:
            logger.error(f"ContextualInference: Error validando contacto: {e}")
            return None
    
    def _get_available_contacts(self) -> List[Dict[str, Any]]:
        """
        Obtiene lista de contactos disponibles desde BD
        
        Returns:
            List[Dict]: Lista de contactos con nombres y alias
        """
        try:
            if not self.db_manager:
                return []
            
            with self.db_manager.get_connection() as conn:
                cursor = conn.cursor()
                cursor.execute("""
                    SELECT display_name, aliases 
                    FROM contacts 
                    WHERE is_active = TRUE 
                    ORDER BY display_name
                """)
                
                contacts = []
                for row in cursor.fetchall():
                    import json
                    aliases = json.loads(row['aliases']) if row['aliases'] else []
                    
                    contacts.append({
                        'display_name': row['display_name'],
                        'aliases': aliases
                    })
                
                logger.debug(f"ContextualInference: {len(contacts)} contactos cargados para validación")
                return contacts
                
        except Exception as e:
            logger.error(f"ContextualInference: Error obteniendo contactos: {e}")
            return []
    
    def _transform_to_second_person(self, question_part: str) -> str:
        """
        Transforma pregunta de tercera persona a segunda persona
        
        Args:
            question_part (str): Parte de pregunta ("a qué hora viene", "ya llegó")
            
        Returns:
            str: Pregunta transformada para segunda persona
        """
        # Transformaciones contextuales tercera → segunda persona
        transformations = {
            # Tiempos verbales
            'viene': 'vienes',
            'va': 'vas', 
            'está': 'estás',
            'llegó': 'llegaste',
            'salió': 'saliste',
            'comió': 'comiste',
            'durmió': 'dormiste',
            'se siente': 'te sientes',
            'puede': 'puedes',
            'tiene': 'tienes',
            'sabe': 'sabes',
            'quiere': 'quieres',
            
            # Construcciones temporales
            'a qué hora viene': 'a qué hora vienes',
            'cuándo llega': 'cuándo llegas',
            'dónde está': 'dónde estás',
            'cómo está': 'cómo estás',
            'qué hace': 'qué haces',
            'si ya llegó': 'si ya llegaste',
            'si está bien': 'si estás bien'
        }
        
        result = question_part.strip()
        
        # Aplicar transformaciones
        for third_person, second_person in transformations.items():
            result = re.sub(r'\b' + re.escape(third_person) + r'\b', 
                          second_person, result, flags=re.IGNORECASE)
        
        return result
    
    def get_inference_stats(self) -> Dict[str, Any]:
        """
        Retorna estadísticas del motor de inferencia
        
        Returns:
            Dict: Estadísticas de rendimiento y uso
        """
        return {
            "patterns_loaded": len(self.contextual_patterns),
            "db_available": self.db_manager is not None,
            "normalizer_available": self.contact_normalizer is not None,
            "phase": "2 - Contextual Inference Engine"
        }

def initialize_contextual_inference(db_manager=None, contact_normalizer=None) -> Optional[ContextualInferenceEngine]:
    """
    Inicializa y retorna una instancia del motor de inferencia contextual
    
    Args:
        db_manager: Gestor de base de datos
        contact_normalizer: Normalizador de contactos
        
    Returns:
        ContextualInferenceEngine o None si falla
    """
    try:
        engine = ContextualInferenceEngine(db_manager, contact_normalizer)
        logger.info("ContextualInferenceEngine: Inicializado exitosamente")
        return engine
    except Exception as e:
        logger.error(f"Error inicializando ContextualInferenceEngine: {e}")
        return None