import sqlite3
from datetime import datetime
import os
import logging

logger = logging.getLogger(__name__)

DB_PATH = os.path.join(os.path.dirname(__file__), "app.db")

def get_conn():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn

def init_db():
    """Inicializa la base de datos, incluyendo la nueva tabla de tareas."""
    logger.info(f"Inicializa base de datos en: {DB_PATH}")
    conn = get_conn()
    c = conn.cursor()
    
    # --- CAMBIO: Se elimina la tabla de tareas vieja si existe ---
    c.execute("DROP TABLE IF EXISTS tasks")
    logger.info("Tabla de tareas vieja eliminada para aplicar nuevo esquema.")

    # Tabla de recordatorios (sin cambios)
    c.execute("""
    CREATE TABLE IF NOT EXISTS reminders (
        id INTEGER PRIMARY KEY, medication_name TEXT NOT NULL, photo_path TEXT,
        times TEXT NOT NULL, days_of_week TEXT NOT NULL
    )""")
    
    # --- NUEVA TABLA DE TAREAS ---
    c.execute("""
    CREATE TABLE IF NOT EXISTS tasks (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        task_name TEXT NOT NULL,
        times TEXT NOT NULL,
        days_of_week TEXT NOT NULL
    )
    """)
    
    # (El resto de las tablas no cambian)
    c.execute("""
    CREATE TABLE IF NOT EXISTS contacts (
        id INTEGER PRIMARY KEY, display_name TEXT NOT NULL, aliases TEXT NOT NULL,
        contact_method TEXT NOT NULL, contact_details TEXT NOT NULL,
        is_emergency INTEGER NOT NULL DEFAULT 0
    )""")
    c.execute("""
    CREATE TABLE IF NOT EXISTS settings (
        key TEXT PRIMARY KEY NOT NULL, value TEXT NOT NULL
    )""")
    
    conn.commit()
    conn.close()
    logger.info("Base de datos inicializada con el nuevo esquema de tareas.")

# --- FUNCIONES DE RECORDATORIOS (SIN CAMBIOS) ---
def add_reminder(medication_name, photo_path, times, days_of_week):
    conn = get_conn()
    conn.execute("INSERT INTO reminders (medication_name, photo_path, times, days_of_week) VALUES (?, ?, ?, ?)",
                 (medication_name, photo_path, times, days_of_week))
    conn.commit()
    conn.close()

def list_reminders():
    conn = get_conn()
    rows = conn.execute("SELECT * FROM reminders ORDER BY id").fetchall()
    conn.close()
    return [dict(row) for row in rows]

def delete_reminder(reminder_id):
    conn = get_conn()
    conn.execute("DELETE FROM reminders WHERE id = ?", (reminder_id,))
    conn.commit()
    conn.close()

# --- NUEVAS FUNCIONES PARA TAREAS ---
def add_task(task_name, times, days_of_week):
    """Añade una nueva tarea recurrente."""
    conn = get_conn()
    conn.execute("INSERT INTO tasks (task_name, times, days_of_week) VALUES (?, ?, ?)",
                 (task_name, times, days_of_week))
    conn.commit()
    conn.close()

def list_tasks():
    """Lista todas las tareas recurrentes."""
    conn = get_conn()
    rows = conn.execute("SELECT * FROM tasks ORDER BY id").fetchall()
    conn.close()
    return [dict(row) for row in rows]

def delete_task(task_id):
    """Elimina una tarea por su ID."""
    conn = get_conn()
    conn.execute("DELETE FROM tasks WHERE id = ?", (task_id,))
    conn.commit()
    conn.close()

# --- FUNCIONES DE CONTACTOS (SIN CAMBIOS) ---
def add_contact(display_name, aliases, method, details, is_emergency):
    conn = get_conn()
    emergency_flag = 1 if is_emergency else 0
    clean_aliases = ", ".join([alias.strip().lower() for alias in aliases.split(',')])
    conn.execute("INSERT INTO contacts (display_name, aliases, contact_method, contact_details, is_emergency) VALUES (?, ?, ?, ?, ?)",
              (display_name, clean_aliases, method, details, emergency_flag))
    conn.commit()
    conn.close()

def list_contacts():
    conn = get_conn()
    rows = conn.execute("SELECT * FROM contacts ORDER BY display_name").fetchall()
    conn.close()
    return [dict(row) for row in rows]

def delete_contact(contact_id):
    conn = get_conn()
    conn.execute("DELETE FROM contacts WHERE id = ?", (contact_id,))
    conn.commit()
    conn.close()

# --- FUNCIONES DE CONFIGURACIÓN (SIN CAMBIOS) ---
def get_setting(key, default_value=None):
    conn = get_conn()
    row = conn.execute("SELECT value FROM settings WHERE key = ?", (key,)).fetchone()
    conn.close()
    return row['value'] if row else default_value

def set_setting(key, value):
    conn = get_conn()
    conn.execute("INSERT OR REPLACE INTO settings (key, value) VALUES (?, ?)", (key, value))
    conn.commit()
    conn.close()
