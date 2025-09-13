#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
ContactNormalizer - Normalizador de nombres de contacto

Limpia artículos, posesivos y variantes en nombres de contacto
para facilitar la búsqueda en base de datos.

Ejemplos:
- "la Maria" → ["Maria", "la Maria"]  
- "mi hermana" → ["hermana", "mi hermana"]
- "el doctor" → ["doctor", "el doctor"]

Autor: Asistente Kata
"""

import logging
import re
from typing import List, Set

logger = logging.getLogger(__name__)

class ContactNormalizer:
    """Normalizador de nombres de contacto para búsqueda flexible"""
    
    # Artículos y posesivos comunes en español
    ARTICLES_AND_POSSESSIVES = {
        'la', 'el', 'las', 'los',           # artículos
        'mi', 'mis', 'tu', 'tus',          # posesivos
        'su', 'sus', 'nuestro', 'nuestra',  # posesivos
        'vuestro', 'vuestra'                # posesivos
    }
    
    def __init__(self):
        logger.info("ContactNormalizer inicializado")
    
    def normalize_contact_name(self, raw_name: str) -> List[str]:
        """
        Normaliza un nombre de contacto generando variantes de búsqueda.
        
        Args:
            raw_name (str): Nombre crudo del contacto ("la Maria", "mi hermana")
            
        Returns:
            List[str]: Lista de variantes para búsqueda ["Maria", "la Maria"]
        """
        if not raw_name or not raw_name.strip():
            return []
        
        # Limpiar espacios y convertir a minúsculas para análisis
        name_clean = raw_name.strip().lower()
        variants = set()
        
        # Siempre incluir el nombre original (manteniendo capitalización)
        variants.add(raw_name.strip())
        
        # Separar en palabras
        words = name_clean.split()
        
        if not words:
            return list(variants)
        
        # Si la primera palabra es un artículo/posesivo, crear variante sin él
        first_word = words[0]
        if first_word in self.ARTICLES_AND_POSSESSIVES and len(words) > 1:
            # Crear variante sin artículo/posesivo
            name_without_article = ' '.join(words[1:])
            
            # Capitalizar apropiadamente
            name_without_article_cap = self._capitalize_name(name_without_article)
            variants.add(name_without_article_cap)
            
            logger.debug(f"Variante sin artículo: '{raw_name}' → '{name_without_article_cap}'")
        
        # Si NO empieza con artículo/posesivo, crear variantes agregándolos
        elif first_word not in self.ARTICLES_AND_POSSESSIVES:
            # Intentar con artículos comunes
            common_articles = ['la', 'el', 'mi']
            
            for article in common_articles:
                variant = f"{article} {name_clean}"
                variant_cap = self._capitalize_name(variant)
                variants.add(variant_cap)
                
                logger.debug(f"Variante con artículo: '{raw_name}' → '{variant_cap}'")
        
        result = list(variants)
        logger.info(f"ContactNormalizer: '{raw_name}' → {len(result)} variantes: {result}")
        
        return result
    
    def _capitalize_name(self, name: str) -> str:
        """
        Capitaliza apropiadamente un nombre.
        
        Args:
            name (str): Nombre en minúsculas
            
        Returns:
            str: Nombre capitalizado apropiadamente
        """
        if not name:
            return name
        
        words = name.split()
        capitalized_words = []
        
        for word in words:
            # Los artículos y posesivos van en minúscula (excepto al inicio)
            if word.lower() in self.ARTICLES_AND_POSSESSIVES and len(capitalized_words) > 0:
                capitalized_words.append(word.lower())
            else:
                # Nombres propios van capitalizados
                capitalized_words.append(word.capitalize())
        
        return ' '.join(capitalized_words)
    
    def find_best_match(self, raw_name: str, available_contacts) -> str:
        """
        Encuentra la mejor coincidencia de un nombre normalizado considerando alias.
        
        Args:
            raw_name (str): Nombre a buscar
            available_contacts: Lista de contactos (str) o diccionarios con alias
            
        Returns:
            str: Mejor coincidencia encontrada, o None si no hay match
        """
        if not available_contacts:
            return None
        
        # Generar variantes del nombre
        variants = self.normalize_contact_name(raw_name)
        
        # Determinar si available_contacts son strings o diccionarios
        if available_contacts and isinstance(available_contacts[0], dict):
            return self._find_match_with_aliases(variants, available_contacts)
        else:
            return self._find_match_simple(variants, available_contacts)
    
    def _find_match_with_aliases(self, variants: List[str], contacts_with_aliases: List[dict]) -> str:
        """
        Busca coincidencias considerando alias de contactos
        
        Args:
            variants: Variantes del nombre a buscar
            contacts_with_aliases: Lista de diccionarios con display_name y aliases
            
        Returns:
            str: display_name del contacto encontrado o None
        """
        logger.debug(f"Buscando coincidencias para variantes: {variants}")
        
        for variant in variants:
            variant_lower = variant.lower()
            
            # PRIORIDAD 1: Buscar en alias primero (más específicos)
            for contact in contacts_with_aliases:
                display_name = contact['display_name']
                aliases = contact.get('aliases', [])
                
                # Coincidencia exacta con algún alias
                for alias in aliases:
                    if variant_lower == alias.lower():
                        logger.info(f"Coincidencia exacta con alias: '{variant}' → '{display_name}' (alias: '{alias}')")
                        return display_name
            
            # PRIORIDAD 2: Buscar en nombres display después
            for contact in contacts_with_aliases:
                display_name = contact['display_name']
                
                # Coincidencia exacta con display_name
                if variant_lower == display_name.lower():
                    logger.info(f"Coincidencia exacta con nombre: '{variant}' → '{display_name}'")
                    return display_name
        
        # 3. Búsqueda parcial en nombres
        for variant in variants:
            variant_lower = variant.lower()
            
            for contact in contacts_with_aliases:
                display_name = contact['display_name']
                aliases = contact.get('aliases', [])
                
                # Coincidencia parcial con display_name
                if variant_lower in display_name.lower() or display_name.lower() in variant_lower:
                    logger.info(f"Coincidencia parcial con nombre: '{variant}' ≈ '{display_name}'")
                    return display_name
                
                # Coincidencia parcial con alias
                for alias in aliases:
                    if variant_lower in alias.lower() or alias.lower() in variant_lower:
                        logger.info(f"Coincidencia parcial con alias: '{variant}' ≈ '{display_name}' (alias: '{alias}')")
                        return display_name
        
        contact_names = [c['display_name'] for c in contacts_with_aliases]
        logger.warning(f"No se encontró coincidencia para variantes {variants} en {len(contact_names)} contactos: {contact_names}")
        return None
    
    def _find_match_simple(self, variants: List[str], available_contacts: List[str]) -> str:
        """
        Busca coincidencias en lista simple de strings (método original)
        """
        # Buscar coincidencia exacta (case-insensitive)
        for variant in variants:
            for contact in available_contacts:
                if variant.lower() == contact.lower():
                    logger.info(f"Coincidencia exacta: '{variant}' → '{contact}'")
                    return contact
        
        # Si no hay coincidencia exacta, buscar coincidencia parcial
        for variant in variants:
            for contact in available_contacts:
                if variant.lower() in contact.lower() or contact.lower() in variant.lower():
                    logger.info(f"Coincidencia parcial: '{variant}' ≈ '{contact}'")
                    return contact
        
        logger.warning(f"No se encontró coincidencia para variantes {variants} en {len(available_contacts)} contactos")
        return None

# Instancia global para uso directo
contact_normalizer = ContactNormalizer()

def normalize_contact_name(raw_name: str) -> List[str]:
    """
    Función de conveniencia para normalizar nombres de contacto.
    
    Args:
        raw_name (str): Nombre crudo del contacto
        
    Returns:
        List[str]: Lista de variantes normalizadas
    """
    return contact_normalizer.normalize_contact_name(raw_name)

def find_contact_match(raw_name: str, available_contacts: List[str]) -> str:
    """
    Función de conveniencia para encontrar mejor coincidencia.
    
    Args:
        raw_name (str): Nombre a buscar
        available_contacts (List[str]): Contactos disponibles
        
    Returns:
        str: Mejor coincidencia o None
    """
    return contact_normalizer.find_best_match(raw_name, available_contacts)