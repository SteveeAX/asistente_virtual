#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
UserManager - Gestión de usuarios multi-usuario para Asistente Kata

Este módulo maneja la creación, gestión y cambio entre usuarios,
garantizando el aislamiento completo de datos entre usuarios.

Autor: Asistente Kata
Fecha: 2024-08-18
Versión: 1.0.0
"""

import sqlite3
import os
import json
import logging
import shutil
from datetime import datetime
from typing import Dict, List, Optional, Any
from pathlib import Path

logger = logging.getLogger(__name__)

class UserManager:
    """
    Gestor principal de usuarios del sistema.
    Maneja el registro de usuarios, cambio de usuario activo,
    y acceso a bases de datos individuales.
    """
    
    def __init__(self, base_path: str = None):
        """
        Inicializa el gestor de usuarios.
        
        Args:
            base_path: Ruta base del proyecto. Si no se especifica, usa el directorio actual.
        """
        self.base_path = Path(base_path) if base_path else Path(__file__).parent.parent.parent
        self.data_path = self.base_path / "data"
        self.users_path = self.data_path / "users"
        self.system_path = self.data_path / "system"
        self.backups_path = self.data_path / "backups"
        
        # Crear directorios si no existen
        self._ensure_directories()
        
        # Inicializar BD del sistema
        self._init_system_database()
        
        # Cargar usuario actual
        self.current_user = self._get_current_user()
        
        logger.info(f"UserManager inicializado. Usuario actual: {self.current_user}")
    
    def _ensure_directories(self):
        """Asegura que todos los directorios necesarios existan."""
        for path in [self.users_path, self.system_path, self.backups_path]:
            path.mkdir(parents=True, exist_ok=True)
    
    def _init_system_database(self):
        """Inicializa la base de datos del sistema para registro de usuarios."""
        system_db_path = self.system_path / "users_registry.db"
        
        with sqlite3.connect(system_db_path) as conn:
            cursor = conn.cursor()
            
            # Tabla de usuarios registrados
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS users (
                    username VARCHAR(50) PRIMARY KEY,
                    display_name VARCHAR(100) NOT NULL,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    last_login TIMESTAMP,
                    is_active BOOLEAN DEFAULT TRUE,
                    data_directory VARCHAR(200) NOT NULL,
                    backup_enabled BOOLEAN DEFAULT TRUE
                )
            """)
            
            # Tabla de configuración del sistema
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS system_settings (
                    key VARCHAR(50) PRIMARY KEY,
                    value TEXT NOT NULL,
                    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            """)
            
            # Configuración inicial si no existe
            cursor.execute("SELECT COUNT(*) FROM system_settings WHERE key = 'current_user'")
            if cursor.fetchone()[0] == 0:
                cursor.execute("""
                    INSERT INTO system_settings (key, value) VALUES 
                    ('current_user', 'francisca'),
                    ('auto_backup_days', '7'),
                    ('max_users', '10')
                """)
            
            conn.commit()
        
        logger.info("Base de datos del sistema inicializada correctamente")
    
    def _get_current_user(self) -> str:
        """Obtiene el usuario actualmente activo del sistema."""
        system_db_path = self.system_path / "users_registry.db"
        
        try:
            with sqlite3.connect(system_db_path) as conn:
                cursor = conn.cursor()
                cursor.execute("SELECT value FROM system_settings WHERE key = 'current_user'")
                result = cursor.fetchone()
                return result[0] if result else 'francisca'
        except Exception as e:
            logger.error(f"Error obteniendo usuario actual: {e}")
            return 'francisca'  # Usuario por defecto
    
    def _set_current_user(self, username: str):
        """Establece el usuario activo del sistema."""
        system_db_path = self.system_path / "users_registry.db"
        
        with sqlite3.connect(system_db_path) as conn:
            cursor = conn.cursor()
            cursor.execute("""
                UPDATE system_settings 
                SET value = ?, updated_at = CURRENT_TIMESTAMP 
                WHERE key = 'current_user'
            """, (username,))
            conn.commit()
        
        # Actualizar también en memoria
        self.current_user = username
        logger.info(f"Usuario actual cambiado a: {username}")
    
    def get_user_database_path(self, username: str = None) -> Path:
        """
        Obtiene la ruta a la base de datos del usuario especificado.
        
        Args:
            username: Nombre del usuario. Si no se especifica, usa el usuario actual.
            
        Returns:
            Path: Ruta al archivo de base de datos del usuario.
        """
        user = username or self.current_user
        return self.users_path / user / "user_data.db"
    
    def get_user_directory(self, username: str = None) -> Path:
        """
        Obtiene la ruta al directorio del usuario especificado.
        
        Args:
            username: Nombre del usuario. Si no se especifica, usa el usuario actual.
            
        Returns:
            Path: Ruta al directorio del usuario.
        """
        user = username or self.current_user
        return self.users_path / user
    
    def delete_user(self, username: str) -> bool:
        """
        Elimina un usuario del sistema.
        
        Args:
            username: Nombre del usuario a eliminar
            
        Returns:
            bool: True si la eliminación fue exitosa, False en caso contrario
        """
        try:
            if not self.user_exists(username):
                logger.error(f"No se puede eliminar usuario inexistente: {username}")
                return False
            
            # No permitir eliminar el usuario actual
            if username == self.current_user:
                logger.error(f"No se puede eliminar el usuario actualmente activo: {username}")
                return False
            
            # Eliminar del registro del sistema
            system_db_path = self.system_path / "users_registry.db"
            with sqlite3.connect(system_db_path) as conn:
                cursor = conn.cursor()
                cursor.execute("DELETE FROM users WHERE username = ?", (username,))
                conn.commit()
            
            # Eliminar directorio de datos del usuario
            user_dir = self.get_user_directory(username)
            if user_dir.exists():
                shutil.rmtree(user_dir)
            
            logger.info(f"Usuario eliminado exitosamente: {username}")
            return True
            
        except Exception as e:
            logger.error(f"Error eliminando usuario {username}: {e}")
            return False
    
    def backup_user_data(self, username: str) -> bool:
        """
        Crea un backup de los datos del usuario.
        
        Args:
            username: Nombre del usuario a respaldar
            
        Returns:
            bool: True si el backup fue exitoso, False en caso contrario
        """
        try:
            if not self.user_exists(username):
                logger.error(f"No se puede hacer backup de usuario inexistente: {username}")
                return False
            
            # Crear directorio de backup
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            backup_dir = self.backups_path / f"user_{username}_{timestamp}"
            backup_dir.mkdir(parents=True, exist_ok=True)
            
            # Copiar datos del usuario
            user_dir = self.get_user_directory(username)
            if user_dir.exists():
                backup_user_dir = backup_dir / "user_data"
                shutil.copytree(user_dir, backup_user_dir)
            
            # Guardar información del usuario desde el registro
            users_list = self.get_users_list()
            user_info = next((u for u in users_list if u['username'] == username), None)
            
            if user_info:
                backup_info = backup_dir / "user_info.json"
                with open(backup_info, 'w', encoding='utf-8') as f:
                    json.dump(user_info, f, indent=2, ensure_ascii=False)
            
            logger.info(f"Backup creado exitosamente para {username}: {backup_dir}")
            return True
            
        except Exception as e:
            logger.error(f"Error creando backup para {username}: {e}")
            return False
    
    def user_exists(self, username: str) -> bool:
        """
        Verifica si un usuario existe en el sistema.
        
        Args:
            username: Nombre del usuario a verificar.
            
        Returns:
            bool: True si el usuario existe, False en caso contrario.
        """
        system_db_path = self.system_path / "users_registry.db"
        
        try:
            with sqlite3.connect(system_db_path) as conn:
                cursor = conn.cursor()
                cursor.execute("SELECT COUNT(*) FROM users WHERE username = ? AND is_active = TRUE", (username,))
                return cursor.fetchone()[0] > 0
        except Exception as e:
            logger.error(f"Error verificando existencia del usuario {username}: {e}")
            return False
    
    def create_user(self, username: str, display_name: str) -> bool:
        """
        Crea un nuevo usuario en el sistema.
        
        Args:
            username: Nombre único del usuario (alfanumérico, guiones bajos permitidos).
            display_name: Nombre completo para mostrar.
            
        Returns:
            bool: True si el usuario se creó exitosamente, False en caso contrario.
        """
        try:
            # Validar nombre de usuario
            if not username.replace('_', '').isalnum():
                logger.error(f"Nombre de usuario inválido: {username}")
                return False
            
            # Verificar que no exista
            if self.user_exists(username):
                logger.error(f"El usuario {username} ya existe")
                return False
            
            # Crear directorio del usuario
            user_dir = self.get_user_directory(username)
            user_dir.mkdir(parents=True, exist_ok=True)
            
            # Crear subdirectorios
            (user_dir / "uploads").mkdir(exist_ok=True)
            
            # Crear base de datos del usuario
            self._create_user_database(username)
            
            # Registrar usuario en el sistema
            system_db_path = self.system_path / "users_registry.db"
            with sqlite3.connect(system_db_path) as conn:
                cursor = conn.cursor()
                cursor.execute("""
                    INSERT INTO users (username, display_name, data_directory, created_at)
                    VALUES (?, ?, ?, CURRENT_TIMESTAMP)
                """, (username, display_name, str(user_dir)))
                conn.commit()
            
            # Inicializar preferencias por defecto
            self._initialize_user_preferences(username)
            
            logger.info(f"Usuario {username} creado exitosamente")
            return True
            
        except Exception as e:
            logger.error(f"Error creando usuario {username}: {e}")
            return False
    
    def _create_user_database(self, username: str):
        """Crea la base de datos individual del usuario."""
        db_path = self.get_user_database_path(username)
        
        with sqlite3.connect(db_path) as conn:
            cursor = conn.cursor()
            
            # Tabla de preferencias
            cursor.execute("""
                CREATE TABLE preferences (
                    category VARCHAR(50) PRIMARY KEY,
                    data TEXT NOT NULL,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            """)
            
            # Tabla de recordatorios
            cursor.execute("""
                CREATE TABLE reminders (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    type VARCHAR(20) NOT NULL,
                    name VARCHAR(200) NOT NULL,
                    quantity VARCHAR(100),
                    prescription TEXT,
                    times TEXT NOT NULL,
                    days TEXT NOT NULL,
                    photo_path VARCHAR(500),
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    is_active BOOLEAN DEFAULT TRUE
                )
            """)
            
            # Tabla de contactos
            cursor.execute("""
                CREATE TABLE contacts (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    display_name VARCHAR(100) NOT NULL,
                    aliases TEXT NOT NULL,
                    platform VARCHAR(20) DEFAULT 'telegram',
                    details VARCHAR(200) NOT NULL,
                    is_emergency BOOLEAN DEFAULT FALSE,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    is_active BOOLEAN DEFAULT TRUE
                )
            """)
            
            # Tabla de logs de interacciones
            cursor.execute("""
                CREATE TABLE interaction_logs (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    interaction_type VARCHAR(50) NOT NULL,
                    details TEXT,
                    success BOOLEAN DEFAULT TRUE
                )
            """)
            
            # Índices para mejorar rendimiento
            cursor.execute("CREATE INDEX idx_reminders_active ON reminders (is_active)")
            cursor.execute("CREATE INDEX idx_contacts_emergency ON contacts (is_emergency, is_active)")
            cursor.execute("CREATE INDEX idx_logs_type_time ON interaction_logs (interaction_type, timestamp)")
            
            conn.commit()
        
        logger.info(f"Base de datos creada para usuario: {username}")
    
    def _load_default_preferences(self) -> Dict[str, Any]:
        """Carga las configuraciones por defecto desde el archivo de configuración."""
        try:
            default_file = Path(__file__).parent / "default_preferences.json"
            if default_file.exists():
                with open(default_file, 'r', encoding='utf-8') as f:
                    config = json.load(f)
                    return config.get('default_preferences', {})
            else:
                logger.warning(f"Archivo de configuración por defecto no encontrado: {default_file}")
                return self._get_fallback_defaults()
        except Exception as e:
            logger.error(f"Error cargando configuraciones por defecto: {e}")
            return self._get_fallback_defaults()
    
    def _get_fallback_defaults(self) -> Dict[str, Any]:
        """Configuraciones mínimas de fallback si no se puede cargar el archivo."""
        return {
            'ia_generativa': {
                'habilitada': True,
                'confianza_minima_clasica': 0.85,
                'temperatura': 0.3,
                'max_tokens_respuesta': 150
            },
            'asistente': {
                'personalidad': 'amigable_profesional',
                'usar_emojis': False,
                'respuestas_cortas': True
            },
            'comandos_clasicos': {
                'siempre_preferir': ['recordatorio', 'medicacion', 'contacto_emergencia', 'fecha', 'hora', 'enchufe'],
                'nunca_derivar_ia': ['emergencia', 'medicacion_critica', 'sistema_apagar']
            }
        }
    
    def _initialize_user_preferences(self, username: str):
        """Inicializa solo las preferencias personales para un nuevo usuario."""
        db_path = self.get_user_database_path(username)
        
        # Solo preferencias personales (las técnicas vienen del archivo de configuración)
        personal_preferences = {
            'usuario': {
                'nombre': username.title(),
                'edad': 25,
                'ciudad': '',
                'timezone': 'America/Guayaquil',
                'idioma_preferido': 'es',
                'modo_verbose': False
            },
            'contexto_cultural': {
                'pais': '',
                'region': '',
                'tradiciones_conoce': []
            },
            'mascotas': {
                'tiene_mascotas': False,
                'tipo': '',
                'nombres': []
            },
            'intereses': {
                'hobbies_principales': [],
                'musica_preferida': [],
                'comidas_favoritas': [],
                'actividades_sociales': [],
                'entretenimiento': [],
                'plantas_conoce': []
            },
            'religion': {
                'practica': False,
                'tipo': ''
            },
            'ejemplos_personalizacion': {
                'frases_cercanas': [],
                'cuando_hablar_comida': {
                    'contexto': '',
                    'incluir': []
                },
                'cuando_hablar_entretenimiento': {
                    'contexto': '',
                    'incluir': []
                },
                'cuando_hablar_mascotas': {
                    'contexto': '',
                    'incluir': []
                },
                'cuando_hablar_plantas': {
                    'contexto': '',
                    'incluir': []
                }
            }
        }
        
        try:
            with sqlite3.connect(db_path) as conn:
                cursor = conn.cursor()
                
                for category, data in personal_preferences.items():
                    cursor.execute("""
                        INSERT INTO preferences (category, data, created_at, updated_at)
                        VALUES (?, ?, CURRENT_TIMESTAMP, CURRENT_TIMESTAMP)
                    """, (category, json.dumps(data, ensure_ascii=False)))
                
                conn.commit()
            
            logger.info(f"Preferencias personales inicializadas para: {username} (6 categorías)")
            
        except Exception as e:
            logger.error(f"Error inicializando preferencias para {username}: {e}")
    
    def get_user_preferences(self, username: str = None) -> Dict[str, Any]:
        """
        Obtiene las preferencias completas del usuario (personales + configuraciones por defecto).
        
        Args:
            username: Nombre del usuario. Si no se especifica, usa el usuario actual.
            
        Returns:
            Dict: Preferencias completas del usuario (personales + técnicas).
        """
        if username is None:
            username = self.current_user
        
        if not username:
            logger.error("No hay usuario actual establecido")
            return self._load_default_preferences()
        
        # Cargar configuraciones por defecto (técnicas)
        default_preferences = self._load_default_preferences()
        
        # Cargar preferencias personales del usuario
        user_preferences = self._get_user_personal_preferences(username)
        
        # Combinar: personales sobrescriben a las por defecto
        combined_preferences = default_preferences.copy()
        combined_preferences.update(user_preferences)
        
        return combined_preferences
    
    def _get_user_personal_preferences(self, username: str) -> Dict[str, Any]:
        """Obtiene solo las preferencias personales del usuario desde su BD."""
        db_path = self.get_user_database_path(username)
        
        try:
            with sqlite3.connect(db_path) as conn:
                cursor = conn.cursor()
                cursor.execute("""
                    SELECT category, data 
                    FROM preferences 
                    ORDER BY category
                """)
                
                preferences = {}
                for row in cursor.fetchall():
                    category = row[0]
                    data = json.loads(row[1])
                    preferences[category] = data
                
                return preferences
                
        except Exception as e:
            logger.error(f"Error obteniendo preferencias personales de {username}: {e}")
            return {}
    
    def get_users_list(self) -> List[Dict[str, Any]]:
        """
        Obtiene la lista de todos los usuarios registrados.
        
        Returns:
            List[Dict]: Lista de usuarios con su información.
        """
        system_db_path = self.system_path / "users_registry.db"
        
        try:
            with sqlite3.connect(system_db_path) as conn:
                cursor = conn.cursor()
                cursor.execute("""
                    SELECT username, display_name, created_at, last_login, is_active 
                    FROM users 
                    ORDER BY created_at DESC
                """)
                
                users = []
                for row in cursor.fetchall():
                    users.append({
                        'username': row[0],
                        'display_name': row[1],
                        'created_at': row[2],
                        'last_login': row[3],
                        'is_active': bool(row[4])
                    })
                
                return users
                
        except Exception as e:
            logger.error(f"Error obteniendo lista de usuarios: {e}")
            return []
    
    def switch_user(self, username: str) -> bool:
        """
        Cambia el usuario activo del sistema.
        
        Args:
            username: Nombre del usuario al que cambiar.
            
        Returns:
            bool: True si el cambio fue exitoso, False en caso contrario.
        """
        try:
            if not self.user_exists(username):
                logger.error(f"No se puede cambiar a usuario inexistente: {username}")
                return False
            
            # Actualizar último login
            system_db_path = self.system_path / "users_registry.db"
            with sqlite3.connect(system_db_path) as conn:
                cursor = conn.cursor()
                cursor.execute("""
                    UPDATE users 
                    SET last_login = CURRENT_TIMESTAMP 
                    WHERE username = ?
                """, (username,))
                conn.commit()
            
            # Cambiar usuario activo
            self._set_current_user(username)
            
            logger.info(f"Usuario cambiado exitosamente a: {username}")
            return True
            
        except Exception as e:
            logger.error(f"Error cambiando a usuario {username}: {e}")
            return False
    
    def get_user_database_connection(self, username: str = None) -> sqlite3.Connection:
        """
        Obtiene una conexión a la base de datos del usuario.
        
        Args:
            username: Nombre del usuario. Si no se especifica, usa el usuario actual.
            
        Returns:
            sqlite3.Connection: Conexión a la base de datos del usuario.
        """
        db_path = self.get_user_database_path(username)
        return sqlite3.connect(db_path)
    
    def backup_user_data(self, username: str = None) -> bool:
        """
        Crea un backup de los datos del usuario.
        
        Args:
            username: Nombre del usuario. Si no se especifica, usa el usuario actual.
            
        Returns:
            bool: True si el backup fue exitoso, False en caso contrario.
        """
        try:
            user = username or self.current_user
            user_dir = self.get_user_directory(user)
            
            if not user_dir.exists():
                logger.error(f"Directorio del usuario {user} no existe")
                return False
            
            # Crear nombre del backup
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            backup_name = f"{user}_{timestamp}.zip"
            backup_path = self.backups_path / backup_name
            
            # Crear backup (usando shutil para comprimir)
            shutil.make_archive(str(backup_path.with_suffix('')), 'zip', str(user_dir))
            
            logger.info(f"Backup creado: {backup_path}")
            return True
            
        except Exception as e:
            logger.error(f"Error creando backup para {username}: {e}")
            return False


# Instancia global del gestor de usuarios
user_manager = UserManager()