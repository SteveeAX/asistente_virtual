from tkinter import *
from tkinter import ttk, filedialog, messagebox # Importar messagebox directamente
from tkcalendar import DateEntry
from datetime import datetime
import os
from PIL import Image, ImageTk
from reminders import add_reminder, list_reminders, delete_reminder
# from tts_manager import speak # speak ya no se usa directamente aqui para la notificacion principal

class ReminderTab(ttk.Frame):
    def __init__(self, parent_notebook, main_app_instance): # Recibe la instancia de MainApplication
        super().__init__(parent_notebook)
        self.parent_notebook = parent_notebook
        self.main_app = main_app_instance # Guardamos referencia a MainApplication
        self.photo_path = None
        
        # Formulario de creacion
        Label(self, text="Nombre del medicamento:").grid(row=0, column=0, sticky="w", padx=5, pady=5)
        self.entry_name = Entry(self)
        self.entry_name.grid(row=0, column=1, columnspan=3, sticky="ew", padx=5)
        
        Label(self, text="Fecha:").grid(row=1, column=0, sticky="w", padx=5, pady=5)
        self.date_entry = DateEntry(self, date_pattern="yyyy-MM-dd") # formato yyyy-MM-dd
        self.date_entry.grid(row=1, column=1, sticky="w", padx=5)
        
        Label(self, text="Hora:").grid(row=1, column=2, sticky="w", padx=5)
        self.spin_hour = Spinbox(self, from_=0, to=23, width=3, format="%02.0f")
        self.spin_hour.grid(row=1, column=3, sticky="w")
        self.spin_minute = Spinbox(self, from_=0, to=59, width=3, format="%02.0f")
        self.spin_minute.grid(row=1, column=4, sticky="w", padx=(0,10))
        
        self.btn_photo = Button(self, text="Subir foto", command=self.upload_photo)
        self.btn_photo.grid(row=0, column=4, rowspan=2, padx=5, pady=5)
        
        self.btn_save = Button(self, text="Guardar recordatorio", command=self.save_reminder)
        self.btn_save.grid(row=2, column=0, columnspan=5, sticky="ew", padx=5, pady=(0,10))
        
        # Listado de recordatorios
        columns = ("medicamento", "fecha_hora")
        self.tree = ttk.Treeview(self, columns=columns, show="headings", height=6)
        self.tree.heading("medicamento", text="Medicamento")
        self.tree.heading("fecha_hora", text="Fecha / Hora")
        self.tree.grid(row=3, column=0, columnspan=5, sticky="nsew", padx=5, pady=5)
        
        self.btn_delete = Button(self, text="Eliminar seleccionado", command=self.delete_selected)
        self.btn_delete.grid(row=4, column=0, columnspan=5, sticky="ew", padx=5, pady=(0,10))
        
        # Configurar expansion
        for col_index in range(5): # Renombrado para evitar confusion con modulo 'col'
            self.grid_columnconfigure(col_index, weight=1)
        self.grid_rowconfigure(3, weight=1)
        
        # Cargar recordatorios existentes
        self.load_reminders()
    
    def upload_photo(self):
        path = filedialog.askopenfilename(
            title="Seleccionar imagen",
            filetypes=[("Archivos de Imagen", "*.jpg *.jpeg *.png *.gif"), ("Todos los archivos", "*.*")]
        )
        if path:
            self.photo_path = path
            # Mostrar solo el nombre del archivo para no ocupar mucho espacio
            filename = os.path.basename(path)
            self.btn_photo.config(text=f"Foto: {filename[:15]}{'...' if len(filename)>15 else ''}")
    
    def save_reminder(self):
        name = self.entry_name.get().strip()
        date_str = self.date_entry.get_date().strftime("%Y-%m-%d") # Obtener fecha como YYYY-MM-DD
        hour_str = self.spin_hour.get()
        minute_str = self.spin_minute.get()
        
        if not name:
            messagebox.showwarning("Datos incompletos", "Debe ingresar el nombre del medicamento.")
            return
        
        try:
            hour = int(hour_str)
            minute = int(minute_str)
            if not (0 <= hour <= 23 and 0 <= minute <= 59):
                raise ValueError("Hora o minuto fuera de rango.")

            dt_str = f"{date_str} {hour:02d}:{minute:02d}:00"
            remind_dt = datetime.strptime(dt_str, "%Y-%m-%d %H:%M:%S")
            
            if remind_dt < datetime.now():
                messagebox.showwarning("Fecha invalida", "La fecha y hora debe ser posterior a la actual.")
                return
                
            reminder_id = add_reminder(name, self.photo_path, remind_dt)
            if reminder_id: # Solo si se anadio correctamente
                self.clear_form()
                self.load_reminders()
                
                # Solicitar a MainApplication que actualice el scheduler
                if self.main_app:
                    self.main_app.update_scheduler()
                
                messagebox.showinfo("Exito", f"Recordatorio para {name} guardado correctamente.")
                log_event("new_reminder", f"Nuevo recordatorio creado: {name} (ID: {reminder_id})")
            else:
                messagebox.showerror("Error", "No se pudo guardar el recordatorio en la base de datos.")

        except ValueError:
            messagebox.showerror("Error de formato", "La hora o minuto ingresado no es valido.")
        except Exception as e:
            messagebox.showerror("Error", f"Error al guardar: {str(e)}")
    
    def delete_selected(self):
        selected_items = self.tree.selection()
        if not selected_items:
            messagebox.showinfo("Seleccion", "Debe seleccionar un recordatorio para eliminar.")
            return

        # Asumimos que solo se puede seleccionar uno, pero tree.selection() devuelve una tupla
        selected_item_id = selected_items[0] 
        
        # El IID del Treeview es el ID del recordatorio
        try:
            rid = int(selected_item_id)
            if messagebox.askyesno("Confirmar", "Esta seguro de eliminar este recordatorio?"):
                delete_reminder(rid)
                self.load_reminders()
                log_event("delete_reminder", f"Recordatorio eliminado: {rid}")
                
                # Actualizar el scheduler ya que un job fue eliminado (indirectamente)
                if self.main_app:
                    self.main_app.update_scheduler()
        except ValueError:
            messagebox.showerror("Error", "El ID del recordatorio seleccionado no es valido.")

    def load_reminders(self):
        for i in self.tree.get_children():
            self.tree.delete(i)
        
        reminders = list_reminders()
        # print(f"Cargando {len(reminders)} recordatorios") # Puedes descomentar para debug
        
        for rem in reminders:
            # Asegurarse de que 'id' es un string para el iid, aunque en la DB sea int
            self.tree.insert("", "end", iid=str(rem["id"]), values=(rem["medication_name"], rem["remind_datetime"]))
    
    def clear_form(self):
        self.entry_name.delete(0, END)
        self.date_entry.set_date(datetime.today()) # Resetea a hoy
        self.spin_hour.delete(0, END)
        self.spin_hour.insert(0, "00")
        self.spin_minute.delete(0, END)
        self.spin_minute.insert(0, "00")
        self.photo_path = None
        self.btn_photo.config(text="Subir foto")

    def show_reminder_modal(self, rem):
        # Esta funcion parece ser para pruebas o una forma alternativa de mostrar recordatorios.
        # La notificacion principal ahora la maneja ClockInterface a traves de MainApplication.
        # Si aun la necesitas, asegurate de que 'speak' este importado.
        # from tts_manager import speak # Descomentar si se usa speak aqui.
        
        print(f"Mostrando modal para: {rem}") # Debug
        log_event("reminder_modal_shown", rem["medication_name"])
        
        # Ejemplo de como podrias llamar a speak si fuera necesario aqui
        # texto_modal = f"Atencion, recordatorio para {rem['medication_name']}"
        # speak(texto_modal) # Necesitaria importar speak
        
        modal = Toplevel(self)
        modal.title("Recordatorio")
        modal.geometry("400x400")
        modal.transient(self.winfo_toplevel())
        modal.grab_set()
        modal.focus_set()
        self.center_window(modal, 400, 400)
        
        Label(modal, text="RECORDATORIO DE MEDICAMENTO", font=("Arial", 16, "bold")).pack(pady=10)
        Label(modal, text=rem["medication_name"], font=("Arial", 24)).pack(pady=10)
        
        if rem.get("photo_path") and os.path.exists(rem["photo_path"]):
            try:
                img = Image.open(rem["photo_path"])
                # Ajustar Image.ANTIALIAS si Pillow es version >= 10, sino Image.LANCZOS
                resample_method = Image.Resampling.LANCZOS if hasattr(Image, 'Resampling') and hasattr(Image.Resampling, 'LANCZOS') else Image.ANTIALIAS
                img = img.resize((200, 200), resample_method)
                photo = ImageTk.PhotoImage(img)
                
                img_label = Label(modal, image=photo)
                img_label.image = photo
                img_label.pack(pady=10)
            except Exception as e:
                print(f"Error al cargar la imagen en modal: {e}")
                Label(modal, text="No se pudo cargar la imagen").pack(pady=10)
        
        Button(modal, text="Cerrar", command=modal.destroy, font=("Arial", 12)).pack(pady=20)
    
    def center_window(self, window, width, height):
        screen_width = window.winfo_screenwidth()
        screen_height = window.winfo_screenheight()
        x = (screen_width - width) // 2
        y = (screen_height - height) // 2
        window.geometry(f"{width}x{height}+{x}+{y}")
