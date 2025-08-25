#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
Shared Reminders Adapter - Adaptador para datos compartidos

Este adaptador proporciona la misma interfaz que el RemindersAdapter original,
pero redirige todas las operaciones (excepto preferencias) a la base de datos compartida.

Solo las preferencias de personalización IA siguen siendo por usuario.

Autor: Asistente Kata
Fecha: 2025-08-25
Versión: 2.0.0
"""

import logging
from typing import List, Dict, Any, Optional

from .shared_data_manager import shared_data_manager
from .user_context import get_current_user, get_user_preferences, set_user_preferences

logger = logging.getLogger(__name__)

class SharedRemindersAdapter:
    """
    Adaptador que redirige operaciones a base de datos compartida,
    manteniendo compatibilidad con la interfaz original.
    
    - Medicamentos, tareas, contactos, configuración → BD compartida
    - Solo preferencias IA → BD por usuario
    """
    
    def __init__(self, fallback_to_legacy=True):
        """
        Inicializa el adaptador compartido.
        
        Args:
            fallback_to_legacy: Si usar sistema legacy como fallback
        """
        self.fallback_to_legacy = fallback_to_legacy
        self.legacy_available = True
        
        # Intentar importar el sistema legacy para fallback
        try:
            import reminders as legacy_reminders
            self.legacy_reminders = legacy_reminders
            logger.info("Sistema legacy disponible como fallback")
        except ImportError:
            self.legacy_available = False
            logger.warning("Sistema legacy no disponible")
    
    def _use_shared_system(self) -> bool:
        """Determina si el sistema compartido está disponible."""
        try:
            # Verificar que el gestor compartido funciona
            shared_data_manager.get_connection().close()
            return True
        except Exception as e:
            logger.warning(f"Sistema compartido no disponible: {e}")
            return False
    
    def _execute_with_fallback(self, shared_func, legacy_func, *args, **kwargs):
        """
        Ejecuta función en sistema compartido, con fallback a legacy.
        """
        if self._use_shared_system():
            try:
                return shared_func(*args, **kwargs)
            except Exception as e:
                logger.error(f"Error en sistema compartido: {e}")
                if self.fallback_to_legacy and self.legacy_available:
                    logger.info("Fallback a sistema legacy")
                    return legacy_func(*args, **kwargs)
                else:
                    raise
        else:
            if self.legacy_available:
                return legacy_func(*args, **kwargs)
            else:
                raise RuntimeError("Ni sistema compartido ni legacy disponibles")
    
    # === MÉTODOS DE MEDICAMENTOS (COMPARTIDOS) ===
    
    def list_reminders(self) -> List[Dict[str, Any]]:
        """Lista todos los medicamentos. Alias para compatibilidad."""
        return self.list_medications()
    
    def list_medications(self) -> List[Dict[str, Any]]:
        """Lista todos los medicamentos desde BD compartida."""
        return self._execute_with_fallback(
            shared_data_manager.list_medications,
            lambda: self.legacy_reminders.list_medications() 
            if hasattr(self.legacy_reminders, 'list_medications') else []
        )
    
    def add_reminder(self, medication_name: str, photo_path: str, times: str, 
                    days_of_week: str, cantidad: str = "", prescripcion: str = "") -> bool:
        """Agrega medicamento. Método para compatibilidad con API web."""
        # Convertir formato de API a formato interno
        times_list = [t.strip() for t in times.split(',') if t.strip()]
        days_list = [d.strip() for d in days_of_week.split(',') if d.strip()]
        
        return self.add_medication(medication_name, cantidad, prescripcion, times_list, days_list, photo_path)
    
    def add_medication(self, name: str, quantity: str = "", prescription: str = "",
                      times: List[str] = None, days: List[str] = None, photo_path: str = "") -> bool:
        """Agrega medicamento a BD compartida."""
        return self._execute_with_fallback(
            shared_data_manager.add_medication,
            lambda n, q, p, t, d, ph: self.legacy_reminders.add_medication(n, q, p, t, d, ph)
            if hasattr(self.legacy_reminders, 'add_medication') else False,
            name, quantity, prescription, times, days, photo_path
        )
    
    def delete_reminder(self, reminder_id: int) -> bool:
        """Elimina medicamento. Método para compatibilidad con API."""
        return self.delete_medication(reminder_id)
    
    def delete_medication(self, medication_id: int) -> bool:
        """Elimina medicamento desde BD compartida."""
        return self._execute_with_fallback(
            shared_data_manager.delete_medication,
            lambda mid: self.legacy_reminders.delete_medication(mid)
            if hasattr(self.legacy_reminders, 'delete_medication') else False,
            medication_id
        )
    
    # === MÉTODOS DE TAREAS (COMPARTIDAS) ===
    
    def list_tasks(self) -> List[Dict[str, Any]]:
        """Lista todas las tareas desde BD compartida."""
        return self._execute_with_fallback(
            shared_data_manager.list_tasks,
            lambda: self.legacy_reminders.list_tasks()
            if hasattr(self.legacy_reminders, 'list_tasks') else []
        )
    
    def add_task(self, name: str, times: str, days: str) -> bool:
        """Agrega tarea. Acepta formato string para compatibilidad con API."""
        # Convertir de formato API (strings) a formato interno (listas)
        if isinstance(times, str):
            times_list = [t.strip() for t in times.split(',') if t.strip()]
        else:
            times_list = times
            
        if isinstance(days, str):
            days_list = [d.strip() for d in days.split(',') if d.strip()]
        else:
            days_list = days
        
        return self._execute_with_fallback(
            lambda n, t, d: shared_data_manager.add_task(n, t, d),
            lambda n, t, d: self.legacy_reminders.add_task(n, t, d)
            if hasattr(self.legacy_reminders, 'add_task') else False,
            name, times_list, days_list
        )
    
    def delete_task(self, task_id: int) -> bool:
        """Elimina tarea desde BD compartida."""
        return self._execute_with_fallback(
            shared_data_manager.delete_task,
            lambda tid: self.legacy_reminders.delete_task(tid)
            if hasattr(self.legacy_reminders, 'delete_task') else False,
            task_id
        )
    
    # === MÉTODOS DE CONTACTOS (COMPARTIDOS) ===
    
    def list_contacts(self) -> List[Dict[str, Any]]:
        """Lista todos los contactos desde BD compartida."""
        return self._execute_with_fallback(
            shared_data_manager.list_contacts,
            lambda: self.legacy_reminders.list_contacts()
            if hasattr(self.legacy_reminders, 'list_contacts') else []
        )
    
    def add_contact(self, display_name: str, aliases: List[str], platform: str,
                   details: str, is_emergency: bool = False) -> bool:
        """Agrega contacto a BD compartida."""
        return self._execute_with_fallback(
            shared_data_manager.add_contact,
            lambda dn, a, p, d, ie: self.legacy_reminders.add_contact(dn, a, p, d, ie)
            if hasattr(self.legacy_reminders, 'add_contact') else False,
            display_name, aliases, platform, details, is_emergency
        )
    
    def delete_contact(self, contact_id: int) -> bool:
        """Elimina contacto desde BD compartida."""
        return self._execute_with_fallback(
            shared_data_manager.delete_contact,
            lambda cid: self.legacy_reminders.delete_contact(cid)
            if hasattr(self.legacy_reminders, 'delete_contact') else False,
            contact_id
        )
    
    # === MÉTODOS DE CONFIGURACIÓN (COMPARTIDA) ===
    
    def get_setting(self, key: str, default_value: Any = None) -> Any:
        """Obtiene configuración desde BD compartida."""
        return self._execute_with_fallback(
            shared_data_manager.get_setting,
            lambda k, d: self.legacy_reminders.get_setting(k, d)
            if hasattr(self.legacy_reminders, 'get_setting') else d,
            key, default_value
        )
    
    def set_setting(self, key: str, value: Any) -> bool:
        """Establece configuración en BD compartida."""
        return self._execute_with_fallback(
            lambda k, v: shared_data_manager.set_setting(k, v),
            lambda k, v: self.legacy_reminders.set_setting(k, v)
            if hasattr(self.legacy_reminders, 'set_setting') else True,
            key, value
        )
    
    # === MÉTODOS DE PREFERENCIAS (POR USUARIO) ===
    
    def get_user_preferences(self, category: str = None) -> Dict[str, Any]:
        """
        Obtiene preferencias del usuario actual.
        Este es el ÚNICO método que sigue siendo por usuario.
        """
        try:
            return get_user_preferences(category)
        except Exception as e:
            logger.error(f"Error obteniendo preferencias de usuario: {e}")
            return {}
    
    def set_user_preferences(self, category: str, preferences: Dict[str, Any]) -> bool:
        """
        Establece preferencias del usuario actual.
        Este es el ÚNICO método que sigue siendo por usuario.
        """
        try:
            return set_user_preferences(category, preferences)
        except Exception as e:
            logger.error(f"Error estableciendo preferencias de usuario: {e}")
            return False
    
    def get_current_user(self) -> str:
        """Obtiene el usuario actual (para compatibilidad)."""
        try:
            return get_current_user()
        except Exception as e:
            logger.error(f"Error obteniendo usuario actual: {e}")
            return "default_user"

# Instancia global del adaptador compartido
shared_reminders_adapter = SharedRemindersAdapter()