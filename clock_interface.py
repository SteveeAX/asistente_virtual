import customtkinter as ctk
from PIL import Image, ImageTk
import time
import os
import logging

logger = logging.getLogger(__name__)

class ClockInterface(ctk.CTkFrame):
    def __init__(self, parent):
        super().__init__(parent, fg_color="black")
        self.pack(fill="both", expand=True)

        self.reminder_active = False
        self.is_light_theme = False

        # --- Contenedor Principal para el Reloj ---
        self.main_frame = ctk.CTkFrame(self, fg_color="black")
        self.main_frame.pack(fill="both", expand=True)
        self.main_frame.grid_rowconfigure((0, 2), weight=1)
        self.main_frame.grid_columnconfigure(0, weight=1)

        # Tamaño de fuente grande para el reloj
        font_size = 400
        self.clock_label = ctk.CTkLabel(self.main_frame, text="", font=ctk.CTkFont(family="Arial", size=font_size, weight="bold"))
        self.clock_label.grid(row=0, column=0, sticky="s")
        self.ampm_label = ctk.CTkLabel(self.main_frame, text="", font=ctk.CTkFont(family="Arial", size=int(font_size*0.35), weight="bold"))
        self.ampm_label.grid(row=1, column=0, sticky="n")
        self.status_label = ctk.CTkLabel(self.main_frame, text="", font=ctk.CTkFont(family="Arial", size=24))
        self.status_label.grid(row=2, column=0, sticky="n", pady=20)

        # --- Contenedor Unificado para Alertas de Medicamento (Pantalla Azul) ---
        self.medication_frame = ctk.CTkFrame(self, fg_color="#2E86AB")
        self.medication_frame.grid_rowconfigure((0, 1, 2, 3, 4), weight=1)
        self.medication_frame.grid_columnconfigure(0, weight=1)

        # Título principal
        self.med_title = ctk.CTkLabel(self.medication_frame, text="🚨 MEDICAMENTO 🚨", 
                                     font=ctk.CTkFont(family="Arial", size=70, weight="bold"), text_color="white")
        self.med_title.grid(row=0, column=0, pady=(20, 10))
        
        # Nombre del medicamento
        self.med_name_label = ctk.CTkLabel(self.medication_frame, text="", 
                                          font=ctk.CTkFont(family="Arial", size=55, weight="bold"), text_color="yellow")
        self.med_name_label.grid(row=1, column=0, pady=(10, 20))
        
        # Contenedor para detalles (cantidad y prescripción)
        self.details_frame = ctk.CTkFrame(self.medication_frame, fg_color="transparent")
        self.details_frame.grid(row=2, column=0, pady=(0, 20), sticky="ew")
        self.details_frame.grid_columnconfigure(0, weight=1)
        
        self.cantidad_label = ctk.CTkLabel(self.details_frame, text="", 
                                          font=ctk.CTkFont(family="Arial", size=35, weight="bold"), text_color="lightblue")
        self.cantidad_label.grid(row=0, column=0, pady=5)
        
        self.prescripcion_label = ctk.CTkLabel(self.details_frame, text="", 
                                              font=ctk.CTkFont(family="Arial", size=30), text_color="lightgreen", 
                                              wraplength=800)  # Permite texto en múltiples líneas
        self.prescripcion_label.grid(row=1, column=0, pady=5)
        
        # Imagen del medicamento
        self.med_img_label = ctk.CTkLabel(self.medication_frame, text="")
        self.med_img_label.grid(row=3, column=0, pady=20, sticky="nsew")
        
        # Instrucción para confirmar
        self.confirm_instruction = ctk.CTkLabel(self.medication_frame, text="PRESIONA EL BOTÓN PARA CONFIRMAR", 
                                               font=ctk.CTkFont(family="Arial", size=40, weight="bold"), text_color="white")
        self.confirm_instruction.grid(row=4, column=0, pady=(20, 30))

        # Variable para rastrear timers activos
        self.active_timer = None

        self.update_time()

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

        # Configurar nombre del medicamento
        self.med_name_label.configure(text=reminder_info['medication_name'])
        
        # Configurar cantidad
        cantidad = reminder_info.get('cantidad', '')
        if cantidad:
            self.cantidad_label.configure(text=f"💊 Cantidad: {cantidad}")
        else:
            self.cantidad_label.configure(text="")
        
        # Configurar prescripción
        prescripcion = reminder_info.get('prescripcion', '')
        if prescripcion:
            self.prescripcion_label.configure(text=f"📋 {prescripcion}")
        else:
            self.prescripcion_label.configure(text="")

        # Configurar imagen
        photo_path = reminder_info.get("photo_path")
        if photo_path and os.path.exists(photo_path):
            try:
                # Forzar la actualización del frame para obtener dimensiones reales
                self.medication_frame.update_idletasks()
                
                # Calcular espacio disponible para la imagen (más conservador debido a más contenido)
                available_width = self.winfo_screenwidth() - 200  # Más margen
                available_height = self.winfo_screenheight() - 600  # Espacio para título, detalles e instrucción
                
                # Asegurar dimensiones mínimas
                available_width = max(available_width, 300)
                available_height = max(available_height, 200)
                
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

    def hide_all_alerts(self):
        """Ocultar todas las alertas y volver a la pantalla principal"""
        # Cancelar cualquier timer activo
        if self.active_timer:
            self.after_cancel(self.active_timer)
            self.active_timer = None
        
        # Ocultar pantalla de medicamento
        self.medication_frame.pack_forget()
        
        # Mostrar pantalla principal
        self.main_frame.pack(fill="both", expand=True)
        self.reminder_active = False
        
        logger.info("CLOCK_INTERFACE: Alerta de medicamento oculta, volviendo a pantalla principal")

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
