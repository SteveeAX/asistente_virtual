# voice_reminder_manager.py
import re
import logging
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Tuple
import reminders
from time_interpreter import parse_natural_time, format_time_confirmation, calculate_reminder_datetime

logger = logging.getLogger(__name__)

# Variable global para almacenar recordatorio pendiente
pending_confirmation = None

class VoiceReminderManager:
    def __init__(self):
        self.pending_confirmation = None  # Para recordatorios que esperan confirmación
    
    def parse_reminder_command(self, text: str) -> Optional[Dict]:
        """
        Analiza un comando de voz y extrae la información del recordatorio usando el nuevo intérprete de tiempo.
        
        Ejemplos de entrada:
        - "recuérdame llamar al doctor a las 3 de la tarde"
        - "recuérdame ir al banco mañana a las 10 de la mañana"
        - "recordatorio tomar vitaminas todos los días a las 8"
        """
        text = text.lower().strip()
        logger.info(f"VOICE_REMINDER: Parseando comando: '{text}'")
        
        # Usar el nuevo intérprete de tiempo
        time_result = parse_natural_time(text)
        
        if not time_result['success']:
            logger.warning(f"VOICE_REMINDER: No se pudo interpretar el tiempo en '{text}'")
            return None
        
        # Detectar frecuencia en el texto original
        frequency_patterns = {
            r'todos los días|cada día|diariamente': 'daily',
        }
        
        frequency = 'once'  # Por defecto una sola vez
        for pattern, freq_type in frequency_patterns.items():
            if re.search(pattern, text):
                frequency = freq_type
                logger.info(f"VOICE_REMINDER: Frecuencia detectada: {frequency}")
                break
        
        # Extraer la tarea del texto
        task_text = text
        # Remover palabras de comando y tiempo
        command_patterns = [
            r'recuérdame\s*', r'recordatorio\s*', r'recuerda que\s*', r'no olvides\s*',
            r'a las? \d{1,2}(?::\d{2})?\s*(?:de la )?\s*(?:mañana|tarde|noche)?',
            r'al mediodía', r'a medianoche', r'mañana\s*', r'pasado mañana\s*',
            r'todos los días\s*', r'cada día\s*', r'diariamente\s*'
        ]
        
        for pattern in command_patterns:
            task_text = re.sub(pattern, ' ', task_text, flags=re.IGNORECASE)
        
        # Limpiar espacios extras y palabras sueltas
        task_text = re.sub(r'\s+', ' ', task_text).strip()
        task_text = task_text.strip(' ,.;')
        
        if not task_text or len(task_text) < 3:
            logger.warning(f"VOICE_REMINDER: Tarea muy corta o vacía: '{task_text}'")
            return None
        
        # Calcular datetime usando el nuevo intérprete
        datetime_result = calculate_reminder_datetime(
            time_result['hour'], 
            time_result['minute'], 
            time_result['day_offset']
        )
        
        # Verificar si la hora ya pasó
        if not datetime_result['success']:
            logger.warning(f"VOICE_REMINDER: {datetime_result['message']}")
            return {
                'error': 'time_passed',
                'message': datetime_result['message']
            }  # Retornar error específico
        
        target_datetime = datetime_result['datetime']
        
        logger.info(f"VOICE_REMINDER: ✅ Recordatorio parseado - Tarea: '{task_text}', Datetime: {target_datetime}, Frecuencia: {frequency}")
        
        return {
            'task': task_text,
            'datetime': target_datetime,
            'frequency': frequency,
            'hour': time_result['hour'],
            'minute': time_result['minute'],
            'day_offset': time_result['day_offset'],
            'original_text': text
        }
    
    def create_reminder_directly(self, reminder_data: Dict) -> bool:
        """Crea el recordatorio directamente sin confirmación."""
        try:
            task = reminder_data['task']
            target_datetime = reminder_data['datetime']
            frequency = reminder_data['frequency']
            
            # Los recordatorios por voz SIEMPRE van a la tabla 'tasks' (no 'reminders')
            # Los 'reminders' son solo para medicinas con foto
            
            time_str = f"{reminder_data['hour']:02d}:{reminder_data['minute']:02d}"
            
            if frequency == 'daily':
                # Tarea diaria
                days_of_week = "mon,tue,wed,thu,fri,sat,sun"
            else:
                # Tarea única - usar el día específico de la semana
                day_names = ['mon', 'tue', 'wed', 'thu', 'fri', 'sat', 'sun']
                days_of_week = day_names[target_datetime.weekday()]
            
            # SIEMPRE usar add_task() para recordatorios por voz
            reminders.add_task(
                task_name=task,
                times=time_str,
                days_of_week=days_of_week
            )
            
            logger.info(f"VOICE_REMINDER: ✅ Recordatorio creado directamente: '{task}' a las {target_datetime}")
            return True
            
        except Exception as e:
            logger.error(f"VOICE_REMINDER: Error creando recordatorio: {e}")
            return False
    
    def format_time_description(self, reminder_data: Dict) -> str:
        """Formatea descripción del tiempo para confirmación."""
        hour = reminder_data['hour']
        minute = reminder_data['minute']
        day_offset = reminder_data['day_offset']
        
        return format_time_confirmation(hour, minute, day_offset)
    
    def convert_to_scheduler_format(self, reminder_data: Dict) -> Dict:
        """Convierte los datos del recordatorio al formato que espera el scheduler."""
        frequency = reminder_data['frequency']
        
        # Mapeo de días
        day_mapping = {
            'mondays': 'mon',
            'tuesdays': 'tue', 
            'wednesdays': 'wed',
            'thursdays': 'thu',
            'fridays': 'fri',
            'saturdays': 'sat',
            'sundays': 'sun'
        }
        
        if frequency == 'daily':
            days_of_week = 'mon,tue,wed,thu,fri,sat,sun'
        elif frequency in day_mapping:
            days_of_week = day_mapping[frequency]
        else:  # 'once'
            # Para recordatorios únicos, usar el día de la semana específico
            weekday = reminder_data['date'].weekday()
            days = ['mon', 'tue', 'wed', 'thu', 'fri', 'sat', 'sun']
            days_of_week = days[weekday]
        
        return {
            'task_name': reminder_data['task'],
            'times': reminder_data['time'],
            'days_of_week': days_of_week,
            'is_voice_created': True,  # Marcar como creado por voz
            'target_date': reminder_data['date'].isoformat() if frequency == 'once' else None
        }
    
    def confirm_reminder(self, reminder_data: Dict) -> bool:
        """Confirma y crea el recordatorio en la base de datos."""
        try:
            scheduler_data = self.convert_to_scheduler_format(reminder_data)
            
            # Guardar en la base de datos
            reminders.add_task(
                scheduler_data['task_name'],
                scheduler_data['times'], 
                scheduler_data['days_of_week']
            )
            
            logger.info(f"Recordatorio por voz creado: {scheduler_data['task_name']} a las {scheduler_data['times']}")
            return True
            
        except Exception as e:
            logger.error(f"Error al crear recordatorio por voz: {e}")
            return False
    
    def list_voice_reminders(self) -> List[Dict]:
        """Lista todos los recordatorios de tareas (incluyendo los creados por voz)."""
        try:
            return reminders.list_tasks()
        except Exception as e:
            logger.error(f"Error al listar recordatorios: {e}")
            return []
    
    def format_reminders_list(self, reminders_list: List[Dict]) -> str:
        """Formatea la lista de recordatorios para respuesta por voz."""
        if not reminders_list:
            return "No tienes recordatorios programados."
        
        if len(reminders_list) == 1:
            reminder = reminders_list[0]
            return f"Tienes un recordatorio: {reminder['task_name']} a las {reminder['times']}."
        
        response = f"Tienes {len(reminders_list)} recordatorios: "
        for i, reminder in enumerate(reminders_list, 1):
            response += f"{i}. {reminder['task_name']} a las {reminder['times']}"
            if i < len(reminders_list):
                response += ", "
        
        return response
    
    def delete_reminder_by_voice(self, text: str) -> Dict:
        """Elimina recordatorios basándose en comando de voz."""
        text = text.lower().strip()
        logger.info(f"VOICE_REMINDER: Procesando eliminación: '{text}'")
        
        # Patrones para identificar qué eliminar
        if 'todos' in text or 'todo' in text:
            return self._delete_all_reminders()
        
        # Buscar por nombre/tarea específica
        # Extraer la tarea después de palabras clave de eliminación
        task_patterns = [
            r'elimina(?:\s+el)?\s+recordatorio\s+(?:de\s+)?(.+)',
            r'borra(?:\s+el)?\s+recordatorio\s+(?:de\s+)?(.+)',
            r'cancela(?:\s+el)?\s+recordatorio\s+(?:de\s+)?(.+)',
            r'quita(?:\s+el)?\s+recordatorio\s+(?:de\s+)?(.+)',
        ]
        
        for pattern in task_patterns:
            match = re.search(pattern, text)
            if match:
                task_query = match.group(1).strip()
                return self._delete_reminder_by_task(task_query)
        
        # Si no encuentra patrón específico, mostrar lista
        return {
            'success': False,
            'message': 'No entendí qué recordatorio eliminar. Di algo como "elimina el recordatorio de llamar al doctor" o "borra todos los recordatorios".'
        }
    
    def _delete_all_reminders(self) -> Dict:
        """Elimina todos los recordatorios de voz (solo tabla tasks)."""
        try:
            # SOLO eliminar tareas (recordatorios por voz)
            # NO tocar la tabla 'reminders' (son recordatorios médicos de la web)
            all_tasks = reminders.list_tasks()
            
            deleted_count = 0
            
            # Eliminar SOLO tareas de voz
            for task in all_tasks:
                reminders.delete_task(task['id'])
                deleted_count += 1
            
            if deleted_count > 0:
                return {
                    'success': True,
                    'message': f"Eliminé {deleted_count} recordatorios en total."
                }
            else:
                return {
                    'success': False,
                    'message': "No había recordatorios para eliminar."
                }
                
        except Exception as e:
            logger.error(f"VOICE_REMINDER: Error eliminando todos los recordatorios: {e}")
            return {
                'success': False,
                'message': "Hubo un error al eliminar los recordatorios."
            }
    
    def _delete_reminder_by_task(self, task_query: str) -> Dict:
        """Elimina recordatorio específico por nombre de tarea (solo de voz)."""
        try:
            # SOLO buscar en tareas de voz (NO en recordatorios médicos)
            all_tasks = reminders.list_tasks()
            for task in all_tasks:
                if task_query.lower() in task['task_name'].lower():
                    reminders.delete_task(task['id'])
                    return {
                        'success': True,
                        'message': f"Eliminé el recordatorio de '{task['task_name']}'."
                    }
            
            # No encontrado
            return {
                'success': False,
                'message': f"No encontré ningún recordatorio que contenga '{task_query}'. Usa la interfaz web para ver todos los recordatorios."
            }
            
        except Exception as e:
            logger.error(f"VOICE_REMINDER: Error eliminando recordatorio específico: {e}")
            return {
                'success': False,
                'message': "Hubo un error al buscar el recordatorio."
            }

# Instancia global
voice_reminder_manager = VoiceReminderManager()

