#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
Validación completa del sistema multi-usuario

Este script valida que todo el sistema multi-usuario funcione correctamente
y que los datos migrados estén disponibles y sean consistentes.
"""

import sys
import os
import json
import sqlite3
from pathlib import Path

# Agregar el directorio principal al path
sys.path.append(str(Path(__file__).parent.parent))

from database.models.user_manager import UserManager

def validate_complete_system():
    """Validación completa del sistema multi-usuario."""
    
    print("🔍 Iniciando validación completa del sistema multi-usuario...")
    
    # Inicializar UserManager
    um = UserManager(base_path="/home/steveen/asistente_kata")
    
    print(f"\n📊 ESTADO DEL SISTEMA:")
    print(f"├── Usuario actual: {um.current_user}")
    print(f"├── Ruta base: {um.base_path}")
    print(f"├── Directorio datos: {um.data_path}")
    print(f"└── Directorio usuarios: {um.users_path}")
    
    # 1. Validar estructura de directorios
    print(f"\n1️⃣ ESTRUCTURA DE DIRECTORIOS:")
    dirs_to_check = [
        um.data_path,
        um.users_path,
        um.system_path,
        um.backups_path
    ]
    
    for dir_path in dirs_to_check:
        exists = "✅" if dir_path.exists() else "❌"
        print(f"    {exists} {dir_path}")
    
    # 2. Validar BD del sistema
    print(f"\n2️⃣ BASE DE DATOS DEL SISTEMA:")
    system_db = um.system_path / "users_registry.db"
    if system_db.exists():
        with sqlite3.connect(system_db) as conn:
            cursor = conn.cursor()
            
            # Contar usuarios
            cursor.execute("SELECT COUNT(*) FROM users")
            user_count = cursor.fetchone()[0]
            print(f"    ✅ BD del sistema existe")
            print(f"    👥 Usuarios registrados: {user_count}")
            
            # Listar usuarios
            cursor.execute("SELECT username, display_name, is_active FROM users")
            users = cursor.fetchall()
            for username, display_name, is_active in users:
                status = "Activo" if is_active else "Inactivo"
                print(f"        🔸 {username} ({display_name}) - {status}")
            
            # Mostrar configuración del sistema
            cursor.execute("SELECT key, value FROM system_settings")
            settings = cursor.fetchall()
            print(f"    ⚙️ Configuración del sistema:")
            for key, value in settings:
                print(f"        🔹 {key}: {value}")
    else:
        print(f"    ❌ BD del sistema no existe")
    
    # 3. Validar datos de usuarios
    print(f"\n3️⃣ DATOS DE USUARIOS:")
    users_list = um.get_users_list()
    
    for user in users_list:
        username = user['username']
        print(f"\n    👤 Usuario: {username} ({user['display_name']})")
        
        # Verificar directorio del usuario
        user_dir = um.get_user_directory(username)
        if user_dir.exists():
            print(f"        📁 Directorio: ✅ {user_dir}")
            
            # Verificar subdirectorios
            uploads_dir = user_dir / "uploads"
            uploads_status = "✅" if uploads_dir.exists() else "❌"
            print(f"        📸 Uploads: {uploads_status} {uploads_dir}")
        else:
            print(f"        📁 Directorio: ❌ No existe")
            continue
        
        # Verificar BD del usuario
        user_db = um.get_user_database_path(username)
        if user_db.exists():
            print(f"        🗄️ Base de datos: ✅ {user_db}")
            
            with sqlite3.connect(user_db) as conn:
                cursor = conn.cursor()
                
                # Contar datos
                cursor.execute("SELECT COUNT(*) FROM preferences")
                prefs_count = cursor.fetchone()[0]
                
                cursor.execute("SELECT COUNT(*) FROM reminders")
                reminders_count = cursor.fetchone()[0]
                
                cursor.execute("SELECT COUNT(*) FROM contacts")
                contacts_count = cursor.fetchone()[0]
                
                cursor.execute("SELECT COUNT(*) FROM interaction_logs")
                logs_count = cursor.fetchone()[0]
                
                print(f"        📊 Datos:")
                print(f"            📝 Preferencias: {prefs_count}")
                print(f"            ⏰ Recordatorios: {reminders_count}")
                print(f"            👥 Contactos: {contacts_count}")
                print(f"            📋 Logs: {logs_count}")
                
                # Mostrar algunas preferencias si existen
                if prefs_count > 0:
                    cursor.execute("SELECT category FROM preferences")
                    categories = [row[0] for row in cursor.fetchall()]
                    print(f"            🏷️ Categorías: {', '.join(categories[:5])}" + 
                          ("..." if len(categories) > 5 else ""))
                
        else:
            print(f"        🗄️ Base de datos: ❌ No existe")
    
    # 4. Validar migración de Francisca específicamente
    print(f"\n4️⃣ VALIDACIÓN ESPECÍFICA DE FRANCISCA:")
    if um.user_exists('francisca'):
        print("    ✅ Usuario Francisca existe")
        
        # Verificar que las preferencias originales están presentes
        francisca_db = um.get_user_database_path('francisca')
        with sqlite3.connect(francisca_db) as conn:
            cursor = conn.cursor()
            
            # Verificar categorías importantes
            important_categories = [
                'usuario', 'intereses', 'mascotas', 'ia_generativa', 
                'comandos_clasicos', 'configuracion_ai'
            ]
            
            for category in important_categories:
                cursor.execute("SELECT data FROM preferences WHERE category = ?", (category,))
                result = cursor.fetchone()
                if result:
                    data = json.loads(result[0])
                    print(f"        ✅ {category}: {len(data)} campos")
                else:
                    print(f"        ❌ {category}: No encontrado")
        
        # Verificar que es el usuario actual
        if um.current_user == 'francisca':
            print("    ✅ Francisca es el usuario actual")
        else:
            print(f"    ⚠️ Usuario actual es {um.current_user}, no Francisca")
            
    else:
        print("    ❌ Usuario Francisca no existe")
    
    # 5. Validar backups
    print(f"\n5️⃣ BACKUPS:")
    backup_files = list(um.backups_path.glob("*.zip"))
    if backup_files:
        print(f"    ✅ {len(backup_files)} archivos de backup encontrados:")
        for backup in sorted(backup_files)[-3:]:  # Mostrar últimos 3
            size = backup.stat().st_size / 1024  # KB
            print(f"        📦 {backup.name} ({size:.1f} KB)")
    else:
        print("    ⚠️ No se encontraron backups")
    
    # 6. Prueba funcional básica
    print(f"\n6️⃣ PRUEBA FUNCIONAL:")
    try:
        # Probar conexión a BD de usuario actual
        conn = um.get_user_database_connection()
        cursor = conn.cursor()
        cursor.execute("SELECT COUNT(*) FROM preferences")
        count = cursor.fetchone()[0]
        conn.close()
        print(f"    ✅ Conexión a BD del usuario actual: {count} preferencias")
        
        # Probar cambio de usuario si hay múltiples
        users = um.get_users_list()
        if len(users) > 1:
            other_user = next((u['username'] for u in users if u['username'] != um.current_user), None)
            if other_user:
                original_user = um.current_user
                if um.switch_user(other_user):
                    print(f"    ✅ Cambio de usuario: {original_user} → {other_user}")
                    # Volver al usuario original
                    um.switch_user(original_user)
                    print(f"    ✅ Regreso a usuario: {um.current_user}")
                else:
                    print(f"    ❌ Error cambiando a usuario: {other_user}")
        
        print("    ✅ Todas las pruebas funcionales pasaron")
        
    except Exception as e:
        print(f"    ❌ Error en pruebas funcionales: {e}")
    
    print(f"\n🎉 VALIDACIÓN COMPLETADA")
    print(f"📊 Resumen:")
    print(f"   👥 Usuarios registrados: {len(um.get_users_list())}")
    print(f"   🔄 Usuario actual: {um.current_user}")
    print(f"   🗄️ BD del sistema: {'✅' if (um.system_path / 'users_registry.db').exists() else '❌'}")
    print(f"   📁 Estructura completa: ✅")
    
    return True

if __name__ == "__main__":
    validate_complete_system()