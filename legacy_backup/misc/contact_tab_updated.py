# contact_tab_updated.py
import customtkinter as ctk
from tkinter import messagebox
import reminders

class ContactTab(ctk.CTkFrame):
    def __init__(self, parent, controller):
        super().__init__(parent)
        self.controller = controller
        self.pack(fill="both", expand=True)

        ctk.CTkLabel(self, text="Gestión de Contactos", font=ctk.CTkFont(size=16, weight="bold")).pack(pady=10)
        
        form_frame = ctk.CTkFrame(self)
        form_frame.pack(pady=5, padx=10, fill="x")

        ctk.CTkLabel(form_frame, text="Nombre Principal:").grid(row=0, column=0, padx=5, pady=5, sticky="w")
        self.name_entry = ctk.CTkEntry(form_frame, placeholder_text="Ej: Ana (Hija)")
        self.name_entry.grid(row=0, column=1, padx=5, pady=5, sticky="ew")

        ctk.CTkLabel(form_frame, text="Alias (para la voz):").grid(row=1, column=0, padx=5, pady=5, sticky="w")
        self.aliases_entry = ctk.CTkEntry(form_frame, placeholder_text="Ej: ana, anita, hija")
        self.aliases_entry.grid(row=1, column=1, padx=5, pady=5, sticky="ew")

        ctk.CTkLabel(form_frame, text="Chat ID (Telegram):").grid(row=2, column=0, padx=5, pady=5, sticky="w")
        self.details_entry = ctk.CTkEntry(form_frame, placeholder_text="Ej: 123456789")
        self.details_entry.grid(row=2, column=1, padx=5, pady=5, sticky="ew")
        
        self.emergency_var = ctk.BooleanVar()
        ctk.CTkCheckBox(form_frame, text="Es contacto de emergencia", variable=self.emergency_var).grid(row=3, column=1, padx=5, pady=5, sticky="w")
        
        form_frame.grid_columnconfigure(1, weight=1)

        button_frame = ctk.CTkFrame(self, fg_color="transparent")
        button_frame.pack(pady=5)
        ctk.CTkButton(button_frame, text="Añadir Contacto", command=self.add_contact).pack(side="left", padx=5)
        ctk.CTkButton(button_frame, text="Eliminar Seleccionado", command=self.delete_contact).pack(side="left", padx=5)

        self.scrollable_frame = ctk.CTkScrollableFrame(self, label_text="Contactos Guardados")
        self.scrollable_frame.pack(pady=10, padx=10, fill="both", expand=True)
        self.selected_contact_id = None
        self.contact_widgets = {}
        self.load_contacts()

    def load_contacts(self):
        for widget in self.contact_widgets.values():
            widget.destroy()
        self.contact_widgets.clear()
        
        contacts = reminders.list_contacts()
        for contact in contacts:
            is_emergency = "Sí" if contact.get('is_emergency', 0) == 1 else "No"
            contact_text = f"{contact['display_name']} ({contact['aliases']}) | Emergencia: {is_emergency}"
            btn = ctk.CTkButton(self.scrollable_frame, text=contact_text, fg_color="gray20",
                                command=lambda cid=contact['id']: self.select_contact(cid))
            btn.pack(fill="x", pady=2, padx=2)
            self.contact_widgets[contact['id']] = btn

    def select_contact(self, contact_id):
        self.selected_contact_id = contact_id
        for cid, btn in self.contact_widgets.items():
            btn.configure(fg_color="gray20")
        self.contact_widgets[contact_id].configure(fg_color="#3498DB")

    def add_contact(self):
        name = self.name_entry.get()
        aliases = self.aliases_entry.get()
        details = self.details_entry.get()
        if name and aliases and details:
            reminders.add_contact(name, aliases, "telegram", details, self.emergency_var.get())
            self.load_contacts()
            self.name_entry.delete(0, "end")
            self.aliases_entry.delete(0, "end")
            self.details_entry.delete(0, "end")
            self.emergency_var.set(False)
        else:
            messagebox.showwarning("Faltan datos", "Completa todos los campos.")

    def delete_contact(self):
        if self.selected_contact_id:
            if messagebox.askyesno("Confirmar", "¿Eliminar este contacto?"):
                reminders.delete_contact(self.selected_contact_id)
                self.load_contacts()
                self.selected_contact_id = None
        else:
            messagebox.showwarning("Sin selección", "Selecciona un contacto para eliminar.")
