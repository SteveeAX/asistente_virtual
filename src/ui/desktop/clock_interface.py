import customtkinter as ctk
from PIL import Image, ImageTk
import time
import os
import logging
from .listening_indicator import ListeningIndicator
from .blue_gradient_bar import BlueGradientBar

logger = logging.getLogger(__name__)

class ClockInterface(ctk.CTkFrame):
    def __init__(self, parent):
        super().__init__(parent, fg_color="black")
        self.pack(fill="both", expand=True)

        self.reminder_active = False
        self.is_light_theme = False
        
        # Estado de mensajes
        self.unread_message_count = 0
        self.message_icon_image = None  # Cache para la imagen del ícono de mensajes
        self.notification_icon_size = 203  # Tamaño del ícono reducido 10% (225 * 0.9 = 202.5 ~ 203)
        
        # Estado de temperatura
        self.temperature_label = None
        self.current_temperature = None

        # --- Contenedor Principal para el Reloj ---
        self.main_frame = ctk.CTkFrame(self, fg_color="black")
        self.main_frame.pack(fill="both", expand=True)
        self.main_frame.grid_rowconfigure(0, weight=0)  # Sin peso arriba - empuja todo hacia arriba
        self.main_frame.grid_rowconfigure(2, weight=1)  # Todo el peso abajo
        self.main_frame.grid_rowconfigure(3, weight=0)  # Fila para listening indicator
        self.main_frame.grid_columnconfigure(0, weight=1)

        # Tamaño de fuente grande para el reloj (aumentado y ligeramente más arriba)
        font_size = 450  # Más grande
        self.clock_label = ctk.CTkLabel(self.main_frame, text="", font=ctk.CTkFont(family="Arial", size=font_size, weight="bold"))
        self.clock_label.grid(row=0, column=0, sticky="s", pady=(20, 5))  # Mucho más cerca del AM/PM (30->5)
        self.ampm_label = ctk.CTkLabel(self.main_frame, text="", font=ctk.CTkFont(family="Arial", size=int(font_size*0.35), weight="bold"))
        self.ampm_label.grid(row=1, column=0, sticky="n", pady=(0, 10))  # Menos distancia del reloj (20->10)
        self.status_label = ctk.CTkLabel(self.main_frame, text="", font=ctk.CTkFont(family="Arial", size=48))  # Texto doble de grande (24 -> 48)
        self.status_label.grid(row=2, column=0, sticky="n", pady=10)  # También sube un poco (20->10)
        
        # Icono de mensajes en esquina inferior derecha (posición original)
        # Se ajustará automáticamente cuando aparezca el listening indicator
        self.message_icon_label = ctk.CTkLabel(self.main_frame, text="", compound="left")
        # No hacer place() inicial - se mostrará solo cuando haya mensajes

        # --- Contenedor Unificado para Alertas de Medicamento (Pantalla Amarilla) ---
        self.medication_frame = ctk.CTkFrame(self, fg_color="#ffff00")  # Amarillo según especificación
        self.medication_frame.grid_rowconfigure(0, weight=0)  # Mensaje arriba - espacio fijo
        self.medication_frame.grid_rowconfigure(1, weight=1)  # Imagen - espacio flexible (mayoría)
        self.medication_frame.grid_columnconfigure(0, weight=1)

        # Mensaje dinámico simplificado (reemplaza título + nombre + detalles)
        self.med_message_label = ctk.CTkLabel(self.medication_frame, text="", 
                                            font=ctk.CTkFont(family="Arial", size=65, weight="bold"), 
                                            text_color="black", wraplength=1200)
        self.med_message_label.grid(row=0, column=0, pady=(30, 20), sticky="ew")
        
        # Imagen del medicamento (ocupa la mayor parte del espacio)
        self.med_img_label = ctk.CTkLabel(self.medication_frame, text="")
        self.med_img_label.grid(row=1, column=0, pady=(0, 30), sticky="nsew")

        # --- Contenedor para Confirmación Exitosa (Pantalla Verde) ---
        self.success_frame = ctk.CTkFrame(self, fg_color="green")
        self.success_frame.grid_rowconfigure(0, weight=1)
        self.success_frame.grid_columnconfigure(0, weight=1)
        
        self.success_label = ctk.CTkLabel(self.success_frame, 
                                        text="Toma de medicina realizada",
                                        font=ctk.CTkFont(family="Arial", size=80, weight="bold"),
                                        text_color="white")
        self.success_label.grid(row=0, column=0, sticky="nsew")
        
        # --- Contenedor para Timeout (Pantalla Roja) ---
        self.timeout_frame = ctk.CTkFrame(self, fg_color="red")
        self.timeout_frame.grid_rowconfigure(0, weight=1)
        self.timeout_frame.grid_columnconfigure(0, weight=1)
        
        self.timeout_label = ctk.CTkLabel(self.timeout_frame, 
                                        text="No tomó el medicamento",
                                        font=ctk.CTkFont(family="Arial", size=80, weight="bold"),
                                        text_color="white")
        self.timeout_label.grid(row=0, column=0, sticky="nsew")

        # Variable para rastrear timers activos
        self.active_timer = None

        # --- Indicadores de Escucha ---
        # Indicador de texto (mantener por compatibilidad, pero sin usar pack)
        self.listening_indicator = ListeningIndicator(self.main_frame)
        
        # Nueva barra azul degradada (sin conflictos de layout)
        self.blue_gradient_bar = BlueGradientBar(self)
        logger.info("CLOCK_INTERFACE: Indicadores de escucha inicializados (texto + barra azul)")
        
        # Crear indicador de temperatura
        self._create_temperature_indicator()

        self.update_time()
        
        # Cargar imagen de notificación
        self._load_notification_icon()
        
        # Cargar el conteo de mensajes existentes para mostrar notificaciones persistentes
        self._load_initial_message_count()

    def _load_notification_icon(self):
        """Carga la imagen de notificación desde notification.png"""
        try:
            notification_path = "/home/steveen/asistente_kata/notification.png"
            if os.path.exists(notification_path):
                # Cargar y redimensionar la imagen
                img = Image.open(notification_path)
                img = img.resize((self.notification_icon_size, self.notification_icon_size), Image.Resampling.LANCZOS)
                
                # Crear CTkImage
                self.message_icon_image = ctk.CTkImage(
                    light_image=img,
                    dark_image=img,
                    size=(self.notification_icon_size, self.notification_icon_size)
                )
                logger.info(f"CLOCK_INTERFACE: Ícono de notificación cargado ({self.notification_icon_size}x{self.notification_icon_size})")
            else:
                logger.warning(f"CLOCK_INTERFACE: No se encontró notification.png en {notification_path}")
                self.message_icon_image = None
        except Exception as e:
            logger.error(f"CLOCK_INTERFACE: Error cargando ícono de notificación: {e}")
            self.message_icon_image = None

    def _load_initial_message_count(self):
        """Carga el conteo de mensajes no leídos al iniciar la aplicación"""
        try:
            # Importar el gestor de base de datos si está disponible
            try:
                import sys
                import os
                from dotenv import load_dotenv
                load_dotenv()
                
                sys.path.append(os.path.dirname(os.path.dirname(__file__)))
                sys.path.append(os.path.dirname(os.path.dirname(os.path.dirname(__file__))))
                
                from database.models.shared_data_manager import shared_data_manager
                
                # Contar mensajes no leídos existentes
                with shared_data_manager.get_connection() as conn:
                    cursor = conn.cursor()
                    cursor.execute("SELECT COUNT(*) FROM received_messages WHERE is_read = 0")
                    unread_count = cursor.fetchone()[0]
                    
                    if unread_count > 0:
                        # Actualizar la UI con el conteo existente
                        self.update_message_count(unread_count)
                        logger.info(f"CLOCK_INTERFACE: Cargados {unread_count} mensajes no leídos al iniciar")
                    else:
                        logger.debug("CLOCK_INTERFACE: No hay mensajes no leídos pendientes")
                        
            except ImportError as e:
                logger.warning(f"CLOCK_INTERFACE: No se pudo cargar gestor de BD para mensajes iniciales: {e}")
                
        except Exception as e:
            logger.error(f"CLOCK_INTERFACE: Error cargando conteo inicial de mensajes: {e}")

    def update_theme(self, is_light_theme):
        """Actualizar el tema del reloj cuando cambie el tema global"""
        self.is_light_theme = is_light_theme
        
        if is_light_theme:
            # Tema claro
            bg_color = "white"
            text_color = "black"
        else:
            # Tema oscuro
            bg_color = "black"
            text_color = "white"
        
        # Actualizar colores del contenedor principal
        self.configure(fg_color=bg_color)
        self.main_frame.configure(fg_color=bg_color)
        
        # Actualizar colores del reloj
        self.clock_label.configure(text_color=text_color)
        self.ampm_label.configure(text_color=text_color)
        
        # Solo actualizar el status si no hay un color específico
        current_status_color = self.status_label.cget("text_color")
        if current_status_color in ["white", "black"]:
            self.status_label.configure(text_color=text_color)

    def update_time(self):
        if not self.reminder_active:
            self.clock_label.configure(text=time.strftime("%I:%M").lstrip("0"))
            self.ampm_label.configure(text=time.strftime("%p"))
        
        # Actualizar temperatura cada minuto (cuando los segundos sean 00)
        current_seconds = int(time.strftime("%S"))
        if current_seconds == 0:
            self._update_temperature()
        
        self.after(1000, self.update_time)

    def update_status(self, text, color=None):
        # Si no se especifica color, usar el color apropiado según el tema
        if color is None:
            color = "black" if self.is_light_theme else "white"
        # Si el color es blanco pero estamos en tema claro, cambiar a negro
        elif color == "white" and self.is_light_theme:
            color = "black"
        
        self.status_label.configure(text=text, text_color=color)

    def calculate_responsive_size(self, img_width, img_height, max_width, max_height):
        """
        Calcula el tamaño óptimo para la imagen manteniendo la proporción.
        """
        # Calcular las proporciones
        width_ratio = max_width / img_width
        height_ratio = max_height / img_height
        
        # Usar la proporción más pequeña para que la imagen quepa completamente
        scale_ratio = min(width_ratio, height_ratio)
        
        # Calcular el nuevo tamaño
        new_width = int(img_width * scale_ratio)
        new_height = int(img_height * scale_ratio)
        
        return new_width, new_height
    
    def _create_dynamic_message(self, reminder_info):
        """
        Crea un mensaje dinámico usando variables de la base de datos.
        Formato: "Es hora de tomarte [cantidad] de [medicamento]"
        """
        medicamento = reminder_info['medication_name']
        cantidad = reminder_info.get('cantidad', '')
        prescripcion = reminder_info.get('prescripcion', '')
        
        # Mensaje base
        if cantidad:
            message = f"Es hora de tomarte {cantidad} de {medicamento}"
        else:
            message = f"Es hora de tomarte {medicamento}"
        
        # Agregar prescripción solo si está disponible y es corta
        if prescripcion and len(prescripcion) <= 50:
            message += f"\n{prescripcion}"
        
        return message

    def show_medication_alert(self, reminder_info):
        """Mostrar la pantalla azul unificada de medicamento con toda la información"""
        self.reminder_active = True
        
        # Cancelar timer anterior si existe
        if self.active_timer:
            self.after_cancel(self.active_timer)
            self.active_timer = None
        
        # Ocultar pantalla principal y mostrar alerta de medicamento
        self.main_frame.pack_forget()
        self.medication_frame.pack(fill="both", expand=True)

        # Crear mensaje dinámico
        message = self._create_dynamic_message(reminder_info)
        self.med_message_label.configure(text=message)

        # Configurar imagen del medicamento (ahora con mayor espacio disponible)
        photo_path = reminder_info.get("photo_path")
        if photo_path and os.path.exists(photo_path):
            try:
                # Forzar la actualización del frame para obtener dimensiones reales
                self.medication_frame.update_idletasks()
                
                # Más espacio para la imagen al simplificar el diseño
                available_width = self.winfo_screenwidth() - 100  # Menos margen
                available_height = self.winfo_screenheight() - 300  # Solo espacio para mensaje arriba
                
                # Asegurar dimensiones mínimas
                available_width = max(available_width, 400)
                available_height = max(available_height, 400)
                
                logger.info(f"Dimensiones disponibles para imagen: {available_width}x{available_height}")
                
                # Cargar la imagen original
                img = Image.open(photo_path)
                original_width, original_height = img.size
                logger.info(f"Tamaño original de imagen: {original_width}x{original_height}")
                
                # Calcular el tamaño responsivo
                new_width, new_height = self.calculate_responsive_size(
                    original_width, original_height, available_width, available_height
                )
                
                logger.info(f"Nuevo tamaño calculado: {new_width}x{new_height}")
                
                # Redimensionar la imagen manteniendo la proporción
                img_resized = img.resize((new_width, new_height), Image.Resampling.LANCZOS)
                
                # Crear el objeto CTkImage con el tamaño calculado
                photo = ctk.CTkImage(
                    light_image=img_resized, 
                    dark_image=img_resized, 
                    size=(new_width, new_height)
                )
                
                self.med_img_label.configure(image=photo, text="")
                logger.info("Imagen del medicamento cargada y redimensionada exitosamente")
                
            except Exception as e:
                logger.error(f"Error al cargar imagen del medicamento: {e}")
                self.med_img_label.configure(image=None, text="(Error al cargar imagen)")
        else:
            logger.warning(f"Imagen no encontrada en: {photo_path}")
            self.med_img_label.configure(image=None, text="(Sin imagen)")

        logger.info(f"CLOCK_INTERFACE: Mostrando alerta de medicamento para {reminder_info['medication_name']}")

    def show_medication_success(self):
        """Mostrar pantalla verde de confirmación por 2 segundos"""
        self.reminder_active = True
        
        # Cancelar timer anterior si existe
        if self.active_timer:
            self.after_cancel(self.active_timer)
            self.active_timer = None
        
        # Ocultar todas las pantallas y mostrar la verde
        self.main_frame.pack_forget()
        self.medication_frame.pack_forget()
        self.timeout_frame.pack_forget()
        self.success_frame.pack(fill="both", expand=True)
        
        # Programar que se oculte después de 2 segundos
        self.active_timer = self.after(2000, self.hide_all_alerts)
        
        logger.info("CLOCK_INTERFACE: Mostrando pantalla verde de confirmación por 2 segundos")

    def show_medication_timeout_alert(self):
        """Mostrar pantalla roja de timeout por 2 segundos"""
        self.reminder_active = True
        
        # Cancelar timer anterior si existe
        if self.active_timer:
            self.after_cancel(self.active_timer)
            self.active_timer = None
        
        # Ocultar todas las pantallas y mostrar la roja
        self.main_frame.pack_forget()
        self.medication_frame.pack_forget()
        self.success_frame.pack_forget()
        self.timeout_frame.pack(fill="both", expand=True)
        
        # Programar que se oculte después de 2 segundos
        self.active_timer = self.after(2000, self.hide_all_alerts)
        
        logger.info("CLOCK_INTERFACE: Mostrando pantalla roja de timeout por 2 segundos")

    def hide_all_alerts(self):
        """Ocultar todas las alertas y volver a la pantalla principal"""
        # Cancelar cualquier timer activo
        if self.active_timer:
            self.after_cancel(self.active_timer)
            self.active_timer = None
        
        # Ocultar todas las pantallas de alerta
        self.medication_frame.pack_forget()
        self.success_frame.pack_forget()
        self.timeout_frame.pack_forget()
        
        # Mostrar pantalla principal
        self.main_frame.pack(fill="both", expand=True)
        self.reminder_active = False
        
        logger.info("CLOCK_INTERFACE: Todas las alertas ocultas, volviendo a pantalla principal")

    # Funciones legacy mantenidas para compatibilidad
    def show_reminder(self, reminder_info):
        """Legacy: ahora redirige a show_medication_alert"""
        logger.warning("CLOCK_INTERFACE: Usando función legacy show_reminder, redirigiendo a show_medication_alert")
        self.show_medication_alert(reminder_info)
    
    def show_medication_urgency(self, medication_name):
        """Legacy: Ya no se usa en el sistema unificado"""
        logger.warning("CLOCK_INTERFACE: Función show_medication_urgency ya no se usa en el sistema unificado")
        
    def hide_reminder(self):
        """Legacy: ahora redirige a hide_all_alerts"""
        logger.warning("CLOCK_INTERFACE: Usando función legacy hide_reminder, redirigiendo a hide_all_alerts")
        self.hide_all_alerts()

    # --- FUNCIONES PARA MENSAJES ---
    def update_message_count(self, count: int):
        """
        Actualiza el contador visual de mensajes no leídos.
        
        Args:
            count: Número de mensajes no leídos
        """
        try:
            self.unread_message_count = count
            
            if count > 0:
                # Formar texto según especificación exacta
                if count == 1:
                    counter_text = "1 mensaje nuevo"
                else:
                    counter_text = f"{count} mensajes nuevos"
                
                # Configurar con imagen de notificación - SIN fondo azul
                if self.message_icon_image:
                    self.message_icon_label.configure(
                        image=self.message_icon_image,
                        text=counter_text,
                        text_color="black",  # Texto negro para visibilidad sin fondo
                        fg_color="transparent",  # Sin fondo
                        font=ctk.CTkFont(family="Arial", size=64, weight="bold"),  # Texto mucho más grande y legible
                        compound="left"  # Imagen a la izquierda, texto a la derecha
                    )
                else:
                    # Fallback sin imagen - también sin fondo
                    self.message_icon_label.configure(
                        image=None,
                        text=f"💬 {counter_text}",
                        text_color="black",  # Texto negro para visibilidad sin fondo
                        fg_color="transparent",  # Sin fondo
                        font=ctk.CTkFont(family="Arial", size=32, weight="bold")
                    )
                # Mostrar el label con place() - posición ajustada para ícono mucho más grande (120px)
                self.message_icon_label.place(relx=1.0, rely=1.0, anchor="se", x=-20, y=-20)
                logger.info(f"CLOCK_INTERFACE: Notificación visual mostrada - {counter_text}")
            else:
                # Ocultar icono y texto completamente
                self.message_icon_label.place_forget()  # Quitar de pantalla
                logger.debug("CLOCK_INTERFACE: Icono de mensajes oculto - sin mensajes")
                
        except Exception as e:
            logger.error(f"CLOCK_INTERFACE: Error actualizando contador de mensajes: {e}")
    
    def get_message_count(self) -> int:
        """
        Obtiene el número actual de mensajes no leídos.
        
        Returns:
            Número de mensajes no leídos
        """
        return self.unread_message_count
    
    # --- FUNCIONES PARA INDICADOR DE ESCUCHA ---
    def show_listening_indicator(self, with_animation=True):
        """
        Muestra el indicador de escucha animado.
        
        Args:
            with_animation (bool): Si True, inicia la animación RGB automáticamente
        """
        try:
            # Usar la nueva barra azul degradada (sin conflictos de layout)
            self.blue_gradient_bar.show(animate=with_animation)
            
            # Ajustar posición de elementos si es necesario
            self._adjust_message_icon_position(listening_active=True)
            self._adjust_temperature_position(listening_active=True)
            
            logger.info(f"CLOCK_INTERFACE: Barra azul de escucha mostrada (animación: {with_animation})")
        except Exception as e:
            logger.error(f"CLOCK_INTERFACE: Error mostrando barra de escucha: {e}")
    
    def hide_listening_indicator(self):
        """
        Oculta el indicador de escucha y detiene la animación.
        También restaura la posición original del message icon.
        """
        try:
            # Ocultar la barra azul degradada
            self.blue_gradient_bar.hide()
            
            # Restaurar posición original de elementos
            self._adjust_message_icon_position(listening_active=False)
            self._adjust_temperature_position(listening_active=False)
            
            logger.info("CLOCK_INTERFACE: Barra azul de escucha ocultada")
        except Exception as e:
            logger.error(f"CLOCK_INTERFACE: Error ocultando barra de escucha: {e}")
    
    def is_listening_indicator_visible(self):
        """
        Verifica si el indicador de escucha está visible.
        
        Returns:
            bool: True si está visible, False en caso contrario
        """
        try:
            return self.blue_gradient_bar.is_shown()
        except Exception as e:
            logger.error(f"CLOCK_INTERFACE: Error verificando estado del indicador: {e}")
            return False
    
    def _adjust_message_icon_position(self, listening_active: bool):
        """
        Ajusta dinámicamente la posición del message icon según el estado del listening indicator.
        
        Args:
            listening_active (bool): True si listening indicator está activo
        """
        try:
            if self.unread_message_count > 0:  # Solo ajustar si hay mensajes visibles
                if listening_active:
                    # Subir el message icon para evitar solapamiento con la barra azul (60px)
                    # Elevar 140px para dar espacio fluido con el ícono súper grande (120px)
                    self.message_icon_label.place(relx=1.0, rely=1.0, anchor="se", x=-20, y=-140)
                    logger.debug("CLOCK_INTERFACE: Message icon elevado para evitar solapamiento con barra azul")
                else:
                    # Restaurar posición original para el ícono súper grande
                    self.message_icon_label.place(relx=1.0, rely=1.0, anchor="se", x=-20, y=-20)
                    logger.debug("CLOCK_INTERFACE: Message icon restaurado a posición original")
        except Exception as e:
            logger.error(f"CLOCK_INTERFACE: Error ajustando posición del message icon: {e}")
    
    def _create_temperature_indicator(self):
        """
        Crea el indicador de temperatura en la esquina inferior izquierda.
        """
        try:
            # Crear label para temperatura
            self.temperature_label = ctk.CTkLabel(
                self.main_frame,
                text="--°C",
                font=("Arial", 14),
                text_color="white",
                fg_color="transparent"
            )
            
            # Posicionar en esquina inferior izquierda
            self.temperature_label.place(relx=0.0, rely=1.0, anchor="sw", x=20, y=-20)
            
            # Inicializar temperatura
            self._update_temperature()
            
            logger.info("CLOCK_INTERFACE: Indicador de temperatura creado")
            
        except Exception as e:
            logger.error(f"CLOCK_INTERFACE: Error creando indicador de temperatura: {e}")
    
    def _get_system_temperature(self) -> float:
        """
        Obtiene la temperatura del sistema en grados Celsius.
        
        Returns:
            float: Temperatura en °C, o None si no se puede obtener
        """
        try:
            with open('/sys/class/thermal/thermal_zone0/temp', 'r') as f:
                temp_str = f.read().strip()
                # El valor está en miligrados, convertir a grados
                temp_celsius = int(temp_str) / 1000.0
                return temp_celsius
        except Exception as e:
            logger.debug(f"CLOCK_INTERFACE: No se pudo leer temperatura: {e}")
            return None
    
    def _update_temperature(self):
        """
        Actualiza el display de temperatura.
        """
        try:
            temp = self._get_system_temperature()
            if temp is not None:
                self.current_temperature = temp
                # Formatear temperatura
                temp_text = f"{temp:.0f}°C"
                
                # Cambiar color según temperatura
                if temp >= 80:
                    color = "#ff4444"  # Rojo para alta temperatura
                elif temp >= 70:
                    color = "#ffaa44"  # Naranja para temperatura media-alta
                else:
                    color = "white"    # Blanco para temperatura normal
                
                if self.temperature_label:
                    self.temperature_label.configure(text=temp_text, text_color=color)
            
        except Exception as e:
            logger.error(f"CLOCK_INTERFACE: Error actualizando temperatura: {e}")
    
    def _adjust_temperature_position(self, listening_active: bool):
        """
        Ajusta dinámicamente la posición del indicador de temperatura según el estado del listening indicator.
        
        Args:
            listening_active (bool): True si listening indicator está activo
        """
        try:
            if self.temperature_label:
                if listening_active:
                    # Subir el indicador de temperatura cuando aparece la barra de listening
                    self.temperature_label.place(relx=0.0, rely=1.0, anchor="sw", x=20, y=-80)
                    logger.debug("CLOCK_INTERFACE: Temperatura subida para evitar solapamiento")
                else:
                    # Restaurar posición original cuando se oculta la barra
                    self.temperature_label.place(relx=0.0, rely=1.0, anchor="sw", x=20, y=-20)
                    logger.debug("CLOCK_INTERFACE: Temperatura restaurada a posición original")
        except Exception as e:
            logger.error(f"CLOCK_INTERFACE: Error ajustando posición de temperatura: {e}")
