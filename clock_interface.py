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

        # --- Contenedor para la Alerta de Recordatorio (oculto) ---
        self.reminder_frame = ctk.CTkFrame(self, fg_color="white")
        self.reminder_frame.grid_rowconfigure(1, weight=1)
        self.reminder_frame.grid_columnconfigure(0, weight=1)

        self.med_label = ctk.CTkLabel(self.reminder_frame, text="", font=ctk.CTkFont(family="Arial", size=70, weight="bold"), text_color="#4a86e8")
        self.med_label.grid(row=0, column=0, pady=(50, 20))
        self.img_label = ctk.CTkLabel(self.reminder_frame, text="")
        self.img_label.grid(row=1, column=0, pady=20, sticky="nsew")

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

    def show_reminder(self, reminder_info):
        self.reminder_active = True
        self.main_frame.pack_forget()
        self.reminder_frame.pack(fill="both", expand=True)

        self.med_label.configure(text=f"Es hora de tomar:\n{reminder_info['medication_name']}")

        photo_path = reminder_info.get("photo_path")
        if photo_path and os.path.exists(photo_path):
            try:
                # Forzar la actualización del frame para obtener dimensiones reales
                self.reminder_frame.update_idletasks()
                
                # Obtener dimensiones disponibles para la imagen
                # Dejamos algo de margen para el texto y padding
                available_width = self.winfo_screenwidth() - 100  # 50px de margen a cada lado
                available_height = self.winfo_screenheight() - 300  # Espacio para texto y márgenes
                
                # Asegurar dimensiones mínimas
                available_width = max(available_width, 400)
                available_height = max(available_height, 300)
                
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
                
                self.img_label.configure(image=photo, text="")
                logger.info("Imagen del recordatorio cargada y redimensionada exitosamente")
                
            except Exception as e:
                logger.error(f"Error al cargar imagen del recordatorio: {e}")
                self.img_label.configure(image=None, text="Error al cargar imagen")
        else:
            logger.warning(f"Imagen no encontrada en: {photo_path}")
            self.img_label.configure(image=None, text="(Sin imagen)")

        # Auto-ocultar después de 60 segundos
        self.after(60000, self.hide_reminder)

    def hide_reminder(self):
        if self.reminder_active:
            self.reminder_frame.pack_forget()
            self.main_frame.pack(fill="both", expand=True)
            self.reminder_active = False
