#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
Aplicación Principal - Asistente Kata
====================================

Aplicación principal del asistente de voz para adultos mayores.
Punto de entrada refactorizado y organizado.

Autor: Asistente Kata
Version: 2.0.0 - Refactoring
"""

import customtkinter as ctk
import threading, queue, logging, time, os, sys
from apscheduler.schedulers.background import BackgroundScheduler
from datetime import datetime

# === SISTEMA HÍBRIDO: COMPARTIDO + POR USUARIO ===
# - Medicamentos, tareas, contactos, configuración → BD compartida (todos los usuarios)
# - Solo preferencias de IA → BD por usuario (para personalización)
# - RouterCentral sigue necesitando contexto de usuario para personalización

# --- Imports usando nueva estructura organizada ---
try:
    # Agregar src al path para imports relativos
    import sys
    import os
    # Desde src/app/main_app.py, necesitamos ir 2 niveles arriba para llegar al src
    src_path = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    project_root = os.path.dirname(src_path)
    
    if src_path not in sys.path:
        sys.path.insert(0, src_path)
    if project_root not in sys.path:
        sys.path.insert(0, project_root)
    
    # Importar desde estructura organizada
    from utils import system_actions, firestore_logger
    from core.audio import tts_manager, stt_manager, wakeword_detector
    from core.hardware import button_manager  
    from core.smart_home import smart_home_manager
    from messaging import (VoiceMessageSender, MessageReceiver, MessageReader, 
                               MessageNotifier, voice_message_sender, message_receiver)
    from messaging.voice_sender import initialize_voice_message_sender
    from ui.desktop import ClockInterface, ReminderTab, ContactTab
    from ai import (parse_intent, INTENTS, MessageAI, message_ai, 
                        VoiceReminderManager, voice_reminder_manager, intent_manager)
    
    # La ruta del proyecto ya fue agregada arriba
    
    ORGANIZED_IMPORTS = True
    logging.info("APP: Usando imports organizados (nuevo sistema)")
    
except ImportError as e:
    # Fallback a imports legacy
    logging.warning(f"APP: Usando imports legacy: {e}")
    
    # Agregar rutas necesarias para fallback
    import sys
    import os
    project_root = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
    if project_root not in sys.path:
        sys.path.insert(0, project_root)
    
    # Intentar imports legacy desde la raíz del proyecto (pueden no existir todos)
    try:
        import tts_manager, stt_manager, intent_manager, wakeword_detector, button_manager, smart_home_manager, firestore_logger, system_actions
    except ImportError:
        logging.warning("Algunos módulos legacy no disponibles")
    
    try:
        import message_receiver, message_reader, message_notifier, voice_message_sender
    except ImportError:
        logging.warning("Algunos módulos de mensajería legacy no disponibles")
    
    try:
        from contact_tab_updated import ContactTab
        from reminder_tab_updated import ReminderTab
        from clock_interface import ClockInterface
        from voice_reminder_manager import voice_reminder_manager
    except ImportError:
        logging.warning("Algunos módulos UI legacy no disponibles")
    
    ORGANIZED_IMPORTS = False

# --- Sistema Multi-Usuario ---
try:
    sys.path.append(os.path.join(os.path.dirname(__file__), '..', '..', 'database'))
    from models.reminders_adapter import reminders_adapter
    MULTI_USER_AVAILABLE = True
    logging.info("Sistema multi-usuario disponible en main_app")
except ImportError as e:
    MULTI_USER_AVAILABLE = False
    reminders_adapter = None
    logging.warning(f"Sistema multi-usuario no disponible: {e}")

# --- Módulos de IA Generativa ---
# Agregar directorio modules al path para importaciones
modules_path = os.path.join(os.path.dirname(__file__), '..', '..', 'modules')
if modules_path not in sys.path:
    sys.path.insert(0, modules_path)

# Importar RouterCentral con manejo de errores
try:
    from ai.generative.router_central import RouterCentral
    ROUTER_AVAILABLE = True
    logging.info("ROUTER: RouterCentral importado correctamente")
except ImportError as e:
    ROUTER_AVAILABLE = False
    logging.warning(f"ROUTER: RouterCentral no disponible: {e}")

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(threadName)s - %(name)s - %(message)s')
logger = logging.getLogger(__name__)
SETTINGS_FLAG_PATH = os.path.join(os.path.dirname(__file__), "..", "..", "settings_updated.flag")

# Configuraciones globales  
ENABLE_AI_GENERATIVE = True     # Flag para IA generativa

# Configuraciones del sistema unificado de confirmación de medicamentos
MEDICATION_TIMEOUT = 300  # 5 minutos totales (sistema unificado)
USER_NAME = "Usuario"  # Nombre del usuario para alertas (será actualizado dinámicamente)

# === FUNCIÓN HELPER PARA REMINDERS ===
def get_reminders_service():
    """
    Obtiene el servicio de recordatorios (ahora siempre sistema compartido).
    Medicamentos, tareas, contactos y configuración son compartidos entre usuarios.
    """
    if MULTI_USER_AVAILABLE and reminders_adapter:
        return reminders_adapter  # Ahora redirige a BD compartida
    else:
        return reminders  # Fallback legacy

# === FUNCIÓN HELPER PARA NOMBRE DE USUARIO ===
def get_current_user_name():
    """
    Obtiene el nombre del usuario actual desde el sistema multi-usuario.
    """
    global USER_NAME
    try:
        if MULTI_USER_AVAILABLE:
            from models.user_manager import user_manager
            preferences = user_manager.get_user_preferences()
            user_info = preferences.get('usuario', {})
            USER_NAME = user_info.get('nombre', 'Usuario')
            return USER_NAME
        else:
            return USER_NAME
    except Exception as e:
        logging.error(f"Error obteniendo nombre de usuario: {e}")
        return "Usuario"

class KataApp(ctk.CTk):
    def __init__(self):
        super().__init__()
        self.title("Asistente Kata")
        self.attributes('-fullscreen', True)
        ctk.set_appearance_mode("Light")

        # --- Atributos de la aplicación ---
        service = get_reminders_service()
        self.selected_voice = service.get_setting('voice_name', 'es-US-Neural2-A')
        self.is_speaking_or_listening = threading.Lock()
        self.admin_mode = False
        
        # --- RouterCentral para IA Generativa ---
        self.router_central = None
        
        # Estado del streaming
        self.is_streaming = False
        
        # --- Cargar nombre del usuario actual ---
        self.current_user_name = get_current_user_name()
        logging.info(f"Aplicación iniciada para usuario: {self.current_user_name}")
        
        # --- Estado del sistema unificado de confirmación de medicamentos ---
        self.medication_confirmation_state = "NORMAL"  # NORMAL, MEDICATION_ACTIVE
        self.current_medication_info = None
        self.medication_timer = None
        self.medication_repeat_timer = None

        # Forzar tema claro siempre
        self.is_light_theme = True  # Solo modo claro disponible

        # --- Configuración de la UI ---
        self.grid_rowconfigure(0, weight=1); self.grid_columnconfigure(0, weight=1)
        
        # Aplicar tema claro fijo
        ctk.set_appearance_mode("Light")
        container_color = "white"
            
        self.main_container = ctk.CTkFrame(self, fg_color=container_color)
        self.admin_container = ctk.CTkFrame(self, fg_color=container_color)
        self.main_container.grid(row=0, column=0, sticky="nsew")
        
        # Crear el ClockInterface y aplicar tema inicial
        self.clock_interface = ClockInterface(self.main_container)
        self.clock_interface.update_theme(self.is_light_theme)
        
        self.setup_admin_view()

        # --- Servicios de Fondo ---
        self.scheduler = BackgroundScheduler(timezone="America/Guayaquil")
        self.update_scheduler()
        self.scheduler.start()
        
        # Iniciar hilos después de que la ventana esté lista
        self.after(100, self.initialize_backend_threads)
        
        # --- Atajos de Teclado ---
        self.bind("<F12>", self.toggle_mode)
        self.bind("<Escape>", lambda event: self.on_closing())
        self.protocol("WM_DELETE_WINDOW", self.on_closing)

    # <--- FUNCIÓN DE HORA HUMANIZADA ---
    def get_speakable_time(self, dt_object):
        hour = dt_object.hour
        minute = dt_object.minute
        
        hour_words = {
            1: "una", 2: "dos", 3: "tres", 4: "cuatro", 5: "cinco", 6: "seis",
            7: "siete", 8: "ocho", 9: "nueve", 10: "diez", 11: "once", 12: "doce"
        }
        
        # Convertir a formato de 12 horas para el display
        if hour == 0:
            display_hour = 12
        elif hour > 12:
            display_hour = hour - 12
        else:
            display_hour = hour
        
        hour_word = hour_words.get(display_hour, str(display_hour))
        
        # Determinar período del día usando hora en formato 24h
        if 0 <= hour <= 5:
            period = "de la madrugada"
        elif 6 <= hour <= 11:
            period = "de la mañana"
        elif hour == 12:
            period = "del mediodía"
        elif 13 <= hour <= 18:  # 1pm a 6pm
            period = "de la tarde"
        else:  # 19 en adelante (7pm+)
            period = "de la noche"
        
        if minute == 0:
            minute_str = "en punto"
        elif minute == 15:
            minute_str = "y cuarto"
        elif minute == 30:
            minute_str = "y media"
        else:
            minute_str = f"y {minute}"
        
        if display_hour == 1:
            return f"Es la {hour_word} {minute_str} {period}."
        else:
            return f"Son las {hour_word} {minute_str} {period}."

    def setup_admin_view(self):
        tab_view = ctk.CTkTabview(self.admin_container); tab_view.pack(fill="both", expand=True, padx=10, pady=10)
        tab_view.add("Recordatorios"); tab_view.add("Contactos")
        self.reminder_tab = ReminderTab(tab_view.tab("Recordatorios"), self)
        self.contact_tab = ContactTab(tab_view.tab("Contactos"), self)
        ctk.CTkButton(self.admin_container, text="Volver a Modo Reloj", command=self.toggle_mode).pack(side="bottom", pady=10)

    def initialize_backend_threads(self):
        wakeword_detector.init_porcupine()
        
        # --- Inicializar RouterCentral ---
        self.initialize_router_central()
        
        # --- Inicializar Sistema de Mensajes Bidireccional ---
        self.initialize_message_system()
        
        # --- Conectar RouterCentral con VoiceMessageSender ---
        if hasattr(self, 'router_central') and self.router_central and hasattr(self, 'voice_message_sender'):
            self.router_central.voice_message_sender = self.voice_message_sender
            logging.info("MESSAGE_SYSTEM: ✅ RouterCentral conectado con VoiceMessageSender")
        
        self.start_wakeword_thread()
        threading.Thread(target=button_manager.start_button_listener, args=(
            self.on_button_short_press,
            self.on_button_long_press
        ), daemon=True, name="ButtonThread").start()
        threading.Thread(target=self.settings_checker, daemon=True, name="SettingsCheckerThread").start()

    def settings_checker(self):
        USER_CHANGED_FLAG_PATH = os.path.join(os.path.dirname(__file__), "..", "..", "user_changed.flag")
        
        while True:
            # Verificar cambios de configuración
            if os.path.exists(SETTINGS_FLAG_PATH):
                flag_content = ""
                try:
                    with open(SETTINGS_FLAG_PATH, 'r') as f: flag_content = f.read()
                    os.remove(SETTINGS_FLAG_PATH)
                except Exception as e: logging.error(f"Error procesando flag file: {e}")

                # Usamos self.after para encolar la acción en el hilo principal de la UI
                if flag_content == 'update_voice':
                    self.after(0, self.reload_voice_setting)
                elif flag_content == 'update_scheduler':
                    self.after(0, self.reload_scheduler)
            
            # Verificar cambios de usuario
            if os.path.exists(USER_CHANGED_FLAG_PATH):
                try:
                    with open(USER_CHANGED_FLAG_PATH, 'r') as f: 
                        user_change_info = f.read().strip()
                    os.remove(USER_CHANGED_FLAG_PATH)
                    
                    # Procesar cambio de usuario
                    self.after(0, lambda: self.handle_user_change(user_change_info))
                    
                except Exception as e: 
                    logging.error(f"Error procesando cambio de usuario: {e}")
            
            time.sleep(3)

    def initialize_router_central(self):
        """Inicializa el RouterCentral para IA generativa"""
        try:
            if ROUTER_AVAILABLE:
                # Crear RouterCentral con el intent_manager existente
                self.router_central = RouterCentral(intent_manager)
                logging.info("ROUTER: RouterCentral inicializado correctamente")
            else:
                logging.warning("ROUTER: RouterCentral no disponible, usando sistema clásico")
                self.router_central = None
        except Exception as e:
            logging.error(f"ROUTER: Error inicializando RouterCentral: {e}")
            self.router_central = None

    def initialize_message_system(self):
        """Inicializa el sistema completo de mensajes bidireccional"""
        try:
            logging.info("MESSAGE_SYSTEM: INICIANDO inicialización del sistema de mensajes...")
            
            # Obtener token del bot de Telegram desde variable de entorno
            logging.info("MESSAGE_SYSTEM: Buscando token de bot...")
            import os
            bot_token = os.getenv('TELEGRAM_BOT_TOKEN')
            if not bot_token:
                logging.error("MESSAGE_SYSTEM: Token de bot no encontrado, sistema de mensajes deshabilitado")
                return
            logging.info(f"MESSAGE_SYSTEM: ✅ Token encontrado: {bot_token[:10]}...")
            
            # Obtener ruta de BD compartida
            logging.info("MESSAGE_SYSTEM: Verificando sistema multi-usuario...")
            if MULTI_USER_AVAILABLE:
                # Importar directamente shared_data_manager
                from database.models.shared_data_manager import shared_data_manager
                db_path = str(shared_data_manager.shared_db_path)
                logging.info(f"MESSAGE_SYSTEM: ✅ BD path: {db_path}")
            else:
                logging.error("MESSAGE_SYSTEM: Sistema multi-usuario requerido para mensajes")
                return
            
            # 1. Inicializar MessageReceiver
            logging.info("MESSAGE_SYSTEM: Paso 1 - Inicializando MessageReceiver...")
            self.message_receiver = MessageReceiver(bot_token, db_path)
            if self.message_receiver:
                logging.info(f"MESSAGE_SYSTEM: ✅ MessageReceiver inicializado con {len(self.message_receiver.known_contacts)} contactos conocidos")
            else:
                logging.error("MESSAGE_SYSTEM: ❌ Error al inicializar MessageReceiver")
                return
            
            # 2. Inicializar MessageReader
            logging.info("MESSAGE_SYSTEM: Paso 2 - Inicializando MessageReader...")
            self.message_reader = MessageReader(db_path, tts_manager, self.selected_voice)
            if self.message_reader:
                logging.info("MESSAGE_SYSTEM: ✅ MessageReader inicializado")
            else:
                logging.error("MESSAGE_SYSTEM: ❌ Error al inicializar MessageReader")
            
            # 3. Inicializar MessageNotifier
            logging.info("MESSAGE_SYSTEM: Paso 3 - Inicializando MessageNotifier...")
            self.message_notifier = MessageNotifier(db_path, tts_manager, self.selected_voice)
            if self.message_notifier:
                logging.info("MESSAGE_SYSTEM: ✅ MessageNotifier inicializado")
            else:
                logging.error("MESSAGE_SYSTEM: ❌ Error al inicializar MessageNotifier")
            
            # 3.5. Inicializar VoiceMessageSender
            logging.info("MESSAGE_SYSTEM: Paso 3.5 - Inicializando VoiceMessageSender...")
            try:
                # MessageAI ya está importado arriba, usar la instancia existente
                if hasattr(self, 'router_central') and self.router_central and hasattr(self.router_central, 'generative_route'):
                    gemini_client = self.router_central.generative_route.gemini_client
                    message_ai_instance = MessageAI(gemini_client, None)
                else:
                    message_ai_instance = MessageAI(None, None)
                
                self.voice_message_sender = initialize_voice_message_sender(
                    tts_manager, self.selected_voice, message_ai_instance
                )
                if self.voice_message_sender:
                    logging.info("MESSAGE_SYSTEM: ✅ VoiceMessageSender inicializado")
                else:
                    logging.error("MESSAGE_SYSTEM: ❌ Error al inicializar VoiceMessageSender")
            except Exception as e:
                logging.error(f"MESSAGE_SYSTEM: Error inicializando VoiceMessageSender: {e}")
                self.voice_message_sender = None
            
            # 4. Configurar callback de UI para notificador Y lector
            logging.info("MESSAGE_SYSTEM: Paso 4 - Configurando callbacks de UI...")
            if self.message_notifier and hasattr(self.clock_interface, 'update_message_count'):
                self.message_notifier.set_ui_update_callback(self.clock_interface.update_message_count)
                logging.info("MESSAGE_SYSTEM: ✅ Callback de UI para notificador configurado")
            else:
                logging.error("MESSAGE_SYSTEM: ❌ Error configurando callback de UI para notificador")
            
            if self.message_reader and hasattr(self.clock_interface, 'update_message_count'):
                self.message_reader.set_ui_update_callback(self.clock_interface.update_message_count)
                logging.info("MESSAGE_SYSTEM: ✅ Callback de UI para lector configurado")
            else:
                logging.error("MESSAGE_SYSTEM: ❌ Error configurando callback de UI para lector")
            
            # 5. Configurar callback de nuevos mensajes
            logging.info("MESSAGE_SYSTEM: Paso 5 - Configurando callback de nuevos mensajes...")
            if self.message_receiver and self.message_notifier:
                self.message_receiver.add_new_message_callback(self.message_notifier.on_new_message)
                logging.info("MESSAGE_SYSTEM: ✅ Callback de nuevos mensajes configurado")
            else:
                logging.error("MESSAGE_SYSTEM: ❌ Error configurando callback de nuevos mensajes")
            
            # 6. Configurar ButtonManager con MessageReader
            logging.info("MESSAGE_SYSTEM: Paso 6 - Configurando ButtonManager...")
            if self.message_reader:
                button_manager.set_message_reader(self.message_reader)
                logging.info("MESSAGE_SYSTEM: ✅ ButtonManager configurado con MessageReader")
            else:
                logging.error("MESSAGE_SYSTEM: ❌ Error configurando ButtonManager")
            
            # 7. Iniciar polling de mensajes
            logging.info("MESSAGE_SYSTEM: Paso 7 - Iniciando polling de mensajes...")
            if self.message_receiver:
                self.message_receiver.start_polling()
                # Pequeña pausa para permitir que el hilo inicie
                time.sleep(0.1)
                if hasattr(self.message_receiver, 'is_running') and self.message_receiver.is_running:
                    logging.info("MESSAGE_SYSTEM: ✅ Polling de mensajes iniciado correctamente")
                else:
                    logging.error("MESSAGE_SYSTEM: ❌ Error al iniciar polling - thread no corriendo")
                    return
            else:
                logging.error("MESSAGE_SYSTEM: ❌ No se puede iniciar polling sin MessageReceiver")
                return
            
            # 8. Verificar mensajes perdidos al iniciar
            logging.info("MESSAGE_SYSTEM: Paso 8 - Verificando mensajes perdidos...")
            if self.message_notifier:
                self.message_notifier.check_missed_notifications()
                logging.info("MESSAGE_SYSTEM: ✅ Verificación de mensajes perdidos completada")
            
            logging.info("MESSAGE_SYSTEM: 🎉 Sistema de mensajes bidireccional inicializado correctamente")
            
        except Exception as e:
            import traceback
            logging.error(f"MESSAGE_SYSTEM: ❌ Error crítico inicializando sistema de mensajes: {e}")
            logging.error(f"MESSAGE_SYSTEM: Traceback: {traceback.format_exc()}")
            # Asegurar que variables estén definidas para evitar errores
            self.message_receiver = None
            self.message_reader = None
            self.message_notifier = None

    def reload_voice_setting(self):
        logging.info("SETTINGS_CHECKER: Se detectó cambio de voz.")
        service = get_reminders_service()
        self.selected_voice = service.get_setting('voice_name', self.selected_voice)
        tts_manager.say("Voz actualizada.", self.selected_voice)

    def reload_scheduler(self):
        logging.info("SETTINGS_CHECKER: Se detectó cambio en recordatorios.")
        self.update_scheduler()
        tts_manager.say("Recordatorios actualizados.", self.selected_voice)
    
    def handle_user_change(self, user_change_info):
        """Maneja el cambio de usuario desde la interfaz web."""
        try:
            if '→' in user_change_info:
                previous_user, new_user = user_change_info.split('→')
                logging.info(f"USER_CHANGE: Cambiando de {previous_user} a {new_user}")
                
                # Actualizar nombre del usuario actual
                previous_name = self.current_user_name
                self.current_user_name = get_current_user_name()
                logging.info(f"USER_CHANGE: Nombre actualizado de '{previous_name}' a '{self.current_user_name}'")
                
                # Recargar contexto de usuario en RouterCentral para cargar nuevas preferencias
                if self.router_central:
                    logging.info("USER_CHANGE: Recargando contexto de usuario en RouterCentral")
                    try:
                        # Usar recarga de contexto más eficiente en lugar de reinicialización completa
                        self.router_central.reload_user_context()
                        logging.info("USER_CHANGE: Contexto de usuario recargado exitosamente")
                    except Exception as e:
                        logging.error(f"USER_CHANGE: Error recargando contexto, reinicializando: {e}")
                        # Fallback a reinicialización completa si falla la recarga
                        self.initialize_router_central()
                
                # Recargar configuración de voz
                service = get_reminders_service()
                self.selected_voice = service.get_setting('voice_name', self.selected_voice)
                
                # Recargar scheduler con datos del nuevo usuario
                self.update_scheduler()
                
                # Notificar al usuario con su nombre real
                tts_manager.say(f"Hola {self.current_user_name}, ahora estoy configurado para ti.", self.selected_voice)
                
                logging.info(f"USER_CHANGE: Cambio completado exitosamente a {self.current_user_name}")
                
            else:
                logging.warning(f"USER_CHANGE: Formato inválido: {user_change_info}")
                
        except Exception as e:
            logging.error(f"USER_CHANGE: Error manejando cambio de usuario: {e}")

    def start_wakeword_thread(self):
        if hasattr(self, 'wakeword_thread') and self.wakeword_thread.is_alive(): return
        self.wakeword_thread = threading.Thread(target=wakeword_detector.listen_for_wake_word, args=(self.on_wakeword_detected,), daemon=True, name="WakeWordThread")
        self.wakeword_thread.start()
        self.clock_interface.update_status("Lista para ayudar. Di 'Catalina'.")

    def on_wakeword_detected(self):
        """Función cuando se detecta la palabra clave"""
        if self.is_speaking_or_listening.locked(): 
            return  # Ignorar si hay operación en curso
        
        # Procesar inmediatamente sin esperar logging
        self.after(0, self.handle_conversation)
        
        # Log asíncrono DESPUÉS para no bloquear wakeword
        threading.Thread(
            target=lambda: firestore_logger.log_interaction("wake_word_detected"),
            daemon=True,
            name="WakewordLoggingThread"
        ).start()

    def on_button_short_press(self):
        """Manejador para pulsación corta."""
        logging.info("BUTTON_MANAGER: Pulsación corta (sin medicamento pendiente - sin acción visible)")

    def on_button_long_press(self):
        """Manejador para pulsación larga (reiniciar app)."""
        if self.medication_confirmation_state == "NORMAL":
            logging.info("BUTTON_MANAGER: Pulsación larga - reiniciando aplicación (cuidadores)")
            tts_manager.say("Reiniciando la aplicación.", self.selected_voice)
            time.sleep(2)
            system_actions.restart_app()
        else:
            logging.info("BUTTON_MANAGER: Pulsación larga ignorada - medicamento pendiente")

    def handle_conversation(self):
        def conversation_task():
            with self.is_speaking_or_listening:
                self.clock_interface.update_status("¡Te escucho!", "#3498DB")
                
                # Mostrar indicador de escucha animado
                self.clock_interface.show_listening_indicator(with_animation=True)
                all_aliases = set()
                service = get_reminders_service()
                for c in service.list_contacts(): all_aliases.update([a.strip() for a in c['aliases'].split(',')])
                
                transcribed_text = stt_manager.stream_audio_and_transcribe(adaptation_phrases=list(all_aliases))
                
                if transcribed_text:
                    self.clock_interface.update_status("Procesando...")
                    clean_text = transcribed_text.lower().replace("catalina", "").strip(".,¿?¡! ")
                    self.process_command(clean_text)
                else:
                    self.clock_interface.update_status("No entendí.")
                    tts_manager.say("No te entendí bien.", self.selected_voice)
            
            # Ocultar indicador de escucha al terminar la conversación
            self.clock_interface.hide_listening_indicator()
            
            # Reiniciar wake word después de completar conversación
            self.start_wakeword_thread()
        
        threading.Thread(target=conversation_task, daemon=True).start()
    
    def _handle_message_command(self, result: dict):
        """Maneja comandos de mensaje procesados por IA especializada"""
        try:
            telegram_data = result.get('telegram_data')
            confirmation_message = result.get('response', '')
            
            if not telegram_data:
                # Solo confirmación sin datos para enviar
                if confirmation_message:
                    tts_manager.say(confirmation_message, self.selected_voice)
                return
            
            # Envío directo sin confirmación (simplificado para adultos mayores)
            success = self._send_telegram_message(telegram_data)
            
            if success:
                tts_manager.say("Mensaje enviado.", self.selected_voice)
                logger.info("MESSAGE_COMMAND: Mensaje enviado exitosamente")
                
                # Log asíncrono de mensaje enviado con más detalles
                def _log_message_sent_async():
                    firestore_logger.log_interaction("message_sent", details={
                        'command': telegram_data.get('original_command', ''),
                        'type': telegram_data.get('type', 'individual'),
                        'recipient_count': len(telegram_data.get('contacts', [])) if telegram_data.get('type') == 'broadcast' else 1,
                        'message_length': len(telegram_data.get('message_content', '')),
                        'send_method': 'voice_command',
                        'sent_at': datetime.now().isoformat()
                    })
                
                threading.Thread(target=_log_message_sent_async, daemon=True).start()
            else:
                tts_manager.say("Hubo un error enviando el mensaje.", self.selected_voice)
                logger.error("MESSAGE_COMMAND: Error enviando mensaje")
            
        except Exception as e:
            logger.error(f"MESSAGE_COMMAND: Error manejando comando: {e}")
            tts_manager.say("Hubo un error procesando el comando de mensaje.", self.selected_voice)
    
    def _send_telegram_message(self, telegram_data: dict) -> bool:
        """Envía mensaje por Telegram usando los datos procesados"""
        try:
            message_type = telegram_data.get('type', 'individual')
            message_content = telegram_data.get('message', '')
            
            if message_type == 'broadcast':
                # Enviar a múltiples contactos
                contacts = telegram_data.get('contacts', [])
                success_count = 0
                
                for contact in contacts:
                    try:
                        chat_id = contact.get('contact_details', '')
                        if chat_id:
                            # Usar voice_message_sender para envío
                            if hasattr(self, 'voice_message_sender') and self.voice_message_sender:
                                if self.voice_message_sender._send_telegram_message(chat_id, message_content):
                                    success_count += 1
                                    logger.debug(f"MESSAGE_SEND: Enviado a {contact.get('display_name', 'contacto')}")
                                else:
                                    logger.error(f"MESSAGE_SEND: Fallo enviando a {contact.get('display_name', 'contacto')}")
                            else:
                                logger.error("MESSAGE_SEND: voice_message_sender no disponible")
                    except Exception as e:
                        logger.error(f"MESSAGE_SEND: Error enviando a {contact.get('display_name', 'contacto')}: {e}")
                
                logger.info(f"MESSAGE_SEND: Broadcast enviado a {success_count}/{len(contacts)} contactos")
                return success_count > 0
                
            else:
                # Enviar a contacto individual
                contact = telegram_data.get('contact', {})
                chat_id = contact.get('contact_details', '')
                
                if chat_id:
                    # Usar voice_message_sender para envío
                    if hasattr(self, 'voice_message_sender') and self.voice_message_sender:
                        if self.voice_message_sender._send_telegram_message(chat_id, message_content):
                            logger.info(f"MESSAGE_SEND: Enviado a {contact.get('display_name', 'contacto')}")
                            return True
                        else:
                            logger.error(f"MESSAGE_SEND: Fallo enviando a {contact.get('display_name', 'contacto')}")
                            return False
                    else:
                        logger.error("MESSAGE_SEND: voice_message_sender no disponible")
                        return False
                else:
                    logger.error("MESSAGE_SEND: No se encontró chat_id del contacto")
                    return False
            
        except Exception as e:
            logger.error(f"MESSAGE_SEND: Error enviando mensaje Telegram: {e}")
            return False

    def process_command(self, text: str):
        # Usar RouterCentral si está disponible, sino fallback al sistema clásico
        if self.router_central:
            try:
                result = self.router_central.process_user_input(text)
                
                if result.get('success', False):
                    intent = result.get('intent')
                    response = result.get('response')
                    route = result.get('route')
                    
                    # Manejar intents específicos ANTES que respuesta genérica
                    if intent == 'processing_message':
                        # Dar feedback inmediato y procesar en background
                        if response:
                            tts_manager.say(response, self.selected_voice)
                        
                        # Ejecutar procesamiento en background
                        if result.get('requires_background_processing') and result.get('background_task'):
                            background_result = result['background_task']()
                            self._handle_message_command(background_result)
                        return
                    elif intent == 'send_message':
                        # Comandos de mensaje - VoiceMessageSender maneja su propio TTS
                        # Solo reproducir audio si no es silencioso
                        if not result.get('silent') and response:
                            tts_manager.say(response, self.selected_voice)
                        return
                    elif intent in ['message_info', 'message_error', 'system_error', 'send_message_error']:
                        # Respuestas de información de mensajes y errores
                        if response:
                            tts_manager.say(response, self.selected_voice)
                        return
                    elif result.get('requires_classic_execution') and intent:
                        # RouterCentral detectó intent clásico que requiere ejecución
                        logging.info(f"RouterCentral solicita ejecución clásica para: {intent}")
                        # El intent ya está extraído, continuar con procesamiento clásico abajo
                        pass
                    # Para respuestas generativas (incluye fallback), usar STREAMING TTS  
                    elif response:
                        # Verificar comando de apagado desde respuesta instantánea o texto original
                        if self._is_shutdown_command(response) or self._is_shutdown_command(text):
                            self._handle_shutdown_device()
                        else:
                            # Usar streaming end-to-end: Gemini stream → TTS stream
                            self._handle_streaming_response(text, route)
                            
                            # Log asíncrono DESPUÉS de iniciar la respuesta
                            self._log_interaction_async(text, result, route, intent)
                        return
                    else:
                        # Para otros casos de ruta clásica, procesar intent como antes
                        pass
                else:
                    # Error en router, usar fallback
                    logging.warning(f"RouterCentral falló: {result.get('error')}")
                    intent = intent_manager.parse_intent(text)
            except Exception as e:
                logging.error(f"Error en RouterCentral: {e}")
                intent = intent_manager.parse_intent(text)
        else:
            # Fallback al sistema clásico original
            intent = intent_manager.parse_intent(text)
        
        # Procesar intents clásicos
        if intent == "EMERGENCY_ALERT": self.on_button_pressed(from_voice=True)
        elif intent == "CONTACT_PERSON": self._handle_specific_contact(text)
        elif intent == "PLUG_ON": self._handle_plug_on()
        elif intent == "PLUG_OFF": self._handle_plug_off()
        elif intent == "GET_DATE": self._handle_get_date()
        elif intent == "GET_TIME": self._handle_get_time()
        elif intent == "CREATE_REMINDER": self._handle_create_reminder_direct(text)
        elif intent == "CREATE_DAILY_REMINDER": self._handle_create_daily_reminder(text)
        elif intent == "LIST_REMINDERS": self._handle_list_reminders()
        elif intent == "DELETE_REMINDER": self._handle_delete_reminder(text)
        elif intent == "READ_MESSAGES": self._handle_read_messages()
        elif intent == "SEND_MESSAGE": self._handle_send_message(text)
        elif intent == "SHUTDOWN_DEVICE": self._handle_shutdown_device()
        else:
            if text:
                if ENABLE_AI_GENERATIVE and ROUTER_AVAILABLE:
                    # IA Generativa habilitada - usar RouterCentral
                    firestore_logger.log_interaction("ai_query", details={'transcription': text})
                    # Verificar si es comando de apagado desde respuesta instantánea
                    if self._is_shutdown_command(text):
                        self._handle_shutdown_device()
                    else:
                        # Usar STREAMING end-to-end para IA generativa
                        self._handle_streaming_response(text)
                else:
                    # IA Generativa deshabilitada
                    firestore_logger.log_interaction("command_not_understood", details={'transcription': text})
                    tts_manager.say("Comando no reconocido. Intenta con comandos específicos como 'qué hora es', 'recuérdame algo', o 'enciende el enchufe'.", self.selected_voice)

    def announce_reminder(self, reminder_info):
        """Sistema unificado de confirmación de medicamentos con pantalla azul (5 minutos)."""
        with self.is_speaking_or_listening:
            firestore_logger.log_interaction("reminder_triggered", details={'type': 'medication', 'name': reminder_info['medication_name']})
            
            # Iniciar sistema unificado
            self.start_medication_alert(reminder_info)

    def announce_task(self, task_info):
        with self.is_speaking_or_listening:
            firestore_logger.log_interaction("reminder_triggered", details={'type': 'task', 'name': task_info['task_name']})
            
            logging.info(f"Ejecutando tarea: {task_info['task_name']}")
            # Para tareas, solo damos el aviso de voz, no mostramos nada en pantalla.
            tts_manager.say(f"Recordatorio de tarea. Es hora de {task_info['task_name']}", self.selected_voice)

    # ==============================================
    # SISTEMA UNIFICADO DE CONFIRMACIÓN DE MEDICAMENTOS (PANTALLA AZUL - 5 MIN)
    # ==============================================
    
    def start_medication_alert(self, medication_info):
        """Sistema unificado: Pantalla azul con toda la información (5 minutos)."""
        logging.info(f"MEDICATION: Iniciando alerta unificada para {medication_info['medication_name']}")
        
        # Actualizar estado
        self.medication_confirmation_state = "MEDICATION_ACTIVE"
        self.current_medication_info = medication_info
        
        # Cancelar timers previos si existen
        self._cancel_medication_timers()
        
        # Configurar botón para confirmación
        button_manager.set_medication_confirmation_mode(self.handle_medication_confirmed)
        
        # Mostrar pantalla azul unificada
        self.clock_interface.show_medication_alert(medication_info)
        
        # Crear mensaje de audio mejorado
        audio_message = self._create_medication_audio_message(medication_info)
        tts_manager.say(audio_message, self.selected_voice)
        
        # Timer para repetición del mensaje (4 minutos = 240 segundos)
        self.medication_repeat_timer = threading.Timer(240, self._repeat_medication_message)
        self.medication_repeat_timer.start()
        
        # Timer para timeout (5 minutos total)
        self.medication_timer = threading.Timer(MEDICATION_TIMEOUT, self.handle_medication_timeout)
        self.medication_timer.start()
        
        logging.info(f"MEDICATION: Alerta unificada iniciada - timer de {MEDICATION_TIMEOUT}s activado, repetición en 240s")

    def _create_medication_audio_message(self, medication_info):
        """Crea un mensaje de audio específico según requerimientos."""
        cantidad = medication_info.get('cantidad', '')
        medicamento = medication_info['medication_name']
        prescripcion = medication_info.get('prescripcion', '')
        
        # Mensaje base: "Es hora de tomarte [cantidad] de [medicamento]"
        if cantidad:
            base_message = f"Es hora de tomarte {cantidad} de {medicamento}"
        else:
            base_message = f"Es hora de tomarte {medicamento}"
        
        # Agregar prescripción si está disponible
        if prescripcion:
            base_message += f" y {prescripcion}"
        
        # Agregar instrucción de confirmación
        base_message += ". Presiona el botón para confirmar que escuchaste el recordatorio y tomarás el medicamento"
        
        return base_message
    
    def _repeat_medication_message(self):
        """Repite el mensaje de voz automáticamente 1 minuto antes del timeout."""
        # Verificar si todavía estamos en estado de medicamento
        if self.medication_confirmation_state != "MEDICATION_ACTIVE":
            logging.info("MEDICATION: Repetición cancelada - medicamento ya confirmado")
            return
        
        if self.current_medication_info:
            logging.info("MEDICATION: Repitiendo mensaje de voz automáticamente")
            audio_message = self._create_medication_audio_message(self.current_medication_info)
            tts_manager.say(audio_message, self.selected_voice)

    def handle_medication_confirmed(self):
        """Manejador cuando el usuario presiona el botón para confirmar medicamento."""
        # Verificar si estamos en modo de confirmación de medicamento
        if self.medication_confirmation_state == "NORMAL":
            logging.info("MEDICATION: Confirmación ignorada - no hay medicamento pendiente")
            return
            
        medication_name = self.current_medication_info['medication_name'] if self.current_medication_info else "medicamento"
        logging.info(f"MEDICATION: Confirmación recibida para {medication_name}")
        
        # Cancelar timer
        self._cancel_medication_timers()
        
        # Logging asíncrono de confirmación con método de confirmación
        def _log_medication_confirmation_async():
            firestore_logger.log_interaction("medication_confirmed", details={
                'medication_name': medication_name,
                'user_name': self.current_user_name,
                'confirmation_method': 'button',  # Confirmado vía botón
                'confirmed_at': datetime.now().isoformat()
            })
        
        threading.Thread(target=_log_medication_confirmation_async, daemon=True).start()
        
        # Feedback de voz
        tts_manager.say("Medicamento confirmado", self.selected_voice)
        
        # Mostrar pantalla verde por 2 segundos antes de volver al reloj
        self.clock_interface.show_medication_success()
        
        # Resetear estado
        self._reset_medication_state()

    def handle_medication_timeout(self):
        """Manejador cuando pasan los 5 minutos totales sin confirmación."""
        # Verificar si todavía estamos en estado de medicamento (evitar timeouts duplicados)
        if self.medication_confirmation_state == "NORMAL":
            logging.info("MEDICATION: Timeout cancelado - medicamento ya fue confirmado")
            return
            
        medication_name = self.current_medication_info['medication_name'] if self.current_medication_info else "medicamento"
        logging.warning(f"MEDICATION: Timeout para {medication_name} - enviando alerta de emergencia")
        
        # Logging de timeout
        firestore_logger.log_interaction("medication_timeout_alert", details={
            'medication_name': medication_name,
            'user_name': self.current_user_name,
            'timeout_minutes': MEDICATION_TIMEOUT / 60
        })
        
        # Enviar alerta a contactos de emergencia usando voice_message_sender
        try:
            if hasattr(self, 'voice_message_sender') and self.voice_message_sender:
                success = self.voice_message_sender.send_medication_timeout_alert(medication_name, self.current_user_name)
                if success:
                    logging.info("MEDICATION: Alerta de medicamento enviada exitosamente")
                else:
                    logging.warning("MEDICATION: No se pudo enviar alerta de medicamento")
            else:
                logging.warning("MEDICATION: Sistema de mensajes no disponible para alertas")
        except Exception as e:
            logging.error(f"MEDICATION: Error enviando alerta de medicación: {e}")
        
        # Mostrar pantalla roja por 2 segundos antes de volver al reloj
        self.after(0, lambda: self.clock_interface.show_medication_timeout_alert())
        
        # Resetear estado
        self._reset_medication_state()

    def _cancel_medication_timers(self):
        """Cancela todos los timers de medicamento activos."""
        if self.medication_timer and self.medication_timer.is_alive():
            self.medication_timer.cancel()
            self.medication_timer = None
            logging.info("MEDICATION: Timer principal cancelado")
        
        if hasattr(self, 'medication_repeat_timer') and self.medication_repeat_timer and self.medication_repeat_timer.is_alive():
            self.medication_repeat_timer.cancel()
            self.medication_repeat_timer = None
            logging.info("MEDICATION: Timer de repetición cancelado")

    def _reset_medication_state(self):
        """Resetea el estado del sistema de confirmación de medicamentos."""
        self.medication_confirmation_state = "NORMAL"
        self.current_medication_info = None
        button_manager.exit_medication_confirmation_mode()
        logging.info("MEDICATION: Estado reseteado a NORMAL")

    # ==============================================
    # FIN DEL SISTEMA UNIFICADO DE CONFIRMACIÓN DE MEDICAMENTOS
    # ==============================================

    def _handle_send_message(self, text: str):
        """Maneja comandos de envío de mensajes usando VoiceMessageSender"""
        try:
            if hasattr(self, 'voice_message_sender') and self.voice_message_sender:
                # Usar el current_user_name si está disponible
                user_name = getattr(self, 'current_user_name', 'Marina')
                
                logging.info(f"SEND_MESSAGE: Procesando mensaje de voz: '{text}' para usuario: {user_name}")
                success = self.voice_message_sender.process_voice_message(text, user_name)
                
                if success:
                    logging.info("SEND_MESSAGE: Mensaje procesado exitosamente")
                else:
                    logging.warning("SEND_MESSAGE: Error procesando mensaje")
                    tts_manager.say("Hubo un problema enviando el mensaje", self.selected_voice)
            else:
                logging.error("SEND_MESSAGE: voice_message_sender no disponible")
                tts_manager.say("Sistema de mensajes no disponible", self.selected_voice)
                
        except Exception as e:
            logging.error(f"SEND_MESSAGE: Error en _handle_send_message: {e}")
            tts_manager.say("Error procesando el comando de mensaje", self.selected_voice)

    def update_scheduler(self):
        if self.scheduler.running: self.scheduler.remove_all_jobs()
        
        # Programar recordatorios de medicamentos
        service = get_reminders_service()
        all_reminders = service.list_reminders()
        for rem in all_reminders:
            try:
                days = rem['days_of_week']
                for t in rem['times'].split(','):
                    hour, minute = map(int, t.strip().split(':'))
                    self.scheduler.add_job(self.announce_reminder, 'cron', day_of_week=days, hour=hour, minute=minute, args=[rem])
            except Exception as e: logging.error(f"Error al programar recordatorio: {e}")

        # Programar tareas generales
        try:
            service = get_reminders_service()
            all_tasks = service.list_tasks()
            for task in all_tasks:
                try:
                    days = task['days_of_week']
                    for t in task['times'].split(','):
                        hour, minute = map(int, t.strip().split(':'))
                        self.scheduler.add_job(self.announce_task, 'cron', day_of_week=days, hour=hour, minute=minute, args=[task])
                except Exception as e:
                    logging.error(f"Error al programar tarea: {e}")
        except Exception as e:
            logging.warning(f"No se pudieron cargar las tareas (posiblemente la tabla no existe): {e}")
        
        logging.info(f"Programador actualizado con {len(self.scheduler.get_jobs())} trabajos.")

    def _handle_plug_on(self): 
        firestore_logger.log_interaction("command_executed", details={'command': 'plug_on'})
        tts_manager.say("Entendido.", self.selected_voice) if smart_home_manager.set_device_state('enchufe', 'ON') else tts_manager.say("Hubo un error.", self.selected_voice)
    
    def _handle_plug_off(self): 
        firestore_logger.log_interaction("command_executed", details={'command': 'plug_off'})
        tts_manager.say("Claro.", self.selected_voice) if smart_home_manager.set_device_state('enchufe', 'OFF') else tts_manager.say("Hubo un error.", self.selected_voice)
    
    def _handle_get_date(self):
        firestore_logger.log_interaction("command_executed", details={'command': 'get_date'})
        dias=["lunes","martes","miércoles","jueves","viernes","sábado","domingo"];meses=["enero","febrero","marzo","abril","mayo","junio","julio","agosto","septiembre","octubre","noviembre","diciembre"]
        hoy=datetime.now();respuesta=f"Hoy es {dias[hoy.weekday()]}, {hoy.day} de {meses[hoy.month-1]} de {hoy.year}."
        tts_manager.say(respuesta, self.selected_voice)
    
    def _handle_get_time(self): 
        firestore_logger.log_interaction("command_executed", details={'command': 'get_time'})
        hora_texto = self.get_speakable_time(datetime.now())
        tts_manager.say(hora_texto, self.selected_voice)

    def _handle_create_reminder_direct(self, text):
        """Crea recordatorio inmediatamente sin confirmación."""
        firestore_logger.log_interaction("voice_reminder_requested", details={'transcription': text})
        
        reminder_data = voice_reminder_manager.parse_reminder_command(text)
        
        if reminder_data:
            # Verificar si es error de hora pasada
            if isinstance(reminder_data, dict) and reminder_data.get('error') == 'time_passed':
                tts_manager.say(reminder_data['message'], self.selected_voice)
                return
                
            # Crear inmediatamente
            success = voice_reminder_manager.create_reminder_directly(reminder_data)
            if success:
                task = reminder_data['task']
                time_desc = voice_reminder_manager.format_time_description(reminder_data)
                tts_manager.say(f"Recordatorio creado: '{task}' {time_desc}.", self.selected_voice)
                self.reload_scheduler()
                firestore_logger.log_interaction("voice_reminder_created", details={'task': task})
            else:
                tts_manager.say("Hubo un problema al crear el recordatorio. Inténtalo de nuevo.", self.selected_voice)
        else:
            # Mensajes más simples para adultos mayores
            tts_manager.say("No entendí. Dime algo como: recuérdame llamar al doctor a las 3 de la tarde.", self.selected_voice)

    def _handle_create_daily_reminder(self, text):
        """Crea recordatorio diario inmediatamente sin confirmación."""
        firestore_logger.log_interaction("voice_daily_reminder_requested", details={'transcription': text})
        
        # Forzar frecuencia diaria
        reminder_data = voice_reminder_manager.parse_reminder_command(text)
        
        if reminder_data:
            # Forzar frecuencia diaria
            reminder_data['frequency'] = 'daily'
            
            # Crear inmediatamente
            success = voice_reminder_manager.create_reminder_directly(reminder_data)
            if success:
                task = reminder_data['task']
                time_str = f"{reminder_data['hour']:02d}:{reminder_data['minute']:02d}"
                tts_manager.say(f"Recordatorio diario creado: '{task}' todos los días a las {time_str}.", self.selected_voice)
                self.reload_scheduler()
                firestore_logger.log_interaction("voice_daily_reminder_created", details={'task': task})
            else:
                tts_manager.say("Hubo un problema al crear el recordatorio diario. Inténtalo de nuevo.", self.selected_voice)
        else:
            tts_manager.say("No pude entender el recordatorio diario. Por favor, di algo como 'recuérdame todos los días tomar vitaminas a las 8 de la mañana'.", self.selected_voice)

    def _handle_list_reminders(self):
        """Lista todos los recordatorios por voz."""
        firestore_logger.log_interaction("voice_reminders_listed")
        
        reminders_list = voice_reminder_manager.list_voice_reminders()
        response = voice_reminder_manager.format_reminders_list(reminders_list)
        tts_manager.say(response, self.selected_voice)

    def _handle_delete_reminder(self, text):
        """Elimina recordatorios por voz."""
        firestore_logger.log_interaction("voice_reminder_delete_requested", details={'transcription': text})
        
        # Intentar extraer qué recordatorio eliminar
        deletion_result = voice_reminder_manager.delete_reminder_by_voice(text)
        
        if deletion_result['success']:
            tts_manager.say(deletion_result['message'], self.selected_voice)
            self.reload_scheduler()  # Actualizar scheduler
        else:
            tts_manager.say(deletion_result['message'], self.selected_voice)

    def _handle_read_messages(self):
        """Maneja el comando de voz para leer mensajes."""
        try:
            firestore_logger.log_interaction("voice_read_messages_requested")
            
            # Verificar si el sistema de mensajes está disponible
            if hasattr(self, 'message_reader') and self.message_reader:
                if self.message_reader.has_unread_messages():
                    logging.info("VOICE_COMMAND: Iniciando lectura de mensajes por voz")
                    self.message_reader.read_messages_async(max_messages=3)
                else:
                    tts_manager.say("No tienes mensajes nuevos.", self.selected_voice)
                    logging.info("VOICE_COMMAND: No hay mensajes para leer")
            else:
                tts_manager.say("El sistema de mensajes no está disponible.", self.selected_voice)
                logging.warning("VOICE_COMMAND: Sistema de mensajes no inicializado")
                
        except Exception as e:
            logging.error(f"VOICE_COMMAND: Error en lectura de mensajes: {e}")
            tts_manager.say("Hubo un error al leer los mensajes.", self.selected_voice)

    def _handle_shutdown_device(self):
        """Maneja el comando de apagado del dispositivo."""
        firestore_logger.log_interaction("voice_shutdown_requested", details={'command': 'shutdown'})
        logging.info("COMANDO_VOZ: Apagado solicitado por voz")
        
        # Confirmar antes de apagar
        tts_manager.say("Entendido. Apagando el sistema en 5 segundos. Hasta luego.", self.selected_voice)
        
        # Dar tiempo para que termine de hablar
        import threading
        import time
        
        def delayed_shutdown():
            time.sleep(6)  # Esperar 6 segundos (5 + margen para TTS)
            logging.info("SISTEMA: Ejecutando apagado...")
            system_actions.shutdown_pi()
        
        # Ejecutar apagado en hilo separado
        shutdown_thread = threading.Thread(target=delayed_shutdown, daemon=True)
        shutdown_thread.start()

    def _is_shutdown_command(self, text: str) -> bool:
        """Verifica si el texto es un comando de apagado"""
        text_lower = text.lower().strip()
        
        # Verificar comando especial de respuesta instantánea
        if text_lower == "comando_shutdown":
            return True
        
        # Verificar frases de apagado normales
        shutdown_phrases = ["apagate", "apágate", "apaga te", "apaga el dispositivo", "apagar sistema", "apagar el sistema"]
        return any(phrase in text_lower for phrase in shutdown_phrases)
        
    def _handle_specific_contact(self, text):
        firestore_logger.log_interaction("command_executed", details={'command': 'contact_person'})
        
        service = get_reminders_service()
        target = next((c for c in service.list_contacts() for alias in c['aliases'].split(',') if alias.strip() in text), None)
        if target:
            msg = f"Hola, Kata se quiere contactar contigo, {target['display_name']}."
            # TODO: Usar sistema de mensajes moderno
            tts_manager.say(f"Enviando aviso a {target['display_name']}.", self.selected_voice)
        else: tts_manager.say("No encontré a esa persona.", self.selected_voice)
        
    def on_button_pressed(self, from_voice=False):
        def emergency_task():
            if self.is_speaking_or_listening.locked(): return
            if not from_voice:
                self.wakeword_thread.join(timeout=1.0)

            with self.is_speaking_or_listening:
                user_name = self.current_user_name
                message = f"🚨 *ALERTA DE EMERGENCIA* 🚨\nSe ha solicitado ayuda para *{user_name}*."
                service = get_reminders_service()
                ayuda = next((c for c in service.list_contacts() if c.get('is_emergency') == 1), None)
                if ayuda:
                    # TODO: Usar sistema de mensajes moderno para emergencias
                    tts_manager.say("Sistema de emergencia pendiente de actualización.", self.selected_voice)
                    logging.warning("EMERGENCY: Sistema de emergencias obsoleto - contactar soporte técnico")
                else: tts_manager.say("Error: No hay contacto de emergencia configurado.", self.selected_voice)
            
            if not from_voice: self.start_wakeword_thread()
        
        threading.Thread(target=emergency_task, daemon=True).start()

    def toggle_mode(self, event=None):
        self.admin_mode = not self.admin_mode
        if self.admin_mode: 
            self.main_container.grid_forget()
            self.admin_container.grid(row=0, column=0, sticky="nsew")
            # Modo admin activo
        else: 
            self.admin_container.grid_forget()
            self.main_container.grid(row=0, column=0, sticky="nsew")
            # Modo reloj activo

    def _handle_streaming_response(self, user_text: str, route: str = None):
        """Maneja respuestas con streaming end-to-end: Gemini → TTS"""
        # Verificar si es comando de apagado antes del streaming
        if self._is_shutdown_command(user_text):
            self._handle_shutdown_device()
            return
            
        if self.is_streaming:
            logging.warning("Ya hay un streaming activo, ignorando nueva solicitud")
            return
        
        def streaming_worker():
            self.is_streaming = True
            try:
                logging.info(f"STREAMING: Iniciando para '{user_text[:30]}...'")
                
                # Filler contextual inmediato
                filler = tts_manager.get_contextual_filler(user_text)
                if filler:
                    tts_manager.say(filler, self.selected_voice)
                    logging.info(f"STREAMING: Filler reproducido: '{filler}'")
                
                # Iniciar streaming de respuesta
                if hasattr(self.router_central.generative_route, 'process_query_streaming'):
                    # Usar streaming nativo del GenerativeRoute
                    chunks_generator = self.router_central.generative_route.process_query_streaming(user_text)
                    
                    # Streaming TTS end-to-end
                    tts_manager.stream_speak_text(chunks_generator, self.selected_voice)
                    
                    logging.info("STREAMING: Completado exitosamente")
                else:
                    # Fallback a método no streaming
                    logging.warning("STREAMING: No disponible, usando método clásico")
                    result = self.router_central.process_user_input(user_text)
                    response = result.get('response', 'No se pudo procesar la consulta')
                    tts_manager.speak_with_immediate_feedback(response, self.selected_voice, user_text)
                
            except Exception as e:
                logging.error(f"STREAMING: Error: {e}")
                # Fallback de emergencia
                tts_manager.say("Disculpe, hubo un problema procesando su consulta.", self.selected_voice)
            
            finally:
                self.is_streaming = False
        
        # Ejecutar streaming en hilo separado para no bloquear UI
        streaming_thread = threading.Thread(target=streaming_worker, daemon=True)
        streaming_thread.start()

    def on_closing(self):
        logging.info("DEBUG: on_closing() llamado - SOLO cerrando aplicación, NO apagando sistema")
        if self.scheduler.running: self.scheduler.shutdown()
        wakeword_detector.stop_listening()
        
        # Detener sistema de mensajes
        if hasattr(self, 'message_receiver') and self.message_receiver:
            self.message_receiver.stop_polling()
        
        # Detener streaming si está activo
        if self.is_streaming:
            tts_manager.stop_streaming()
        
        logging.info("DEBUG: Cerrando aplicación con destroy()")
        self.destroy()
    
    def _log_interaction_async(self, text: str, result: dict, route: str, intent: str):
        """Log asíncrono de interacciones a Firestore (no bloquea respuesta)"""
        def _async_interaction_log():
            try:
                # Log apropiado según el tipo de respuesta
                if route in ['generative', 'generative_personalized']:
                    log_type = "ai_query_personalized" if route == 'generative_personalized' else "ai_query"
                    firestore_logger.log_interaction(log_type, details={
                        'transcription': text,
                        'route': route,
                        'intent': intent,
                        'personalization': result.get('router_metadata', {}).get('personalization', {})
                    })
                elif route == 'generative_fallback':
                    firestore_logger.log_interaction("command_not_understood", details={
                        'transcription': text,
                        'route': route,
                        'fallback_reason': 'generative_api_error'
                    })
                
                logging.debug("Interaction logging completado asíncronamente")
                
            except Exception as log_error:
                # No fallar si hay error en logging asíncrono
                logging.warning(f"Error en logging asíncrono de interacción: {log_error}")
        
        # Ejecutar en thread separado para no bloquear
        thread = threading.Thread(target=_async_interaction_log, daemon=True)
        thread.start()
        logging.debug("Interaction logging iniciado asíncronamente")

# Función para inicializar la aplicación
def initialize_app():
    """Inicializa la aplicación principal"""
    # Inicializar base de datos con sistema multi-usuario
    if MULTI_USER_AVAILABLE:
        logging.info("Inicializando sistema multi-usuario")
        # El adaptador se encarga de la inicialización automáticamente
    else:
        logging.info("Inicializando sistema legacy")
        reminders.init_db()
    
    return KataApp()

def run_app():
    """Ejecuta la aplicación principal"""
    app = initialize_app()
    app.mainloop()

if __name__ == '__main__':
    run_app()