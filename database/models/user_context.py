#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
User Context - Middleware y utilidades para contexto de usuario

Este módulo proporciona middleware de Flask y utilidades para manejar
automáticamente el contexto de usuario en todas las requests HTTP,
garantizando que cada operación se ejecute en el contexto correcto.

Autor: Asistente Kata
Fecha: 2024-08-18
Versión: 1.0.0
"""

import sqlite3
import logging
from functools import wraps
from flask import g, request, jsonify
from typing import Optional, Dict, Any

from .user_manager import user_manager

logger = logging.getLogger(__name__)

class UserContextMiddleware:
    """
    Middleware que inyecta contexto de usuario en todas las requests de Flask.
    """
    
    def __init__(self, app=None):
        """
        Inicializa el middleware.
        
        Args:
            app: Instancia de Flask (opcional, se puede configurar después)
        """
        self.app = app
        if app is not None:
            self.init_app(app)
    
    def init_app(self, app):
        """
        Configura el middleware con la aplicación Flask.
        
        Args:
            app: Instancia de Flask
        """
        self.app = app
        app.before_request(self.load_user_context)
        app.teardown_appcontext(self.close_user_context)
        
        logger.info("UserContextMiddleware configurado correctamente")
    
    def load_user_context(self):
        """
        Carga el contexto de usuario antes de cada request.
        Ejecutado automáticamente por Flask antes de cada endpoint.
        """
        try:
            # Cargar información del usuario actual
            g.current_user = user_manager.current_user
            g.user_manager = user_manager
            
            # Preparar conexión a BD del usuario (lazy loading)
            g.user_db_connection = None
            g.user_db_path = user_manager.get_user_database_path()
            
            # Verificar que el usuario existe
            if not user_manager.user_exists(g.current_user):
                logger.warning(f"Usuario actual no existe: {g.current_user}")
                # No bloqueamos la request, pero registramos el problema
            
            logger.debug(f"Contexto de usuario cargado: {g.current_user}")
            
        except Exception as e:
            logger.error(f"Error cargando contexto de usuario: {e}")
            # En caso de error, establecer valores por defecto
            g.current_user = 'francisca'
            g.user_manager = user_manager
            g.user_db_connection = None
    
    def close_user_context(self, exception=None):
        """
        Limpia el contexto de usuario después de cada request.
        
        Args:
            exception: Excepción si la request falló (opcional)
        """
        try:
            # Cerrar conexión a BD si está abierta
            if hasattr(g, 'user_db_connection') and g.user_db_connection:
                g.user_db_connection.close()
                logger.debug("Conexión a BD de usuario cerrada")
                
        except Exception as e:
            logger.error(f"Error cerrando contexto de usuario: {e}")

def get_user_db() -> sqlite3.Connection:
    """
    Obtiene la conexión a la base de datos del usuario actual.
    Utiliza lazy loading para crear la conexión solo cuando se necesite.
    
    Returns:
        sqlite3.Connection: Conexión a la BD del usuario actual
        
    Raises:
        RuntimeError: Si no hay contexto de usuario disponible
    """
    if not hasattr(g, 'current_user'):
        raise RuntimeError("No hay contexto de usuario disponible. "
                         "Asegúrate de que UserContextMiddleware esté configurado.")
    
    # Lazy loading de la conexión
    if not hasattr(g, 'user_db_connection') or g.user_db_connection is None:
        try:
            g.user_db_connection = user_manager.get_user_database_connection(g.current_user)
            logger.debug(f"Conexión a BD abierta para usuario: {g.current_user}")
        except Exception as e:
            logger.error(f"Error abriendo conexión a BD para {g.current_user}: {e}")
            raise
    
    return g.user_db_connection

def get_current_user() -> str:
    """
    Obtiene el nombre del usuario actual.
    
    Returns:
        str: Nombre del usuario actual
        
    Raises:
        RuntimeError: Si no hay contexto de usuario disponible
    """
    if not hasattr(g, 'current_user'):
        raise RuntimeError("No hay contexto de usuario disponible")
    
    return g.current_user

def require_user_context(f):
    """
    Decorador que asegura que hay contexto de usuario disponible.
    
    Args:
        f: Función a decorar
        
    Returns:
        Función decorada que verifica contexto de usuario
    """
    @wraps(f)
    def decorated_function(*args, **kwargs):
        try:
            # Verificar que hay contexto de usuario
            current_user = get_current_user()
            
            # Verificar que el usuario existe
            if not user_manager.user_exists(current_user):
                return jsonify({
                    "error": "Usuario actual no válido",
                    "message": f"El usuario '{current_user}' no existe en el sistema"
                }), 400
            
            return f(*args, **kwargs)
            
        except RuntimeError as e:
            logger.error(f"Error de contexto de usuario en {f.__name__}: {e}")
            return jsonify({
                "error": "Error de contexto de usuario",
                "message": str(e)
            }), 500
        except Exception as e:
            logger.error(f"Error inesperado en {f.__name__}: {e}")
            return jsonify({
                "error": "Error interno del servidor",
                "message": "Error procesando la solicitud"
            }), 500
    
    return decorated_function

def switch_user_context(username: str) -> bool:
    """
    Cambia el contexto de usuario para la sesión actual.
    
    Args:
        username: Nombre del usuario al que cambiar
        
    Returns:
        bool: True si el cambio fue exitoso, False en caso contrario
    """
    try:
        # Verificar que el usuario existe
        if not user_manager.user_exists(username):
            logger.error(f"Intento de cambio a usuario inexistente: {username}")
            return False
        
        # Cerrar conexión actual si existe
        if hasattr(g, 'user_db_connection') and g.user_db_connection:
            g.user_db_connection.close()
            g.user_db_connection = None
        
        # Cambiar usuario en el manager
        success = user_manager.switch_user(username)
        
        if success:
            # Actualizar contexto local
            g.current_user = username
            g.user_db_path = user_manager.get_user_database_path(username)
            logger.info(f"Contexto de usuario cambiado a: {username}")
        
        return success
        
    except Exception as e:
        logger.error(f"Error cambiando contexto de usuario a {username}: {e}")
        return False

def get_user_preferences(category: Optional[str] = None) -> Dict[str, Any]:
    """
    Obtiene las preferencias del usuario actual desde su BD.
    
    Args:
        category: Categoría específica de preferencias (opcional)
        
    Returns:
        Dict: Preferencias del usuario (todas o de la categoría especificada)
    """
    try:
        db = get_user_db()
        cursor = db.cursor()
        
        if category:
            # Obtener categoría específica
            cursor.execute("SELECT data FROM preferences WHERE category = ?", (category,))
            result = cursor.fetchone()
            
            if result:
                import json
                return json.loads(result[0])
            else:
                return {}
        else:
            # Usar el método híbrido del UserManager para obtener todas las preferencias
            from .user_manager import user_manager
            return user_manager.get_user_preferences()
            
    except Exception as e:
        logger.error(f"Error obteniendo preferencias del usuario: {e}")
        return {}

def set_user_preferences(category: str, preferences: Dict[str, Any]) -> bool:
    """
    Actualiza las preferencias del usuario actual en su BD.
    
    Args:
        category: Categoría de preferencias a actualizar
        preferences: Datos de preferencias a guardar
        
    Returns:
        bool: True si la actualización fue exitosa, False en caso contrario
    """
    try:
        db = get_user_db()
        cursor = db.cursor()
        
        import json
        preferences_json = json.dumps(preferences, ensure_ascii=False)
        
        # Usar UPSERT (INSERT OR REPLACE)
        cursor.execute("""
            INSERT OR REPLACE INTO preferences (category, data, updated_at)
            VALUES (?, ?, CURRENT_TIMESTAMP)
        """, (category, preferences_json))
        
        db.commit()
        logger.info(f"Preferencias actualizadas para usuario {get_current_user()}, categoría: {category}")
        return True
        
    except Exception as e:
        logger.error(f"Error actualizando preferencias: {e}")
        return False

# Instancia global del middleware
user_context_middleware = UserContextMiddleware()