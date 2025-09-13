import customtkinter as ctk
from tkinter import messagebox
from datetime import datetime
import reminders

class ReminderTab(ctk.CTkFrame):
    def __init__(self, parent, controller):
        super().__init__(parent)
        self.controller = controller
        self.pack(fill="both", expand=True)

        ctk.CTkLabel(self, text="Gestión de Recordatorios de Medicamentos", font=ctk.CTkFont(size=16, weight="bold")).pack(pady=10)
        
        form_frame = ctk.CTkFrame(self)
        form_frame.pack(pady=5, padx=10, fill="x")

        ctk.CTkLabel(form_frame, text="Medicamento:").grid(row=0, column=0, padx=5, pady=5, sticky="w")
        self.name_entry = ctk.CTkEntry(form_frame, placeholder_text="Ej: Pastilla de la presión")
        self.name_entry.grid(row=0, column=1, padx=5, pady=5, sticky="ew")

        ctk.CTkLabel(form_frame, text="Cantidad:").grid(row=1, column=0, padx=5, pady=5, sticky="w")
        self.cantidad_entry = ctk.CTkEntry(form_frame, placeholder_text="Ej: 2 pastillas, 500ml, 1/2 tableta")
        self.cantidad_entry.grid(row=1, column=1, padx=5, pady=5, sticky="ew")

        ctk.CTkLabel(form_frame, text="Prescripción:").grid(row=2, column=0, padx=5, pady=5, sticky="w")
        self.prescripcion_textbox = ctk.CTkTextbox(form_frame, height=80)
        self.prescripcion_textbox.grid(row=2, column=1, padx=5, pady=5, sticky="ew")
        self.prescripcion_textbox.insert("1.0", "Ej: Tomar después del almuerzo con estómago lleno")

        ctk.CTkLabel(form_frame, text="Horas (HH:MM, ...):").grid(row=3, column=0, padx=5, pady=5, sticky="w")
        self.times_entry = ctk.CTkEntry(form_frame, placeholder_text="Ej: 08:00, 20:00")
        self.times_entry.grid(row=3, column=1, padx=5, pady=5, sticky="ew")

        ctk.CTkLabel(form_frame, text="Días:").grid(row=4, column=0, padx=5, pady=5, sticky="w")
        self.days_frame = ctk.CTkFrame(form_frame, fg_color="transparent")
        self.days_frame.grid(row=4, column=1, padx=5, pady=5, sticky="ew")
        
        self.day_vars = {}
        days = {"Lunes": "mon", "Martes": "tue", "Miércoles": "wed", "Jueves": "thu", "Viernes": "fri", "Sábado": "sat", "Domingo": "sun"}
        for i, (day_name, day_val) in enumerate(days.items()):
            self.day_vars[day_val] = ctk.StringVar(value="off")
            cb = ctk.CTkCheckBox(self.days_frame, text=day_name, variable=self.day_vars[day_val], onvalue=day_val, offvalue="off")
            cb.grid(row=0, column=i, padx=5)

        form_frame.grid_columnconfigure(1, weight=1)

        button_frame = ctk.CTkFrame(self, fg_color="transparent")
        button_frame.pack(pady=5)
        ctk.CTkButton(button_frame, text="Añadir Recordatorio", command=self.add_reminder).pack(side="left", padx=5)
        ctk.CTkButton(button_frame, text="Eliminar Seleccionado", command=self.delete_reminder).pack(side="left", padx=5)

        self.scrollable_frame = ctk.CTkScrollableFrame(self, label_text="Recordatorios Programados")
        self.scrollable_frame.pack(pady=10, padx=10, fill="both", expand=True)
        self.selected_reminder_id = None
        self.reminder_widgets = {}
        self.load_reminders()

    def load_reminders(self):
        for widget in self.reminder_widgets.values():
            widget.destroy()
        self.reminder_widgets.clear()
        
        all_reminders = reminders.list_reminders()
        for rem in all_reminders:
            # Mostrar información mejorada incluyendo cantidad
            cantidad_text = f" ({rem.get('cantidad', 'Sin cantidad')})" if rem.get('cantidad') else ""
            rem_text = f"{rem['medication_name']}{cantidad_text} - {rem['times']} - {rem['days_of_week']}"
            btn = ctk.CTkButton(self.scrollable_frame, text=rem_text, fg_color="gray20", 
                                      command=lambda rid=rem['id']: self.select_reminder(rid))
            btn.pack(fill="x", pady=2, padx=2)
            self.reminder_widgets[rem['id']] = btn

    def select_reminder(self, reminder_id):
        self.selected_reminder_id = reminder_id
        for rid, btn in self.reminder_widgets.items():
            btn.configure(fg_color="gray20")
        self.reminder_widgets[reminder_id].configure(fg_color="#3498DB")

    def add_reminder(self):
        name = self.name_entry.get()
        cantidad = self.cantidad_entry.get().strip()
        prescripcion = self.prescripcion_textbox.get("1.0", "end-1c").strip()
        times = self.times_entry.get()
        
        selected_days = [var.get() for var in self.day_vars.values() if var.get() != "off"]
        days_str = ",".join(selected_days)
        
        # Limpiar texto placeholder si está presente
        if prescripcion == "Ej: Tomar después del almuerzo con estómago lleno":
            prescripcion = ""
        
        if name and times and days_str:
            # Pasar los nuevos campos a la función (cantidad y prescripción pueden estar vacíos)
            reminders.add_reminder(name, "", times, days_str, cantidad, prescripcion)
            self.load_reminders()
            self.controller.update_scheduler()
            
            # Limpiar campos
            self.name_entry.delete(0, "end")
            self.cantidad_entry.delete(0, "end")
            self.prescripcion_textbox.delete("1.0", "end")
            self.prescripcion_textbox.insert("1.0", "Ej: Tomar después del almuerzo con estómago lleno")
            self.times_entry.delete(0, "end")
            for var in self.day_vars.values():
                var.set("off")
        else:
            messagebox.showwarning("Faltan datos", "Completa al menos Medicamento, Horas y Días.")

    def delete_reminder(self):
        if self.selected_reminder_id is not None:
            if messagebox.askyesno("Confirmar", "¿Eliminar este recordatorio?"):
                reminders.delete_reminder(self.selected_reminder_id)
                self.load_reminders()
                self.controller.update_scheduler()
                self.selected_reminder_id = None
        else:
            messagebox.showwarning("Sin selección", "Selecciona un recordatorio.")
