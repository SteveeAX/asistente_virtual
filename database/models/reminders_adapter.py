#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
Reminders Adapter - Adaptador para sistema híbrido compartido/por usuario

Este módulo redirige operaciones según el tipo de dato:
- Medicamentos, tareas, contactos, configuración → BD compartida
- Solo preferencias IA → BD por usuario

Autor: Asistente Kata
Fecha: 2025-08-25
Versión: 2.0.0 - Sistema compartido
"""

import logging
from typing import List, Dict, Any

# Importar el nuevo adaptador compartido
from .shared_reminders_adapter import shared_reminders_adapter

logger = logging.getLogger(__name__)

class RemindersAdapter:
    """
    Adaptador que redirige todas las operaciones al sistema compartido.
    
    Este adaptador mantiene la misma interfaz que el anterior, pero ahora
    redirige todas las operaciones (excepto preferencias) al sistema compartido.
    
    Mantiene compatibilidad total con el código existente.
    """
    
    def __init__(self, fallback_to_legacy=True):
        """
        Inicializa el adaptador compartido.
        
        Args:
            fallback_to_legacy: Si True, usa el sistema legacy como fallback
        """
        # Simplemente delegamos todo al adaptador compartido
        self.shared_adapter = shared_reminders_adapter
        logger.info("RemindersAdapter actualizado para usar sistema compartido")
    
    # === DELEGACIÓN COMPLETA AL SHARED ADAPTER ===
    
    # Métodos de medicamentos
    def list_reminders(self) -> List[Dict[str, Any]]:
        """Lista medicamentos desde BD compartida."""
        return self.shared_adapter.list_reminders()
    
    def list_medications(self) -> List[Dict[str, Any]]:
        """Lista medicamentos desde BD compartida."""
        return self.shared_adapter.list_medications()
    
    def add_reminder(self, medication_name: str, photo_path: str, times: str, 
                    days_of_week: str, cantidad: str = "", prescripcion: str = "") -> bool:
        """Agrega medicamento a BD compartida."""
        return self.shared_adapter.add_reminder(medication_name, photo_path, times, days_of_week, cantidad, prescripcion)
    
    def add_medication(self, name: str, quantity: str = "", prescription: str = "",
                      times: List[str] = None, days: List[str] = None, photo_path: str = "") -> bool:
        """Agrega medicamento a BD compartida."""
        return self.shared_adapter.add_medication(name, quantity, prescription, times, days, photo_path)
    
    def delete_reminder(self, reminder_id: int) -> bool:
        """Elimina medicamento desde BD compartida."""
        return self.shared_adapter.delete_reminder(reminder_id)
    
    def delete_medication(self, medication_id: int) -> bool:
        """Elimina medicamento desde BD compartida."""
        return self.shared_adapter.delete_medication(medication_id)
    
    # Métodos de tareas
    def list_tasks(self) -> List[Dict[str, Any]]:
        """Lista tareas desde BD compartida."""
        return self.shared_adapter.list_tasks()
    
    def add_task(self, name: str, times: str, days: str) -> bool:
        """Agrega tarea a BD compartida."""
        return self.shared_adapter.add_task(name, times, days)
    
    def delete_task(self, task_id: int) -> bool:
        """Elimina tarea desde BD compartida."""
        return self.shared_adapter.delete_task(task_id)
    
    # Métodos de contactos
    def list_contacts(self) -> List[Dict[str, Any]]:
        """Lista contactos desde BD compartida."""
        return self.shared_adapter.list_contacts()
    
    def add_contact(self, display_name: str, aliases: List[str], platform: str,
                   details: str, is_emergency: bool = False) -> bool:
        """Agrega contacto a BD compartida."""
        return self.shared_adapter.add_contact(display_name, aliases, platform, details, is_emergency)
    
    def delete_contact(self, contact_id: int) -> bool:
        """Elimina contacto desde BD compartida."""
        return self.shared_adapter.delete_contact(contact_id)
    
    # Métodos de configuración
    def get_setting(self, key: str, default_value: Any = None) -> Any:
        """Obtiene configuración desde BD compartida."""
        return self.shared_adapter.get_setting(key, default_value)
    
    def set_setting(self, key: str, value: Any) -> bool:
        """Establece configuración en BD compartida."""
        return self.shared_adapter.set_setting(key, value)
    
    # Métodos de preferencias (siguen siendo por usuario)
    def get_user_preferences(self, category: str = None) -> Dict[str, Any]:
        """Obtiene preferencias del usuario actual."""
        return self.shared_adapter.get_user_preferences(category)
    
    def set_user_preferences(self, category: str, preferences: Dict[str, Any]) -> bool:
        """Establece preferencias del usuario actual."""
        return self.shared_adapter.set_user_preferences(category, preferences)
    
    def get_current_user(self) -> str:
        """Obtiene el usuario actual."""
        return self.shared_adapter.get_current_user()

# Instancia global del adaptador (mantiene compatibilidad)
reminders_adapter = RemindersAdapter()