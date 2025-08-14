import sqlite3
from datetime import datetime
import os
import logging

logger = logging.getLogger(__name__)
DB_PATH = os.path.join(os.path.dirname(__file__), "app.db")

def get_conn():
    conn = sqlite3.connect(DB_PATH); conn.row_factory = sqlite3.Row; return conn

def init_db():
    conn = get_conn(); c = conn.cursor()
    # Para asegurar una transición limpia, eliminamos la tabla vieja si existe
    c.execute("DROP TABLE IF EXISTS reminders")
    c.execute("""CREATE TABLE IF NOT EXISTS reminders (id INTEGER PRIMARY KEY, medication_name TEXT NOT NULL, photo_path TEXT, times TEXT NOT NULL, days_of_week TEXT NOT NULL)""")
    c.execute("""CREATE TABLE IF NOT EXISTS contacts (id INTEGER PRIMARY KEY, display_name TEXT NOT NULL, aliases TEXT NOT NULL, contact_method TEXT NOT NULL, contact_details TEXT NOT NULL, is_emergency INTEGER NOT NULL DEFAULT 0)""")
    c.execute("""CREATE TABLE IF NOT EXISTS settings (key TEXT PRIMARY KEY NOT NULL, value TEXT NOT NULL)""")
    conn.commit(); conn.close()

def add_reminder(med_name, path, times, days):
    conn = get_conn(); conn.execute("INSERT INTO reminders (medication_name, photo_path, times, days_of_week) VALUES (?, ?, ?, ?)", (med_name, path, times, days)); conn.commit(); conn.close()
def list_reminders():
    conn = get_conn(); return [dict(row) for row in conn.execute("SELECT * FROM reminders ORDER BY id").fetchall()]
def delete_reminder(rid):
    conn = get_conn(); conn.execute("DELETE FROM reminders WHERE id = ?", (rid,)); conn.commit(); conn.close()
def add_contact(name, aliases, method, details, is_emergency):
    conn = get_conn(); conn.execute("INSERT INTO contacts (display_name, aliases, contact_method, contact_details, is_emergency) VALUES (?, ?, ?, ?, ?)", (name, ", ".join([a.strip().lower() for a in aliases.split(',')]), method, details, 1 if is_emergency else 0)); conn.commit(); conn.close()
def list_contacts():
    conn = get_conn(); return [dict(row) for row in conn.execute("SELECT * FROM contacts ORDER BY display_name").fetchall()]
def delete_contact(cid):
    conn = get_conn(); conn.execute("DELETE FROM contacts WHERE id = ?", (cid,)); conn.commit(); conn.close()
def get_setting(key, default=None):
    conn = get_conn(); row = conn.execute("SELECT value FROM settings WHERE key = ?", (key,)).fetchone(); return row['value'] if row else default
def set_setting(key, value):
    conn = get_conn(); conn.execute("INSERT OR REPLACE INTO settings (key, value) VALUES (?, ?)", (key, value)); conn.commit(); conn.close()
