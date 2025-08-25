#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
Shared Data Manager - Gestor de datos compartidos globalmente

Este módulo gestiona los datos que son compartidos entre todos los usuarios:
- Medicamentos/recordatorios
- Tareas 
- Contactos
- Configuraciones del sistema (voz, etc.)

Solo las preferencias de personalización IA son por usuario.

Autor: Asistente Kata
Fecha: 2025-08-25
Versión: 2.0.0
"""

import sqlite3
import json
import logging
from pathlib import Path
from typing import List, Dict, Any, Optional
from datetime import datetime

logger = logging.getLogger(__name__)

class SharedDataManager:
    """
    Gestor de datos compartidos globalmente entre todos los usuarios.
    """
    
    def __init__(self, data_root: Optional[Path] = None):
        """
        Inicializa el gestor de datos compartidos.
        
        Args:
            data_root: Directorio raíz de datos (opcional)
        """
        if data_root is None:
            # Usar directorio del proyecto como base
            project_root = Path(__file__).parent.parent.parent
            data_root = project_root / "data"
        
        self.data_path = Path(data_root)
        self.system_path = self.data_path / "system"
        
        # Archivo de base de datos compartida
        self.shared_db_path = self.system_path / "shared_data.db"
        
        # Crear directorios si no existen
        self.system_path.mkdir(parents=True, exist_ok=True)
        
        # Inicializar base de datos compartida
        self._init_shared_database()
        
        logger.info(f"SharedDataManager inicializado: {self.shared_db_path}")
    
    def _init_shared_database(self):
        """Inicializa la base de datos compartida con todas las tablas necesarias."""
        try:
            with sqlite3.connect(self.shared_db_path) as conn:
                cursor = conn.cursor()
                
                # Tabla de medicamentos/recordatorios
                cursor.execute("""
                    CREATE TABLE IF NOT EXISTS reminders (
                        id INTEGER PRIMARY KEY AUTOINCREMENT,
                        name TEXT NOT NULL,
                        quantity TEXT DEFAULT '',
                        prescription TEXT DEFAULT '',
                        times TEXT NOT NULL,  -- JSON array de horarios
                        days TEXT NOT NULL,   -- JSON array de días
                        photo_path TEXT DEFAULT '',
                        is_active BOOLEAN DEFAULT TRUE,
                        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                        updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                    )
                """)
                
                # Tabla de tareas
                cursor.execute("""
                    CREATE TABLE IF NOT EXISTS tasks (
                        id INTEGER PRIMARY KEY AUTOINCREMENT,
                        name TEXT NOT NULL,
                        times TEXT NOT NULL,  -- JSON array de horarios
                        days TEXT NOT NULL,   -- JSON array de días
                        is_active BOOLEAN DEFAULT TRUE,
                        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                        updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                    )
                """)
                
                # Tabla de contactos
                cursor.execute("""
                    CREATE TABLE IF NOT EXISTS contacts (
                        id INTEGER PRIMARY KEY AUTOINCREMENT,
                        display_name TEXT NOT NULL,
                        aliases TEXT NOT NULL,    -- JSON array de aliases
                        platform TEXT NOT NULL,
                        details TEXT NOT NULL,    -- Chat ID, teléfono, etc.
                        is_emergency BOOLEAN DEFAULT FALSE,
                        is_active BOOLEAN DEFAULT TRUE,
                        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                        updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                    )
                """)
                
                # Tabla de configuraciones globales
                cursor.execute("""
                    CREATE TABLE IF NOT EXISTS settings (
                        key TEXT PRIMARY KEY,
                        value TEXT NOT NULL,
                        category TEXT DEFAULT 'general',
                        updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                    )
                """)
                
                # Insertar configuraciones por defecto
                cursor.execute("""
                    INSERT OR IGNORE INTO settings (key, value, category) 
                    VALUES ('voice_name', 'es-US-Neural2-A', 'tts')
                """)
                cursor.execute("""
                    INSERT OR IGNORE INTO settings (key, value, category) 
                    VALUES ('app_theme', 'dark', 'ui')
                """)
                
                conn.commit()
                
            logger.info("Base de datos compartida inicializada correctamente")
            
        except Exception as e:
            logger.error(f"Error inicializando base de datos compartida: {e}")
            raise
    
    def get_connection(self) -> sqlite3.Connection:
        """
        Obtiene una conexión a la base de datos compartida.
        
        Returns:
            Conexión a la BD compartida
        """
        conn = sqlite3.connect(self.shared_db_path)
        conn.row_factory = sqlite3.Row
        return conn
    
    # === MÉTODOS DE MEDICAMENTOS ===
    
    def list_medications(self) -> List[Dict[str, Any]]:
        """Lista todos los medicamentos activos."""
        try:
            with self.get_connection() as conn:
                cursor = conn.cursor()
                cursor.execute("""
                    SELECT id, name, quantity, prescription, times, days, photo_path, created_at
                    FROM reminders 
                    WHERE is_active = TRUE
                    ORDER BY created_at DESC
                """)
                
                medications = []
                for row in cursor.fetchall():
                    # Convertir formato para compatibilidad con API existente
                    times_list = json.loads(row['times']) if row['times'] else []
                    days_list = json.loads(row['days']) if row['days'] else []
                    
                    medications.append({
                        'id': row['id'],
                        'medication_name': row['name'],  # Nombre esperado por API
                        'cantidad': row['quantity'] or '',
                        'prescripcion': row['prescription'] or '',
                        'times': ','.join(times_list),   # String para compatibilidad
                        'days_of_week': ','.join(days_list),  # String para compatibilidad
                        'photo_path': row['photo_path'] or '',
                        'created_at': row['created_at']
                    })
                
                return medications
                
        except Exception as e:
            logger.error(f"Error listando medicamentos: {e}")
            return []
    
    def add_medication(self, name: str, quantity: str = "", prescription: str = "", 
                      times: List[str] = None, days: List[str] = None, 
                      photo_path: str = "") -> bool:
        """
        Agrega un medicamento.
        
        Args:
            name: Nombre del medicamento
            quantity: Cantidad (ej: "2 pastillas")
            prescription: Prescripción médica
            times: Lista de horarios (ej: ["08:00", "20:00"])
            days: Lista de días (ej: ["0", "1", "2"])  # 0=lunes
            photo_path: Ruta de la foto
            
        Returns:
            True si se agregó correctamente
        """
        try:
            if times is None:
                times = []
            if days is None:
                days = []
                
            with self.get_connection() as conn:
                cursor = conn.cursor()
                cursor.execute("""
                    INSERT INTO reminders (name, quantity, prescription, times, days, photo_path)
                    VALUES (?, ?, ?, ?, ?, ?)
                """, (
                    name, quantity, prescription,
                    json.dumps(times), json.dumps(days), photo_path
                ))
                conn.commit()
                
            logger.info(f"Medicamento agregado: {name}")
            return True
            
        except Exception as e:
            logger.error(f"Error agregando medicamento: {e}")
            return False
    
    def delete_medication(self, medication_id: int) -> bool:
        """Elimina un medicamento (soft delete)."""
        try:
            with self.get_connection() as conn:
                cursor = conn.cursor()
                cursor.execute("""
                    UPDATE reminders 
                    SET is_active = FALSE, updated_at = CURRENT_TIMESTAMP
                    WHERE id = ?
                """, (medication_id,))
                conn.commit()
                
            logger.info(f"Medicamento eliminado: {medication_id}")
            return True
            
        except Exception as e:
            logger.error(f"Error eliminando medicamento: {e}")
            return False
    
    # === MÉTODOS DE TAREAS ===
    
    def list_tasks(self) -> List[Dict[str, Any]]:
        """Lista todas las tareas activas."""
        try:
            with self.get_connection() as conn:
                cursor = conn.cursor()
                cursor.execute("""
                    SELECT id, name, times, days, created_at
                    FROM tasks 
                    WHERE is_active = TRUE
                    ORDER BY created_at DESC
                """)
                
                tasks = []
                for row in cursor.fetchall():
                    times_list = json.loads(row['times']) if row['times'] else []
                    days_list = json.loads(row['days']) if row['days'] else []
                    
                    tasks.append({
                        'id': row['id'],
                        'task_name': row['name'],  # Nombre esperado por API
                        'name': row['name'],       # Formato alternativo
                        'times': ','.join(times_list),
                        'days_of_week': ','.join(days_list),
                        'created_at': row['created_at']
                    })
                
                return tasks
                
        except Exception as e:
            logger.error(f"Error listando tareas: {e}")
            return []
    
    def add_task(self, name: str, times: List[str] = None, days: List[str] = None) -> bool:
        """Agrega una tarea."""
        try:
            if times is None:
                times = []
            if days is None:
                days = []
                
            with self.get_connection() as conn:
                cursor = conn.cursor()
                cursor.execute("""
                    INSERT INTO tasks (name, times, days)
                    VALUES (?, ?, ?)
                """, (name, json.dumps(times), json.dumps(days)))
                conn.commit()
                
            logger.info(f"Tarea agregada: {name}")
            return True
            
        except Exception as e:
            logger.error(f"Error agregando tarea: {e}")
            return False
    
    def delete_task(self, task_id: int) -> bool:
        """Elimina una tarea (soft delete)."""
        try:
            with self.get_connection() as conn:
                cursor = conn.cursor()
                cursor.execute("""
                    UPDATE tasks 
                    SET is_active = FALSE, updated_at = CURRENT_TIMESTAMP
                    WHERE id = ?
                """, (task_id,))
                conn.commit()
                
            logger.info(f"Tarea eliminada: {task_id}")
            return True
            
        except Exception as e:
            logger.error(f"Error eliminando tarea: {e}")
            return False
    
    # === MÉTODOS DE CONTACTOS ===
    
    def list_contacts(self) -> List[Dict[str, Any]]:
        """Lista todos los contactos activos."""
        try:
            with self.get_connection() as conn:
                cursor = conn.cursor()
                cursor.execute("""
                    SELECT id, display_name, aliases, platform, details, is_emergency, created_at
                    FROM contacts 
                    WHERE is_active = TRUE
                    ORDER BY display_name
                """)
                
                contacts = []
                for row in cursor.fetchall():
                    aliases_list = json.loads(row['aliases']) if row['aliases'] else []
                    
                    contacts.append({
                        'id': row['id'],
                        'display_name': row['display_name'],
                        'displayName': row['display_name'],   # Formato nuevo
                        'aliases': ','.join(aliases_list),    # String para compatibilidad
                        'platform': row['platform'],
                        'details': row['details'],
                        'contact_details': row['details'],    # Alias para compatibilidad
                        'is_emergency': int(row['is_emergency']),  # Int para legacy
                        'isEmergency': bool(row['is_emergency']),  # Boolean para nuevo
                        'created_at': row['created_at']
                    })
                
                return contacts
                
        except Exception as e:
            logger.error(f"Error listando contactos: {e}")
            return []
    
    def add_contact(self, display_name: str, aliases: List[str], platform: str,
                   details: str, is_emergency: bool = False) -> bool:
        """Agrega un contacto."""
        try:
            with self.get_connection() as conn:
                cursor = conn.cursor()
                cursor.execute("""
                    INSERT INTO contacts (display_name, aliases, platform, details, is_emergency)
                    VALUES (?, ?, ?, ?, ?)
                """, (display_name, json.dumps(aliases), platform, details, is_emergency))
                conn.commit()
                
            logger.info(f"Contacto agregado: {display_name}")
            return True
            
        except Exception as e:
            logger.error(f"Error agregando contacto: {e}")
            return False
    
    def delete_contact(self, contact_id: int) -> bool:
        """Elimina un contacto (soft delete)."""
        try:
            with self.get_connection() as conn:
                cursor = conn.cursor()
                cursor.execute("""
                    UPDATE contacts 
                    SET is_active = FALSE, updated_at = CURRENT_TIMESTAMP
                    WHERE id = ?
                """, (contact_id,))
                conn.commit()
                
            logger.info(f"Contacto eliminado: {contact_id}")
            return True
            
        except Exception as e:
            logger.error(f"Error eliminando contacto: {e}")
            return False
    
    # === MÉTODOS DE CONFIGURACIÓN ===
    
    def get_setting(self, key: str, default_value: Any = None) -> Any:
        """Obtiene una configuración global."""
        try:
            with self.get_connection() as conn:
                cursor = conn.cursor()
                cursor.execute("SELECT value FROM settings WHERE key = ?", (key,))
                row = cursor.fetchone()
                
                if row:
                    return row['value']
                else:
                    return default_value
                    
        except Exception as e:
            logger.error(f"Error obteniendo configuración {key}: {e}")
            return default_value
    
    def set_setting(self, key: str, value: Any, category: str = 'general') -> bool:
        """Establece una configuración global."""
        try:
            with self.get_connection() as conn:
                cursor = conn.cursor()
                cursor.execute("""
                    INSERT OR REPLACE INTO settings (key, value, category, updated_at)
                    VALUES (?, ?, ?, CURRENT_TIMESTAMP)
                """, (key, str(value), category))
                conn.commit()
                
            logger.info(f"Configuración actualizada: {key} = {value}")
            return True
            
        except Exception as e:
            logger.error(f"Error estableciendo configuración {key}: {e}")
            return False
    
    def get_all_settings(self, category: str = None) -> Dict[str, str]:
        """Obtiene todas las configuraciones, opcionalmente filtradas por categoría."""
        try:
            with self.get_connection() as conn:
                cursor = conn.cursor()
                if category:
                    cursor.execute("SELECT key, value FROM settings WHERE category = ?", (category,))
                else:
                    cursor.execute("SELECT key, value FROM settings")
                
                return {row['key']: row['value'] for row in cursor.fetchall()}
                
        except Exception as e:
            logger.error(f"Error obteniendo configuraciones: {e}")
            return {}

# Instancia global del gestor de datos compartidos
shared_data_manager = SharedDataManager()