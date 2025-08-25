#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
Migration: Añadir tabla de memoria conversacional

Añade la tabla conversation_memory para almacenar los últimos intercambios
de conversación entre usuarios y el asistente.

Autor: Asistente Kata
Fecha: 2025-01-20
Versión: 1.0.0
"""

import sqlite3
import os
import logging
from pathlib import Path

logger = logging.getLogger(__name__)

def add_conversation_memory_table(db_path: str):
    """
    Añade la tabla conversation_memory a una base de datos de usuario.
    
    Args:
        db_path: Ruta a la base de datos del usuario
    """
    try:
        with sqlite3.connect(db_path) as conn:
            cursor = conn.cursor()
            
            # Verificar si la tabla ya existe
            cursor.execute("""
                SELECT name FROM sqlite_master 
                WHERE type='table' AND name='conversation_memory'
            """)
            
            if cursor.fetchone():
                logger.info(f"Tabla conversation_memory ya existe en {db_path}")
                return True
            
            # Crear tabla conversation_memory
            cursor.execute("""
                CREATE TABLE conversation_memory (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    session_id TEXT NOT NULL,
                    user_query TEXT NOT NULL,
                    ai_response TEXT NOT NULL,
                    domain_detected TEXT,
                    confidence REAL,
                    timestamp DATETIME DEFAULT CURRENT_TIMESTAMP,
                    created_at DATETIME DEFAULT CURRENT_TIMESTAMP
                )
            """)
            
            # Crear índices para mejorar rendimiento
            cursor.execute("""
                CREATE INDEX idx_conversation_session 
                ON conversation_memory(session_id)
            """)
            
            cursor.execute("""
                CREATE INDEX idx_conversation_timestamp 
                ON conversation_memory(timestamp DESC)
            """)
            
            conn.commit()
            logger.info(f"Tabla conversation_memory creada exitosamente en {db_path}")
            return True
            
    except Exception as e:
        logger.error(f"Error creando tabla conversation_memory en {db_path}: {e}")
        return False

def migrate_all_users():
    """
    Ejecuta la migración en todas las bases de datos de usuarios existentes.
    """
    # Obtener ruta base del proyecto
    base_path = Path(__file__).parent.parent.parent
    users_path = base_path / "data" / "users"
    
    if not users_path.exists():
        logger.warning("Directorio de usuarios no encontrado")
        return False
    
    success_count = 0
    total_count = 0
    
    # Iterar sobre todos los directorios de usuarios
    for user_dir in users_path.iterdir():
        if user_dir.is_dir():
            user_db_path = user_dir / "user_data.db"
            if user_db_path.exists():
                total_count += 1
                logger.info(f"Migrando usuario: {user_dir.name}")
                
                if add_conversation_memory_table(str(user_db_path)):
                    success_count += 1
                    logger.info(f"Migración exitosa para usuario: {user_dir.name}")
                else:
                    logger.error(f"Migración falló para usuario: {user_dir.name}")
    
    logger.info(f"Migración completada: {success_count}/{total_count} usuarios migrados")
    return success_count == total_count

if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    migrate_all_users()