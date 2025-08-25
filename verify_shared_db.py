#!/usr/bin/env python3
import sqlite3
import json

# Verificar base de datos compartida
db_path = "data/system/shared_data.db"

print("=== VERIFICACIÓN BASE DE DATOS COMPARTIDA ===")

with sqlite3.connect(db_path) as conn:
    conn.row_factory = sqlite3.Row
    cursor = conn.cursor()
    
    # Ver tablas
    cursor.execute("SELECT name FROM sqlite_master WHERE type='table'")
    tables = [row[0] for row in cursor.fetchall()]
    print(f"Tablas: {tables}")
    
    # Medicamentos
    cursor.execute("SELECT COUNT(*) as count FROM reminders")
    med_count = cursor.fetchone()['count']
    print(f"Medicamentos: {med_count}")
    
    if med_count > 0:
        cursor.execute("SELECT name, quantity FROM reminders LIMIT 3")
        for row in cursor.fetchall():
            print(f"  - {row['name']}: {row['quantity']}")
    
    # Contactos
    cursor.execute("SELECT COUNT(*) as count FROM contacts")
    contact_count = cursor.fetchone()['count']
    print(f"Contactos: {contact_count}")
    
    # Tareas
    cursor.execute("SELECT COUNT(*) as count FROM tasks")
    task_count = cursor.fetchone()['count']
    print(f"Tareas: {task_count}")
    
    # Configuraciones
    cursor.execute("SELECT COUNT(*) as count FROM settings")
    settings_count = cursor.fetchone()['count']
    print(f"Configuraciones: {settings_count}")
    
    if settings_count > 0:
        cursor.execute("SELECT key, value FROM settings")
        for row in cursor.fetchall():
            print(f"  - {row['key']}: {row['value']}")

print("\n✅ Verificación completada")