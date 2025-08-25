#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
User API - Endpoints para gestión de usuarios y preferencias

SISTEMA HÍBRIDO v2.0:
- Gestión de usuarios (crear, cambiar, etc.) → Sigue igual
- Preferencias de IA → Por usuario (personalización)
- Medicamentos, tareas, contactos, configuración → Ahora compartidos (ver web_server.py)

Autor: Asistente Kata
Fecha: 2025-08-25
Versión: 2.0.0 - Sistema híbrido compartido
"""

import logging
import json
from flask import Blueprint, request, jsonify, g
from datetime import datetime
from typing import Dict, Any, List

import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(__file__)))

from database.models.user_manager import user_manager
from database.models.user_context import (
    require_user_context, 
    get_current_user, 
    get_user_db,
    switch_user_context,
    get_user_preferences,
    set_user_preferences
)

logger = logging.getLogger(__name__)

# Crear Blueprint para las rutas de usuarios
user_api = Blueprint('user_api', __name__, url_prefix='/api')

# === ENDPOINTS DE GESTIÓN DE USUARIOS ===

@user_api.route('/users', methods=['GET'])
@require_user_context
def list_users():
    """
    Lista todos los usuarios registrados en el sistema.
    
    Returns:
        JSON: Lista de usuarios con su información básica
    """
    try:
        users = user_manager.get_users_list()
        
        # Agregar información adicional
        for user in users:
            user['is_current'] = (user['username'] == get_current_user())
            
            # Contar datos del usuario
            try:
                db_path = user_manager.get_user_database_path(user['username'])
                if db_path.exists():
                    import sqlite3
                    with sqlite3.connect(db_path) as conn:
                        cursor = conn.cursor()
                        
                        cursor.execute("SELECT COUNT(*) FROM preferences")
                        user['preferences_count'] = cursor.fetchone()[0]
                        
                        cursor.execute("SELECT COUNT(*) FROM reminders")
                        user['reminders_count'] = cursor.fetchone()[0]
                        
                        cursor.execute("SELECT COUNT(*) FROM contacts")
                        user['contacts_count'] = cursor.fetchone()[0]
                else:
                    user['preferences_count'] = 0
                    user['reminders_count'] = 0
                    user['contacts_count'] = 0
                    
            except Exception as e:
                logger.warning(f"Error contando datos para usuario {user['username']}: {e}")
                user['preferences_count'] = 0
                user['reminders_count'] = 0
                user['contacts_count'] = 0
        
        return jsonify({
            "success": True,
            "users": users,
            "current_user": get_current_user(),
            "total_users": len(users)
        })
        
    except Exception as e:
        logger.error(f"Error listando usuarios: {e}")
        return jsonify({
            "success": False,
            "error": "Error obteniendo lista de usuarios",
            "message": str(e)
        }), 500

@user_api.route('/users/current', methods=['GET'])
@require_user_context
def get_current_user_info():
    """
    Obtiene información detallada del usuario actual.
    
    Returns:
        JSON: Información completa del usuario actual
    """
    try:
        current_user = get_current_user()
        
        # Obtener información básica del usuario
        users = user_manager.get_users_list()
        user_info = next((u for u in users if u['username'] == current_user), None)
        
        if not user_info:
            return jsonify({
                "success": False,
                "error": "Usuario actual no encontrado"
            }), 404
        
        # Obtener solo las preferencias editables del usuario
        all_preferences = get_user_preferences()
        
        # Filtrar solo las categorías editables
        editable_categories = {
            'usuario',
            'contexto_cultural', 
            'mascotas',
            'intereses',
            'religion',
            'ejemplos_personalizacion'
        }
        
        preferences = {
            category: data 
            for category, data in all_preferences.items() 
            if category in editable_categories
        }
        
        # Agregar información del directorio
        user_dir = user_manager.get_user_directory(current_user)
        
        result = {
            "success": True,
            "user": {
                "username": user_info['username'],
                "display_name": user_info['display_name'],
                "created_at": user_info['created_at'],
                "last_login": user_info['last_login'],
                "is_active": user_info['is_active'],
                "data_directory": str(user_dir),
                "database_path": str(user_manager.get_user_database_path(current_user))
            },
            "preferences": preferences,
            "stats": {
                "preferences_categories": len(preferences),
                "directory_exists": user_dir.exists()
            }
        }
        
        return jsonify(result)
        
    except Exception as e:
        logger.error(f"Error obteniendo información del usuario actual: {e}")
        return jsonify({
            "success": False,
            "error": "Error obteniendo información del usuario",
            "message": str(e)
        }), 500

@user_api.route('/users/current', methods=['PUT'])
@require_user_context
def update_current_user():
    """
    Actualiza información del usuario actual.
    
    Body JSON esperado:
    {
        "display_name": "Nuevo nombre",
        "preferences": {
            "categoria": { ... }
        }
    }
    
    Returns:
        JSON: Resultado de la actualización
    """
    try:
        data = request.get_json()
        if not data:
            return jsonify({
                "success": False,
                "error": "No se proporcionaron datos para actualizar"
            }), 400
        
        current_user = get_current_user()
        
        # Actualizar display_name si se proporciona
        if 'display_name' in data:
            system_db_path = user_manager.system_path / "users_registry.db"
            import sqlite3
            
            with sqlite3.connect(system_db_path) as conn:
                cursor = conn.cursor()
                cursor.execute("""
                    UPDATE users 
                    SET display_name = ?, updated_at = CURRENT_TIMESTAMP 
                    WHERE username = ?
                """, (data['display_name'], current_user))
                conn.commit()
            
            logger.info(f"Display name actualizado para {current_user}: {data['display_name']}")
        
        # Actualizar preferencias si se proporcionan
        if 'preferences' in data and isinstance(data['preferences'], dict):
            for category, prefs in data['preferences'].items():
                success = set_user_preferences(category, prefs)
                if not success:
                    logger.warning(f"Error actualizando preferencias de categoría: {category}")
        
        return jsonify({
            "success": True,
            "message": "Usuario actualizado correctamente",
            "updated_fields": list(data.keys())
        })
        
    except Exception as e:
        logger.error(f"Error actualizando usuario actual: {e}")
        return jsonify({
            "success": False,
            "error": "Error actualizando usuario",
            "message": str(e)
        }), 500

@user_api.route('/users/create', methods=['POST'])
@require_user_context
def create_new_user():
    """
    Crea un nuevo usuario en el sistema.
    
    Body JSON esperado:
    {
        "username": "nuevo_usuario",
        "display_name": "Nombre Completo"
    }
    
    Returns:
        JSON: Resultado de la creación
    """
    try:
        data = request.get_json()
        if not data:
            return jsonify({
                "success": False,
                "error": "No se proporcionaron datos para crear usuario"
            }), 400
        
        username = data.get('username', '').strip().lower()
        display_name = data.get('display_name', '').strip()
        
        # Validaciones
        if not username:
            return jsonify({
                "success": False,
                "error": "El nombre de usuario es requerido"
            }), 400
        
        if not display_name:
            return jsonify({
                "success": False,
                "error": "El nombre completo es requerido"
            }), 400
        
        # Validar formato de username
        if not username.replace('_', '').isalnum():
            return jsonify({
                "success": False,
                "error": "El nombre de usuario solo puede contener letras, números y guiones bajos"
            }), 400
        
        # Verificar que no existe
        if user_manager.user_exists(username):
            return jsonify({
                "success": False,
                "error": f"El usuario '{username}' ya existe"
            }), 409
        
        # Crear usuario
        success = user_manager.create_user(username, display_name)
        
        if success:
            logger.info(f"Usuario creado exitosamente: {username} ({display_name})")
            return jsonify({
                "success": True,
                "message": f"Usuario '{username}' creado exitosamente",
                "user": {
                    "username": username,
                    "display_name": display_name
                }
            })
        else:
            return jsonify({
                "success": False,
                "error": "Error creando usuario"
            }), 500
        
    except Exception as e:
        logger.error(f"Error creando usuario: {e}")
        return jsonify({
            "success": False,
            "error": "Error interno creando usuario",
            "message": str(e)
        }), 500

@user_api.route('/users/switch', methods=['POST'])
@require_user_context
def switch_active_user():
    """
    Cambia el usuario activo del sistema.
    
    Body JSON esperado:
    {
        "username": "usuario_destino"
    }
    
    Returns:
        JSON: Resultado del cambio
    """
    try:
        data = request.get_json()
        if not data:
            return jsonify({
                "success": False,
                "error": "No se proporcionó el usuario destino"
            }), 400
        
        target_user = data.get('username', '').strip()
        
        if not target_user:
            return jsonify({
                "success": False,
                "error": "El nombre de usuario es requerido"
            }), 400
        
        current_user = get_current_user()
        
        if target_user == current_user:
            return jsonify({
                "success": True,
                "message": f"Ya eres el usuario activo: {target_user}"
            })
        
        # Verificar que el usuario destino existe
        if not user_manager.user_exists(target_user):
            return jsonify({
                "success": False,
                "error": f"El usuario '{target_user}' no existe"
            }), 404
        
        # Realizar el cambio
        success = switch_user_context(target_user)
        
        if success:
            # Crear archivo de señal para notificar a la aplicación principal
            try:
                import os
                signal_file = os.path.join(os.path.dirname(__file__), '..', 'user_changed.flag')
                with open(signal_file, 'w') as f:
                    f.write(f"{current_user}→{target_user}")
                logger.info(f"Archivo de señal creado para cambio de usuario")
            except Exception as e:
                logger.warning(f"No se pudo crear archivo de señal: {e}")
            
            logger.info(f"Usuario cambiado exitosamente: {current_user} → {target_user}")
            return jsonify({
                "success": True,
                "message": f"Usuario cambiado de '{current_user}' a '{target_user}'",
                "previous_user": current_user,
                "current_user": target_user,
                "restart_required": False,  # Ahora se sincroniza automáticamente
                "signal_sent": True
            })
        else:
            return jsonify({
                "success": False,
                "error": "Error realizando el cambio de usuario"
            }), 500
        
    except Exception as e:
        logger.error(f"Error cambiando usuario: {e}")
        return jsonify({
            "success": False,
            "error": "Error interno cambiando usuario",
            "message": str(e)
        }), 500

@user_api.route('/users/<username>/delete', methods=['DELETE'])
@require_user_context  
def delete_user(username):
    """
    Elimina un usuario del sistema.
    
    Args:
        username: Nombre del usuario a eliminar
        
    Returns:
        JSON: Resultado de la eliminación
    """
    try:
        current_user = get_current_user()
        
        # Verificar que no se esté intentando eliminar el usuario actual
        if username == current_user:
            return jsonify({
                "success": False,
                "error": "No puedes eliminar el usuario actualmente activo"
            }), 400
        
        # Verificar que el usuario existe
        if not user_manager.user_exists(username):
            return jsonify({
                "success": False,
                "error": f"El usuario '{username}' no existe"
            }), 404
        
        # Crear backup antes de eliminar
        backup_success = user_manager.backup_user_data(username)
        
        # Eliminar usuario
        success = user_manager.delete_user(username)
        
        if success:
            logger.info(f"Usuario eliminado exitosamente: {username}")
            return jsonify({
                "success": True,
                "message": f"Usuario '{username}' eliminado exitosamente",
                "backup_created": backup_success
            })
        else:
            return jsonify({
                "success": False,
                "error": "Error eliminando el usuario"
            }), 500
        
    except Exception as e:
        logger.error(f"Error eliminando usuario {username}: {e}")
        return jsonify({
            "success": False,
            "error": "Error interno eliminando usuario",
            "message": str(e)
        }), 500

@user_api.route('/users/<username>/backup', methods=['POST'])
@require_user_context
def backup_user_data(username):
    """
    Crea un backup de los datos del usuario especificado.
    
    Args:
        username: Nombre del usuario a respaldar
        
    Returns:
        JSON: Resultado del backup
    """
    try:
        # Verificar que el usuario existe
        if not user_manager.user_exists(username):
            return jsonify({
                "success": False,
                "error": f"El usuario '{username}' no existe"
            }), 404
        
        # Solo permitir backup del usuario actual o ser admin (para futuras extensiones)
        current_user = get_current_user()
        if username != current_user:
            # Por ahora, solo permitir backup del usuario actual
            return jsonify({
                "success": False,
                "error": "Solo puedes respaldar tus propios datos"
            }), 403
        
        # Crear backup
        success = user_manager.backup_user_data(username)
        
        if success:
            # Obtener lista de backups para mostrar el más reciente
            backup_files = list(user_manager.backups_path.glob(f"{username}_*.zip"))
            latest_backup = max(backup_files, key=lambda f: f.stat().st_mtime) if backup_files else None
            
            result = {
                "success": True,
                "message": f"Backup creado para usuario '{username}'",
                "user": username
            }
            
            if latest_backup:
                result["backup_file"] = latest_backup.name
                result["backup_size"] = latest_backup.stat().st_size
                result["backup_created"] = datetime.fromtimestamp(latest_backup.stat().st_mtime).isoformat()
            
            return jsonify(result)
        else:
            return jsonify({
                "success": False,
                "error": "Error creando backup"
            }), 500
        
    except Exception as e:
        logger.error(f"Error creando backup para {username}: {e}")
        return jsonify({
            "success": False,
            "error": "Error interno creando backup",
            "message": str(e)
        }), 500

# === ENDPOINTS DE PREFERENCIAS POR USUARIO ===

@user_api.route('/preferences', methods=['GET'])
@require_user_context
def get_user_preferences_api():
    """
    Obtiene las preferencias editables del usuario actual.
    Solo muestra categorías que el usuario puede modificar desde la interfaz web.
    
    Returns:
        JSON: Categorías de preferencias editables del usuario
    """
    try:
        # Categorías que pueden ser editadas por el usuario
        editable_categories = {
            'usuario',
            'contexto_cultural', 
            'mascotas',
            'intereses',
            'religion',
            'ejemplos_personalizacion'
        }
        
        all_preferences = get_user_preferences()
        
        # Filtrar solo las categorías editables
        editable_preferences = {
            category: data 
            for category, data in all_preferences.items() 
            if category in editable_categories
        }
        
        return jsonify({
            "success": True,
            "user": get_current_user(),
            "preferences": editable_preferences,
            "editable_categories": list(editable_categories),
            "total_categories": len(all_preferences),
            "shown_categories": len(editable_preferences)
        })
        
    except Exception as e:
        logger.error(f"Error obteniendo preferencias: {e}")
        return jsonify({
            "success": False,
            "error": "Error obteniendo preferencias",
            "message": str(e)
        }), 500

@user_api.route('/preferences/<category>', methods=['GET'])
@require_user_context
def get_user_preference_category(category):
    """
    Obtiene una categoría específica de preferencias del usuario actual.
    Solo permite acceso a categorías editables.
    
    Args:
        category: Nombre de la categoría
        
    Returns:
        JSON: Preferencias de la categoría especificada
    """
    try:
        # Categorías que pueden ser leídas por el usuario
        editable_categories = {
            'usuario',
            'contexto_cultural', 
            'mascotas',
            'intereses',
            'religion',
            'ejemplos_personalizacion'
        }
        
        # Verificar si la categoría es accesible
        if category not in editable_categories:
            return jsonify({
                "success": False,
                "error": f"La categoría '{category}' no es accesible desde la interfaz web",
                "editable_categories": list(editable_categories)
            }), 403
        
        preferences = get_user_preferences(category)
        
        return jsonify({
            "success": True,
            "user": get_current_user(),
            "category": category,
            "preferences": preferences
        })
        
    except Exception as e:
        logger.error(f"Error obteniendo preferencias de categoría {category}: {e}")
        return jsonify({
            "success": False,
            "error": f"Error obteniendo preferencias de categoría '{category}'",
            "message": str(e)
        }), 500

@user_api.route('/preferences/<category>', methods=['PUT'])
@require_user_context
def update_user_preference_category(category):
    """
    Actualiza una categoría específica de preferencias del usuario actual.
    Solo permite editar categorías específicas definidas como editables.
    
    Args:
        category: Nombre de la categoría
        
    Body JSON: Las nuevas preferencias para la categoría
    
    Returns:
        JSON: Resultado de la actualización
    """
    try:
        # Categorías que pueden ser editadas por el usuario
        editable_categories = {
            'usuario',
            'contexto_cultural', 
            'mascotas',
            'intereses',
            'religion',
            'ejemplos_personalizacion'
        }
        
        # Verificar si la categoría es editable
        if category not in editable_categories:
            return jsonify({
                "success": False,
                "error": f"La categoría '{category}' no puede ser editada desde la interfaz web",
                "editable_categories": list(editable_categories)
            }), 403
        
        data = request.get_json()
        if not data:
            return jsonify({
                "success": False,
                "error": "No se proporcionaron datos para actualizar"
            }), 400
        
        # Actualizar preferencias
        success = set_user_preferences(category, data)
        
        if success:
            return jsonify({
                "success": True,
                "message": f"Preferencias de categoría '{category}' actualizadas",
                "user": get_current_user(),
                "category": category
            })
        else:
            return jsonify({
                "success": False,
                "error": "Error actualizando preferencias"
            }), 500
        
    except Exception as e:
        logger.error(f"Error actualizando preferencias de categoría {category}: {e}")
        return jsonify({
            "success": False,
            "error": f"Error actualizando preferencias de categoría '{category}'",
            "message": str(e)
        }), 500

@user_api.route('/system/status', methods=['GET'])
@require_user_context
def get_system_status():
    """
    Obtiene el estado general del sistema multi-usuario.
    
    Returns:
        JSON: Estado del sistema y estadísticas
    """
    try:
        users = user_manager.get_users_list()
        current_user = get_current_user()
        
        # Calcular estadísticas
        total_users = len(users)
        active_users = len([u for u in users if u['is_active']])
        
        # Información del sistema
        system_info = {
            "total_users": total_users,
            "active_users": active_users,
            "current_user": current_user,
            "data_directory": str(user_manager.data_path),
            "users_directory": str(user_manager.users_path),
            "system_database": str(user_manager.system_path / "users_registry.db"),
            "backups_directory": str(user_manager.backups_path)
        }
        
        # Contar backups
        backup_files = list(user_manager.backups_path.glob("*.zip"))
        system_info["total_backups"] = len(backup_files)
        
        return jsonify({
            "success": True,
            "system": system_info,
            "users": users
        })
        
    except Exception as e:
        logger.error(f"Error obteniendo estado del sistema: {e}")
        return jsonify({
            "success": False,
            "error": "Error obteniendo estado del sistema",
            "message": str(e)
        }), 500