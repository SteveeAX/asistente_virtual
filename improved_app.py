import customtkinter as ctk
import threading, queue, logging, time, os, sys
from apscheduler.schedulers.background import BackgroundScheduler
from datetime import datetime

# --- Módulos del Proyecto ---
import reminders, tts_manager, stt_manager, intent_manager, wakeword_detector, button_manager, emergency_manager, smart_home_manager, gemini_manager, firestore_logger, system_actions

# --- Módulos de IA Generativa ---
# Agregar directorio modules al path para importaciones
modules_path = os.path.join(os.path.dirname(__file__), 'modules')
if modules_path not in sys.path:
    sys.path.insert(0, modules_path)

# Importar RouterCentral con manejo de errores
try:
    from generative.router_central import RouterCentral
    ROUTER_AVAILABLE = True
    logging.info("ROUTER: RouterCentral importado correctamente")
except ImportError as e:
    ROUTER_AVAILABLE = False
    logging.warning(f"ROUTER: RouterCentral no disponible: {e}")
from contact_tab_updated import ContactTab
from reminder_tab_updated import ReminderTab
from clock_interface import ClockInterface
from voice_reminder_manager import voice_reminder_manager

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(threadName)s - %(name)s - %(message)s')
SETTINGS_FLAG_PATH = os.path.join(os.path.dirname(__file__), "settings_updated.flag")

# Configuraciones globales  
ENABLE_AI_GENERATIVE = False     # Flag para IA generativa

# Configuraciones del sistema unificado de confirmación de medicamentos
MEDICATION_TIMEOUT = 300  # 5 minutos totales (sistema unificado)
USER_NAME = "Usuario"  # Nombre del usuario para alertas

class KataApp(ctk.CTk):
    def __init__(self):
        super().__init__()
        self.title("Asistente Kata")
        self.attributes('-fullscreen', True)
        ctk.set_appearance_mode("Dark")

        # --- Atributos de la aplicación ---
        self.selected_voice = reminders.get_setting('voice_name', 'es-US-Neural2-A')
        self.is_speaking_or_listening = threading.Lock()
        self.admin_mode = False
        
        # --- RouterCentral para IA Generativa ---
        self.router_central = None
        
        # --- Estado del sistema unificado de confirmación de medicamentos ---
        self.medication_confirmation_state = "NORMAL"  # NORMAL, MEDICATION_ACTIVE
        self.current_medication_info = None
        self.medication_timer = None

        
        # Cargar tema guardado (por defecto oscuro)
        saved_theme = reminders.get_setting('app_theme', 'dark')
        self.is_light_theme = (saved_theme == 'light')

        # --- Configuración de la UI ---
        self.grid_rowconfigure(0, weight=1); self.grid_columnconfigure(0, weight=1)
        
        # Aplicar tema inicial antes de crear los contenedores
        if self.is_light_theme:
            ctk.set_appearance_mode("Light")
            container_color = "white"
        else:
            ctk.set_appearance_mode("Dark")
            container_color = "black"
            
        self.main_container = ctk.CTkFrame(self, fg_color=container_color)
        self.admin_container = ctk.CTkFrame(self)
        self.main_container.grid(row=0, column=0, sticky="nsew")
        
        # Crear el ClockInterface y aplicar tema inicial
        self.clock_interface = ClockInterface(self.main_container)
        self.clock_interface.update_theme(self.is_light_theme)
        
        # --- BOTÓN DE TEMA EN EL CONTENEDOR PRINCIPAL ---
        # Configurar botón según el tema inicial
        if self.is_light_theme:
            button_text = "🌙 TEMA"
            button_fg = "gray80"
            button_hover = "gray70"
            button_text_color = "black"
        else:
            button_text = "☀️ TEMA"
            button_fg = "gray20"
            button_hover = "gray30"
            button_text_color = "white"
            
        self.theme_button = ctk.CTkButton(
            self.main_container,
            text=button_text,
            width=100,
            height=50,
            font=ctk.CTkFont(size=16, weight="bold"),
            command=self.toggle_global_theme,
            fg_color=button_fg,
            hover_color=button_hover,
            text_color=button_text_color,
            corner_radius=25
        )
        # Posicionar en la esquina superior derecha
        self.theme_button.place(relx=0.98, rely=0.02, anchor="ne")
        
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

    def toggle_global_theme(self):
        """Cambiar el tema global de la aplicación"""
        self.is_light_theme = not self.is_light_theme
        
        # Guardar la preferencia de tema
        theme_value = 'light' if self.is_light_theme else 'dark'
        reminders.set_setting('app_theme', theme_value)
        
        if self.is_light_theme:
            ctk.set_appearance_mode("Light")
            self.main_container.configure(fg_color="white")
            self.admin_container.configure(fg_color="white")
            # Actualizar botón para tema claro
            self.theme_button.configure(
                text="🌙 TEMA",
                fg_color="gray80",
                hover_color="gray70",
                text_color="black"
            )
        else:
            ctk.set_appearance_mode("Dark")
            self.main_container.configure(fg_color="black")
            self.admin_container.configure(fg_color="black")
            # Actualizar botón para tema oscuro
            self.theme_button.configure(
                text="☀️ TEMA",
                fg_color="gray20",
                hover_color="gray30",
                text_color="white"
            )
        
        # Actualizar el reloj interface
        self.clock_interface.update_theme(self.is_light_theme)
        
        logging.info(f"Tema cambiado y guardado: {'Claro' if self.is_light_theme else 'Oscuro'}")
        print(f"Tema cambiado a: {'Claro' if self.is_light_theme else 'Oscuro'}")

    # <--- CAMBIO: Función de hora humanizada ---
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
    # --- FIN DEL CAMBIO ---

    def setup_admin_view(self):
        tab_view = ctk.CTkTabview(self.admin_container); tab_view.pack(fill="both", expand=True, padx=10, pady=10)
        tab_view.add("Recordatorios"); tab_view.add("Contactos")
        self.reminder_tab = ReminderTab(tab_view.tab("Recordatorios"), self)
        self.contact_tab = ContactTab(tab_view.tab("Contactos"), self)
        ctk.CTkButton(self.admin_container, text="Volver a Modo Reloj", command=self.toggle_mode).pack(side="bottom", pady=10)

    def initialize_backend_threads(self):
        wakeword_detector.init_porcupine()
        gemini_manager.start_new_chat_session()
        
        # --- Inicializar RouterCentral ---
        self.initialize_router_central()
        
        self.start_wakeword_thread()
        threading.Thread(target=button_manager.start_button_listener, args=(
            self.on_button_short_press,
            self.on_button_long_press,
            self.on_button_triple_press
        ), daemon=True, name="ButtonThread").start()
        threading.Thread(target=self.settings_checker, daemon=True, name="SettingsCheckerThread").start()

    def settings_checker(self):
        while True:
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

    def reload_voice_setting(self):
        logging.info("SETTINGS_CHECKER: Se detectó cambio de voz.")
        self.selected_voice = reminders.get_setting('voice_name', self.selected_voice)
        tts_manager.say("Voz actualizada.", self.selected_voice)

    def reload_scheduler(self):
        logging.info("SETTINGS_CHECKER: Se detectó cambio en recordatorios.")
        self.update_scheduler()
        tts_manager.say("Recordatorios actualizados.", self.selected_voice)

    def start_wakeword_thread(self):
        if hasattr(self, 'wakeword_thread') and self.wakeword_thread.is_alive(): return
        self.wakeword_thread = threading.Thread(target=wakeword_detector.listen_for_wake_word, args=(self.on_wakeword_detected,), daemon=True, name="WakeWordThread")
        self.wakeword_thread.start()
        self.clock_interface.update_status("Lista para ayudar. Di 'Catalina'.")

    def on_wakeword_detected(self):
        # --- AÑADIR ESTA LÍNEA ---
        firestore_logger.log_interaction("wake_word_detected")
        
        self.after(0, self.handle_conversation)

    # --- Nuevas funciones para manejar los eventos del botón ---
    def on_button_short_press(self):
        """
        Manejador para pulsación corta - YA NO ES EMERGENCIA.
        Solo funciona para cuidadores cuando no hay medicamento pendiente.
        """
        # Esta función ya no hace nada visible para adultos mayores
        # Solo logging para cuidadores/técnicos
        logging.info("BUTTON_MANAGER: Pulsación corta (sin medicamento pendiente - sin acción visible)")

    def on_button_long_press(self):
        """
        Manejador para pulsación larga (SOLO CUIDADORES - reiniciar app).
        Solo funciona cuando NO hay medicamento pendiente.
        """
        if self.medication_confirmation_state == "NORMAL":
            logging.info("BUTTON_MANAGER: Pulsación larga - reiniciando aplicación (cuidadores)")
            tts_manager.say("Reiniciando la aplicación.", self.selected_voice)
            time.sleep(2)
            system_actions.restart_app()
        else:
            logging.info("BUTTON_MANAGER: Pulsación larga ignorada - medicamento pendiente")

    def on_button_triple_press(self):
        """
        Manejador para triple pulsación (SOLO CUIDADORES - apagar Pi).
        Solo funciona cuando NO hay medicamento pendiente.
        """
        if self.medication_confirmation_state == "NORMAL":
            logging.info("BUTTON_MANAGER: Triple pulsación - apagando sistema (cuidadores)")
            tts_manager.say("Apagando el sistema. Hasta luego.", self.selected_voice)
            time.sleep(3)
            system_actions.shutdown_pi()
        else:
            logging.info("BUTTON_MANAGER: Triple pulsación ignorada - medicamento pendiente")

    def handle_conversation(self):
        def conversation_task():
            with self.is_speaking_or_listening:
                self.clock_interface.update_status("¡Te escucho!", "#3498DB")
                all_aliases = set()
                for c in reminders.list_contacts(): all_aliases.update([a.strip() for a in c['aliases'].split(',')])
                
                transcribed_text = stt_manager.stream_audio_and_transcribe(adaptation_phrases=list(all_aliases))
                
                if transcribed_text:
                    self.clock_interface.update_status("Procesando...")
                    clean_text = transcribed_text.lower().replace("catalina", "").strip(".,¿?¡! ")
                    self.process_command(clean_text)
                else:
                    self.clock_interface.update_status("No entendí.")
                    tts_manager.say("No te entendí bien.", self.selected_voice)
            
            self.start_wakeword_thread()
        
        threading.Thread(target=conversation_task, daemon=True).start()

    def process_command(self, text: str):
        # Usar RouterCentral si está disponible, sino fallback al sistema clásico
        if self.router_central:
            try:
                result = self.router_central.process_user_input(text)
                
                if result.get('success', False):
                    intent = result.get('intent')
                    response = result.get('response')
                    route = result.get('route')
                    
                    # Log de la interacción basado en la ruta
                    if route in ['generative', 'generative_personalized', 'generative_fallback']:
                        # Log apropiado según el tipo de respuesta
                        if route in ['generative', 'generative_personalized']:
                            log_type = "ai_query_personalized" if route == 'generative_personalized' else "ai_query"
                            firestore_logger.log_interaction(log_type, details={
                                'transcription': text,
                                'route': route,
                                'intent': intent,
                                'personalization': result.get('router_metadata', {}).get('personalization', {})
                            })
                        else:  # generative_fallback
                            firestore_logger.log_interaction("command_not_understood", details={
                                'transcription': text,
                                'route': route,
                                'fallback_reason': 'generative_api_error'
                            })
                        
                        # Para respuestas generativas (incluye fallback), usar la respuesta directamente
                        if response:
                            tts_manager.say(response, self.selected_voice)
                        return
                    else:
                        # Para ruta clásica, procesar intent como antes
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
        else:
            if text:
                if ENABLE_AI_GENERATIVE:
                    # IA Generativa habilitada
                    firestore_logger.log_interaction("ai_query", details={'transcription': text})
                    response = gemini_manager.ask_gemini_chat(text)
                    tts_manager.say(response, self.selected_voice)
                else:
                    # IA Generativa deshabilitada
                    firestore_logger.log_interaction("command_not_understood", details={'transcription': text})
                    tts_manager.say("Comando no reconocido. Intenta con comandos específicos como 'qué hora es', 'recuérdame algo', o 'enciende el enchufe'.", self.selected_voice)

    def announce_reminder(self, reminder_info):
        """
        Sistema unificado de confirmación de medicamentos con pantalla azul (5 minutos).
        """
        with self.is_speaking_or_listening:
            firestore_logger.log_interaction("reminder_triggered", details={'type': 'medication', 'name': reminder_info['medication_name']})
            
            # Iniciar sistema unificado
            self.start_medication_alert(reminder_info)

    # --- NUEVA FUNCIÓN PARA ANUNCIAR TAREAS ---
    def announce_task(self, task_info):
        with self.is_speaking_or_listening:
            # --- AÑADIR ESTA LÍNEA ---
            firestore_logger.log_interaction("reminder_triggered", details={'type': 'task', 'name': task_info['task_name']})
            
            logging.info(f"Ejecutando tarea: {task_info['task_name']}")
            # Para tareas, solo damos el aviso de voz, no mostramos nada en pantalla.
            tts_manager.say(f"Recordatorio de tarea. Es hora de {task_info['task_name']}", self.selected_voice)
    # --- FIN DE LA NUEVA FUNCIÓN ---

    # ==============================================
    # SISTEMA UNIFICADO DE CONFIRMACIÓN DE MEDICAMENTOS (PANTALLA AZUL - 5 MIN)
    # ==============================================
    
    def start_medication_alert(self, medication_info):
        """
        Sistema unificado: Pantalla azul con toda la información (5 minutos).
        """
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
        
        # Timer para timeout (5 minutos total)
        self.medication_timer = threading.Timer(MEDICATION_TIMEOUT, self.handle_medication_timeout)
        self.medication_timer.start()
        
        logging.info(f"MEDICATION: Alerta unificada iniciada - timer de {MEDICATION_TIMEOUT}s activado")

    def _create_medication_audio_message(self, medication_info):
        """
        Crea un mensaje de audio inteligente con cantidad y prescripción.
        """
        base_message = f"Recordatorio. Es hora de tomar"
        
        # Agregar cantidad si está disponible
        cantidad = medication_info.get('cantidad', '')
        if cantidad:
            base_message += f" {cantidad} de"
        
        # Agregar nombre del medicamento
        base_message += f" {medication_info['medication_name']}"
        
        # Agregar prescripción (solo parte clave para no hacer muy largo)
        prescripcion = medication_info.get('prescripcion', '')
        if prescripcion:
            # Buscar palabras clave importantes
            key_phrases = []
            prescripcion_lower = prescripcion.lower()
            
            if 'después' in prescripcion_lower:
                if 'almuerzo' in prescripcion_lower:
                    key_phrases.append('después del almuerzo')
                elif 'comida' in prescripcion_lower:
                    key_phrases.append('después de comer')
                elif 'cena' in prescripcion_lower:
                    key_phrases.append('después de la cena')
            elif 'antes' in prescripcion_lower:
                if 'almuerzo' in prescripcion_lower:
                    key_phrases.append('antes del almuerzo')
                elif 'comida' in prescripcion_lower:
                    key_phrases.append('antes de comer')
            elif 'con comida' in prescripcion_lower or 'con estómago' in prescripcion_lower:
                key_phrases.append('con comida')
            elif 'sin comida' in prescripcion_lower or 'estómago vacío' in prescripcion_lower:
                key_phrases.append('con el estómago vacío')
            
            if key_phrases:
                base_message += f". Recuerda: {', '.join(key_phrases)}"
        
        return base_message

    def handle_medication_confirmed(self):
        """
        Manejador cuando el usuario presiona el botón para confirmar medicamento.
        """
        # Verificar si estamos en modo de confirmación de medicamento
        if self.medication_confirmation_state == "NORMAL":
            logging.info("MEDICATION: Confirmación ignorada - no hay medicamento pendiente")
            return
            
        medication_name = self.current_medication_info['medication_name'] if self.current_medication_info else "medicamento"
        logging.info(f"MEDICATION: Confirmación recibida para {medication_name}")
        
        # Cancelar timer
        self._cancel_medication_timers()
        
        # Logging de confirmación
        firestore_logger.log_interaction("medication_confirmed", details={
            'medication_name': medication_name,
            'user_name': USER_NAME
        })
        
        # Feedback de voz
        tts_manager.say("Medicamento confirmado", self.selected_voice)
        
        # Volver a pantalla normal
        self.clock_interface.hide_all_alerts()
        
        # Resetear estado
        self._reset_medication_state()

    def handle_medication_timeout(self):
        """
        Manejador cuando pasan los 5 minutos totales sin confirmación.
        Envía alerta a contactos de emergencia.
        """
        # Verificar si todavía estamos en estado de medicamento (evitar timeouts duplicados)
        if self.medication_confirmation_state == "NORMAL":
            logging.info("MEDICATION: Timeout cancelado - medicamento ya fue confirmado")
            return
            
        medication_name = self.current_medication_info['medication_name'] if self.current_medication_info else "medicamento"
        logging.warning(f"MEDICATION: Timeout para {medication_name} - enviando alerta de emergencia")
        
        # Logging de timeout
        firestore_logger.log_interaction("medication_timeout_alert", details={
            'medication_name': medication_name,
            'user_name': USER_NAME,
            'timeout_minutes': MEDICATION_TIMEOUT / 60
        })
        
        # Enviar alerta a contactos de emergencia
        try:
            emergency_manager.send_medication_alert(medication_name, USER_NAME)
            logging.info("MEDICATION: Alerta de emergencia enviada exitosamente")
        except Exception as e:
            logging.error(f"MEDICATION: Error enviando alerta de emergencia: {e}")
        
        # Usar self.after para actualizar la UI desde el hilo principal
        self.after(0, lambda: self.clock_interface.hide_all_alerts())
        
        # Resetear estado
        self._reset_medication_state()

    def _cancel_medication_timers(self):
        """Cancela el timer de medicamento activo."""
        if self.medication_timer and self.medication_timer.is_alive():
            self.medication_timer.cancel()
            self.medication_timer = None
            logging.info("MEDICATION: Timer cancelado")

    def _reset_medication_state(self):
        """Resetea el estado del sistema de confirmación de medicamentos."""
        self.medication_confirmation_state = "NORMAL"
        self.current_medication_info = None
        button_manager.exit_medication_confirmation_mode()
        logging.info("MEDICATION: Estado reseteado a NORMAL")

    # ==============================================
    # FIN DEL SISTEMA UNIFICADO DE CONFIRMACIÓN DE MEDICAMENTOS
    # ==============================================

    # --- CAMBIO: update_scheduler ahora lee ambas tablas ---
    def update_scheduler(self):
        if self.scheduler.running: self.scheduler.remove_all_jobs()
        
        # Programar recordatorios de medicamentos
        all_reminders = reminders.list_reminders()
        for rem in all_reminders:
            try:
                days = rem['days_of_week']
                for t in rem['times'].split(','):
                    hour, minute = map(int, t.strip().split(':'))
                    self.scheduler.add_job(self.announce_reminder, 'cron', day_of_week=days, hour=hour, minute=minute, args=[rem])
            except Exception as e: logging.error(f"Error al programar recordatorio: {e}")

        # Programar tareas generales
        try:
            all_tasks = reminders.list_tasks()
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
    # --- FIN DEL CAMBIO ---

    def _handle_plug_on(self): 
        # --- AÑADIR ESTA LÍNEA ---
        firestore_logger.log_interaction("command_executed", details={'command': 'plug_on'})
        
        tts_manager.say("Entendido.", self.selected_voice) if smart_home_manager.set_device_state('enchufe', 'ON') else tts_manager.say("Hubo un error.", self.selected_voice)
    def _handle_plug_off(self): 
        # --- AÑADIR ESTA LÍNEA ---
        firestore_logger.log_interaction("command_executed", details={'command': 'plug_off'})
        
        tts_manager.say("Claro.", self.selected_voice) if smart_home_manager.set_device_state('enchufe', 'OFF') else tts_manager.say("Hubo un error.", self.selected_voice)
    def _handle_get_date(self):
        # --- AÑADIR ESTA LÍNEA ---
        firestore_logger.log_interaction("command_executed", details={'command': 'get_date'})
        
        dias=["lunes","martes","miércoles","jueves","viernes","sábado","domingo"];meses=["enero","febrero","marzo","abril","mayo","junio","julio","agosto","septiembre","octubre","noviembre","diciembre"]
        hoy=datetime.now();respuesta=f"Hoy es {dias[hoy.weekday()]}, {hoy.day} de {meses[hoy.month-1]} de {hoy.year}."
        tts_manager.say(respuesta, self.selected_voice)
    def _handle_get_time(self): 
        # --- AÑADIR ESTA LÍNEA ---
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
    def _handle_specific_contact(self, text):
        # --- AÑADIR ESTA LÍNEA ---
        firestore_logger.log_interaction("command_executed", details={'command': 'contact_person'})
        
        target = next((c for c in reminders.list_contacts() for alias in c['aliases'].split(',') if alias.strip() in text), None)
        if target:
            msg = f"Hola, Kata se quiere contactar contigo, {target['display_name']}."
            emergency_manager.send_emergency_alert(msg, chat_id=target['contact_details']); tts_manager.say(f"Enviando aviso a {target['display_name']}.", self.selected_voice)
        else: tts_manager.say("No encontré a esa persona.", self.selected_voice)
        
    def on_button_pressed(self, from_voice=False):
        def emergency_task():
            if self.is_speaking_or_listening.locked(): return
            if not from_voice:
                self.wakeword_thread.join(timeout=1.0)

            with self.is_speaking_or_listening:
                user_name = os.getenv("USER_NAME", "el usuario")
                message = f"🚨 *ALERTA DE EMERGENCIA* 🚨\nSe ha solicitado ayuda para *{user_name}*."
                ayuda = next((c for c in reminders.list_contacts() if c.get('is_emergency') == 1), None)
                if ayuda:
                    emergency_manager.send_emergency_alert(message, chat_id=ayuda['contact_details'])
                    tts_manager.say("Enviando alerta de emergencia.", self.selected_voice)
                    # --- AÑADIR ESTA LÍNEA ---
                    firestore_logger.log_interaction("emergency_alert_sent", details={'trigger': 'voice' if from_voice else 'button'})
                else: tts_manager.say("Error: No hay contacto de emergencia configurado.", self.selected_voice)
            
            if not from_voice: self.start_wakeword_thread()
        
        threading.Thread(target=emergency_task, daemon=True).start()

    def toggle_mode(self, event=None):
        self.admin_mode = not self.admin_mode
        if self.admin_mode: 
            self.main_container.grid_forget()
            self.admin_container.grid(row=0, column=0, sticky="nsew")
            # Ocultar el botón de tema en modo admin
            self.theme_button.place_forget()
        else: 
            self.admin_container.grid_forget()
            self.main_container.grid(row=0, column=0, sticky="nsew")
            # Mostrar el botón de tema en modo reloj
            self.theme_button.place(relx=0.98, rely=0.02, anchor="ne")

    def on_closing(self):
        if self.scheduler.running: self.scheduler.shutdown()
        wakeword_detector.stop_listening()
        self.destroy()

if __name__ == '__main__':
    reminders.init_db()
    app = KataApp()
    app.mainloop()
