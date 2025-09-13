#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
Módulo reminders - Importa el adaptador de recordatorios para compatibilidad
"""

# Importar desde el sistema multi-usuario
try:
    from database.models.reminders_adapter import reminders_adapter
    
    # Exponer funciones principales para compatibilidad
    def list_reminders():
        return reminders_adapter.list_reminders()
    
    def add_reminder(medication_name, photo_path, times, days_of_week, cantidad="", prescripcion=""):
        return reminders_adapter.add_reminder(medication_name, photo_path, times, days_of_week, cantidad, prescripcion)
    
    def delete_reminder(reminder_id):
        return reminders_adapter.delete_reminder(reminder_id)
    
    def list_tasks():
        return reminders_adapter.list_tasks()
    
    def add_task(name, times, days):
        return reminders_adapter.add_task(name, times, days)
    
    def delete_task(task_id):
        return reminders_adapter.delete_task(task_id)
    
    def list_contacts():
        return reminders_adapter.list_contacts()
    
    def add_contact(name, aliases, phone=''):
        return reminders_adapter.add_contact(name, aliases, phone)
    
    def delete_contact(contact_id):
        return reminders_adapter.delete_contact(contact_id)
    
    def get_setting(key, default=None):
        return reminders_adapter.get_setting(key, default)
    
    def set_setting(key, value):
        return reminders_adapter.set_setting(key, value)

except ImportError as e:
    print(f"Error importando reminders_adapter: {e}")
    
    # Funciones dummy para evitar errores
    def list_reminders():
        return []
    
    def add_reminder(medication_name, photo_path, times, days_of_week, cantidad="", prescripcion=""):
        return None
    
    def delete_reminder(reminder_id):
        return False
    
    def list_tasks():
        return []
    
    def add_task(name, times, days):
        return None
    
    def delete_task(task_id):
        return False
    
    def list_contacts():
        return []
    
    def add_contact(name, aliases, phone=''):
        return None
    
    def delete_contact(contact_id):
        return False
    
    def get_setting(key, default=None):
        return default
    
    def set_setting(key, value):
        return False