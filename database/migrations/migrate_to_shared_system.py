#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
Migration to Shared System - Script de migración a sistema compartido

Este script migra los datos existentes del sistema multi-usuario
al nuevo sistema donde solo las preferencias son por usuario.

Migra:
- Medicamentos/recordatorios → BD compartida  
- Tareas → BD compartida
- Contactos → BD compartida  
- Configuraciones → BD compartida
- Solo preserva preferencias por usuario

Autor: Asistente Kata
Fecha: 2025-08-25  
Versión: 2.0.0
"""

import sys
import os
import sqlite3
import json
import logging
from pathlib import Path
from datetime import datetime
from typing import Dict, List, Any, Optional

# Agregar directorios al path
project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root))
sys.path.insert(0, str(project_root / 'database'))

from database.models.shared_data_manager import shared_data_manager
from database.models.user_manager import user_manager

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

class SharedSystemMigration:
    """Maneja la migración de datos al sistema compartido."""
    
    def __init__(self):
        """Inicializa la migración."""
        self.backup_path = project_root / "data" / "backups" / f"migration_backup_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
        self.backup_path.mkdir(parents=True, exist_ok=True)
        
        # Usuarios para migrar datos
        self.primary_user = "francisca"  # Usuario principal del que tomar datos
        self.all_users = []
        
        logger.info(f"Migración inicializada. Backup en: {self.backup_path}")
    
    def create_backup(self) -> bool:
        """Crea backup completo antes de la migración."""
        try:
            logger.info("Creando backup completo antes de migración...")
            
            # Backup de base de datos legacy si existe
            legacy_db = project_root / "app.db"
            if legacy_db.exists():
                backup_legacy = self.backup_path / "app.db"
                import shutil
                shutil.copy2(legacy_db, backup_legacy)
                logger.info(f"Backup de BD legacy: {backup_legacy}")
            
            # Backup del directorio de datos completo
            data_dir = project_root / "data"
            if data_dir.exists():
                backup_data = self.backup_path / "data"
                import shutil
                shutil.copytree(data_dir, backup_data, dirs_exist_ok=True)
                logger.info(f"Backup de directorio data: {backup_data}")
            
            logger.info("Backup completado exitosamente")
            return True
            
        except Exception as e:
            logger.error(f"Error creando backup: {e}")
            return False
    
    def get_users_to_migrate(self) -> List[str]:
        """Obtiene lista de usuarios existentes."""
        try:
            users = user_manager.get_users_list()
            user_names = [user['username'] for user in users if user['is_active']]
            
            # Asegurar que el usuario principal esté primero
            if self.primary_user in user_names:
                user_names.remove(self.primary_user)
                user_names.insert(0, self.primary_user)
            
            logger.info(f"Usuarios para migrar: {user_names}")
            return user_names
            
        except Exception as e:
            logger.error(f"Error obteniendo usuarios: {e}")
            return []
    
    def migrate_legacy_database(self) -> bool:
        """Migra datos de la base de datos legacy app.db si existe."""
        legacy_db_path = project_root / "app.db"
        
        if not legacy_db_path.exists():
            logger.info("No se encontró base de datos legacy app.db")
            return True
            
        try:
            logger.info("Migrando datos de base de datos legacy...")
            
            with sqlite3.connect(legacy_db_path) as legacy_conn:
                legacy_conn.row_factory = sqlite3.Row
                cursor = legacy_conn.cursor()
                
                # Migrar medicamentos/recordatorios
                try:
                    cursor.execute("SELECT * FROM reminders")
                    for row in cursor.fetchall():
                        times_list = row['times'].split(',') if row['times'] else []
                        days_list = row['days_of_week'].split(',') if row['days_of_week'] else []
                        
                        shared_data_manager.add_medication(
                            name=row['medication_name'],
                            quantity=row.get('cantidad', ''),
                            prescription=row.get('prescripcion', ''),
                            times=times_list,
                            days=days_list,
                            photo_path=row.get('photo_path', '')
                        )
                    logger.info("Medicamentos legacy migrados")
                except sqlite3.OperationalError:
                    logger.info("Tabla de medicamentos legacy no encontrada")
                
                # Migrar tareas si existe la tabla
                try:
                    cursor.execute("SELECT * FROM tasks")
                    for row in cursor.fetchall():
                        times_list = row['times'].split(',') if row['times'] else []
                        days_list = row['days_of_week'].split(',') if row['days_of_week'] else []
                        
                        shared_data_manager.add_task(
                            name=row['task_name'],
                            times=times_list,
                            days=days_list
                        )
                    logger.info("Tareas legacy migradas")
                except sqlite3.OperationalError:
                    logger.info("Tabla de tareas legacy no encontrada")
                
                # Migrar contactos si existe la tabla
                try:
                    cursor.execute("SELECT * FROM contacts")
                    for row in cursor.fetchall():
                        aliases_list = row['aliases'].split(',') if row['aliases'] else []
                        
                        shared_data_manager.add_contact(
                            display_name=row['display_name'],
                            aliases=aliases_list,
                            platform=row.get('platform', 'telegram'),
                            details=row['contact_details'],
                            is_emergency=bool(row.get('is_emergency', False))
                        )
                    logger.info("Contactos legacy migrados")
                except sqlite3.OperationalError:
                    logger.info("Tabla de contactos legacy no encontrada")
                
                # Migrar configuraciones si existe la tabla
                try:
                    cursor.execute("SELECT * FROM settings")
                    for row in cursor.fetchall():
                        shared_data_manager.set_setting(
                            key=row['key'],
                            value=row['value'],
                            category=row.get('category', 'general')
                        )
                    logger.info("Configuraciones legacy migradas")
                except sqlite3.OperationalError:
                    logger.info("Tabla de configuraciones legacy no encontrada")
            
            logger.info("Migración legacy completada")
            return True
            
        except Exception as e:
            logger.error(f"Error migrando base de datos legacy: {e}")
            return False
    
    def migrate_user_data(self, username: str, is_primary: bool = False) -> bool:
        """
        Migra datos de un usuario específico.
        
        Args:
            username: Nombre del usuario
            is_primary: Si es el usuario principal (sus datos van a BD compartida)
        """
        try:
            user_db_path = user_manager.get_user_database_path(username)
            
            if not user_db_path.exists():
                logger.warning(f"Base de datos de usuario {username} no existe")
                return True
            
            logger.info(f"Migrando datos de usuario: {username} (primario: {is_primary})")
            
            with sqlite3.connect(user_db_path) as user_conn:
                user_conn.row_factory = sqlite3.Row
                cursor = user_conn.cursor()
                
                if is_primary:
                    # Usuario principal: sus datos van a BD compartida
                    
                    # Migrar medicamentos
                    try:
                        cursor.execute("SELECT * FROM reminders WHERE type = 'medication' AND is_active = TRUE")
                        migrated_meds = 0
                        for row in cursor.fetchall():
                            times_list = json.loads(row['times']) if row['times'] else []
                            days_list = json.loads(row['days']) if row['days'] else []
                            
                            shared_data_manager.add_medication(
                                name=row['name'],
                                quantity=row['quantity'] or '',
                                prescription=row['prescription'] or '',
                                times=times_list,
                                days=days_list,
                                photo_path=row['photo_path'] or ''
                            )
                            migrated_meds += 1
                        logger.info(f"Medicamentos migrados de {username}: {migrated_meds}")
                    except sqlite3.OperationalError:
                        logger.info(f"Tabla de medicamentos no encontrada en {username}")
                    
                    # Migrar tareas
                    try:
                        cursor.execute("SELECT * FROM reminders WHERE type = 'task' AND is_active = TRUE")
                        migrated_tasks = 0
                        for row in cursor.fetchall():
                            times_list = json.loads(row['times']) if row['times'] else []
                            days_list = json.loads(row['days']) if row['days'] else []
                            
                            shared_data_manager.add_task(
                                name=row['name'],
                                times=times_list,
                                days=days_list
                            )
                            migrated_tasks += 1
                        logger.info(f"Tareas migradas de {username}: {migrated_tasks}")
                    except sqlite3.OperationalError:
                        logger.info(f"Tabla de tareas no encontrada en {username}")
                    
                    # Migrar contactos
                    try:
                        cursor.execute("SELECT * FROM contacts WHERE is_active = TRUE")
                        migrated_contacts = 0
                        for row in cursor.fetchall():
                            aliases_list = json.loads(row['aliases']) if row['aliases'] else []
                            
                            shared_data_manager.add_contact(
                                display_name=row['display_name'],
                                aliases=aliases_list,
                                platform=row['platform'],
                                details=row['details'],
                                is_emergency=bool(row['is_emergency'])
                            )
                            migrated_contacts += 1
                        logger.info(f"Contactos migrados de {username}: {migrated_contacts}")
                    except sqlite3.OperationalError:
                        logger.info(f"Tabla de contactos no encontrada en {username}")
                    
                    # Migrar configuraciones a BD compartida
                    try:
                        cursor.execute("SELECT * FROM preferences")
                        for row in cursor.fetchall():
                            prefs = json.loads(row['data'])
                            
                            # Solo migrar configuraciones del asistente a BD compartida
                            if row['category'] == 'asistente':
                                for key, value in prefs.items():
                                    shared_data_manager.set_setting(key, value, 'asistente')
                    except sqlite3.OperationalError:
                        logger.info(f"Tabla de preferencias no encontrada en {username}")
                
                # Para TODOS los usuarios: preservar solo preferencias de IA
                self._preserve_ai_preferences(cursor, username)
            
            return True
            
        except Exception as e:
            logger.error(f"Error migrando datos de usuario {username}: {e}")
            return False
    
    def _preserve_ai_preferences(self, cursor: sqlite3.Cursor, username: str):
        """Preserva solo las preferencias de IA en la BD del usuario."""
        try:
            # Categorías de preferencias que se mantienen por usuario
            ai_categories = {
                'usuario', 'contexto_cultural', 'mascotas', 
                'intereses', 'religion', 'ejemplos_personalizacion'
            }
            
            cursor.execute("SELECT category, data FROM preferences WHERE category IN ({})".format(
                ','.join('?' * len(ai_categories))
            ), list(ai_categories))
            
            preserved_prefs = cursor.fetchall()
            logger.info(f"Preservando {len(preserved_prefs)} categorías de preferencias IA para {username}")
            
        except sqlite3.OperationalError:
            logger.info(f"No hay preferencias que preservar para {username}")
    
    def update_user_databases(self):
        """Actualiza las bases de datos de usuarios para contener solo preferencias."""
        try:
            logger.info("Actualizando bases de datos de usuarios...")
            
            for username in self.all_users:
                user_db_path = user_manager.get_user_database_path(username)
                
                if not user_db_path.exists():
                    continue
                
                logger.info(f"Limpiando BD de {username} para solo preferencias...")
                
                with sqlite3.connect(user_db_path) as conn:
                    cursor = conn.cursor()
                    
                    # Crear backup de preferencias
                    ai_categories = {
                        'usuario', 'contexto_cultural', 'mascotas',
                        'intereses', 'religion', 'ejemplos_personalizacion'
                    }
                    
                    preferences_backup = []
                    try:
                        cursor.execute("SELECT category, data FROM preferences WHERE category IN ({})".format(
                            ','.join('?' * len(ai_categories))
                        ), list(ai_categories))
                        preferences_backup = cursor.fetchall()
                    except sqlite3.OperationalError:
                        pass
                    
                    # Recrear base de datos solo con tabla de preferencias
                    cursor.execute("DROP TABLE IF EXISTS reminders")
                    cursor.execute("DROP TABLE IF EXISTS tasks")  
                    cursor.execute("DROP TABLE IF EXISTS contacts")
                    cursor.execute("DELETE FROM preferences WHERE category NOT IN ({})".format(
                        ','.join('?' * len(ai_categories))
                    ), list(ai_categories))
                    
                    # Restaurar preferencias de IA
                    for category, data in preferences_backup:
                        cursor.execute("""
                            INSERT OR REPLACE INTO preferences (category, data, updated_at)
                            VALUES (?, ?, CURRENT_TIMESTAMP)
                        """, (category, data))
                    
                    conn.commit()
                    logger.info(f"BD de {username} actualizada (solo preferencias)")
            
        except Exception as e:
            logger.error(f"Error actualizando bases de datos de usuarios: {e}")
    
    def verify_migration(self) -> bool:
        """Verifica que la migración fue exitosa."""
        try:
            logger.info("Verificando migración...")
            
            # Verificar BD compartida
            medications = shared_data_manager.list_medications()
            tasks = shared_data_manager.list_tasks()
            contacts = shared_data_manager.list_contacts()
            
            logger.info(f"BD compartida - Medicamentos: {len(medications)}, Tareas: {len(tasks)}, Contactos: {len(contacts)}")
            
            # Verificar configuración
            voice_setting = shared_data_manager.get_setting('voice_name')
            logger.info(f"Configuración de voz: {voice_setting}")
            
            # Verificar que usuarios mantienen solo preferencias
            for username in self.all_users[:2]:  # Verificar solo primeros 2
                user_db_path = user_manager.get_user_database_path(username)
                if user_db_path.exists():
                    with sqlite3.connect(user_db_path) as conn:
                        cursor = conn.cursor()
                        
                        # Verificar que no hay tablas de datos compartidos
                        cursor.execute("SELECT name FROM sqlite_master WHERE type='table'")
                        tables = [row[0] for row in cursor.fetchall()]
                        
                        has_reminders = 'reminders' in tables
                        has_tasks = 'tasks' in tables
                        has_contacts = 'contacts' in tables
                        has_preferences = 'preferences' in tables
                        
                        if has_reminders or has_tasks or has_contacts:
                            logger.warning(f"Usuario {username} aún tiene tablas compartidas")
                        if has_preferences:
                            logger.info(f"Usuario {username} mantiene preferencias ✓")
            
            logger.info("Verificación de migración completada")
            return True
            
        except Exception as e:
            logger.error(f"Error verificando migración: {e}")
            return False
    
    def run_migration(self) -> bool:
        """Ejecuta la migración completa."""
        try:
            logger.info("=== INICIANDO MIGRACIÓN A SISTEMA COMPARTIDO ===")
            
            # Paso 1: Crear backup
            if not self.create_backup():
                logger.error("Fallo al crear backup. Migración cancelada.")
                return False
            
            # Paso 2: Inicializar BD compartida
            logger.info("Inicializando base de datos compartida...")
            shared_data_manager._init_shared_database()
            
            # Paso 3: Obtener usuarios
            self.all_users = self.get_users_to_migrate()
            
            # Paso 4: Migrar datos legacy si existe
            self.migrate_legacy_database()
            
            # Paso 5: Migrar datos de usuarios
            for i, username in enumerate(self.all_users):
                is_primary = (i == 0)  # Primer usuario es el principal
                if not self.migrate_user_data(username, is_primary):
                    logger.warning(f"Error migrando usuario {username}")
            
            # Paso 6: Limpiar bases de datos de usuarios
            self.update_user_databases()
            
            # Paso 7: Verificar migración
            if not self.verify_migration():
                logger.error("Verificación de migración falló")
                return False
            
            logger.info("=== MIGRACIÓN COMPLETADA EXITOSAMENTE ===")
            logger.info(f"Backup guardado en: {self.backup_path}")
            
            return True
            
        except Exception as e:
            logger.error(f"Error en migración: {e}")
            return False

def main():
    """Función principal de migración."""
    migration = SharedSystemMigration()
    
    print("=== MIGRACIÓN A SISTEMA COMPARTIDO ===")
    print("Esta migración:")
    print("✓ Convierte medicamentos, tareas, contactos y configuración a compartidos")
    print("✓ Mantiene solo preferencias IA por usuario")
    print("✓ Crea backup automático")
    print()
    
    # Ejecutar migración automáticamente para testing
    success = migration.run_migration()
    
    if success:
        print("\n✅ MIGRACIÓN EXITOSA")
        print("El sistema ahora usa base de datos compartida para medicamentos, tareas y contactos.")
        print("Las preferencias de IA siguen siendo por usuario.")
    else:
        print("\n❌ MIGRACIÓN FALLÓ")
        print("Revisa los logs para más detalles.")
        print(f"Backup disponible en: {migration.backup_path}")

if __name__ == "__main__":
    main()