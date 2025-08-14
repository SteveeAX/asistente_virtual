# contact_tab.py (Actualizado con sistema de ALIAS)
from tkinter import *
from tkinter import ttk, messagebox
from reminders import add_contact, list_contacts, delete_contact

class ContactTab(ttk.Frame):
    def __init__(self, parent_notebook, main_app_instance):
        super().__init__(parent_notebook)
        self.main_app = main_app_instance

        # --- Formulario de creación ---
        form_frame = ttk.LabelFrame(self, text="Nuevo Contacto")
        form_frame.pack(fill="x", padx=10, pady=10)

        # <--- CAMBIO: Etiqueta para el nombre principal ---
        Label(form_frame, text="Nombre principal:").grid(row=0, column=0, sticky="w", padx=5, pady=2)
        self.entry_display_name = Entry(form_frame)
        self.entry_display_name.grid(row=0, column=1, sticky="ew", padx=5, pady=2)

        # <--- CAMBIO: Etiqueta y campo para los alias ---
        Label(form_frame, text="Alias (separados por coma):").grid(row=1, column=0, sticky="w", padx=5, pady=2)
        self.entry_aliases = Entry(form_frame)
        self.entry_aliases.grid(row=1, column=1, sticky="ew", padx=5, pady=2)

        Label(form_frame, text="Método:").grid(row=2, column=0, sticky="w", padx=5, pady=2)
        self.entry_method = Entry(form_frame)
        self.entry_method.insert(0, "telegram")
        self.entry_method.grid(row=2, column=1, sticky="ew", padx=5, pady=2)

        Label(form_frame, text="Detalles (Chat ID):").grid(row=3, column=0, sticky="w", padx=5, pady=2)
        self.entry_details = Entry(form_frame)
        self.entry_details.grid(row=3, column=1, sticky="ew", padx=5, pady=2)

        self.is_emergency_var = IntVar()
        self.check_is_emergency = Checkbutton(form_frame, text="¿Es un contacto de emergencia?", variable=self.is_emergency_var)
        self.check_is_emergency.grid(row=4, column=0, columnspan=2, sticky="w", padx=5, pady=5)

        self.btn_save = Button(form_frame, text="Guardar Contacto", command=self.save_contact)
        self.btn_save.grid(row=5, column=0, columnspan=2, sticky="ew", padx=5, pady=5)

        form_frame.grid_columnconfigure(1, weight=1)

        # --- Listado de contactos ---
        list_frame = ttk.LabelFrame(self, text="Contactos Guardados")
        list_frame.pack(fill="both", expand=True, padx=10, pady=10)
        
        # <--- CAMBIO: Actualizamos las columnas de la lista ---
        columns = ("id", "display_name", "aliases", "method", "details", "is_emergency")
        self.tree = ttk.Treeview(list_frame, columns=columns, show="headings", height=6)
        self.tree.heading("id", text="ID")
        self.tree.heading("display_name", text="Nombre")
        self.tree.heading("aliases", text="Alias")
        self.tree.heading("method", text="Método")
        self.tree.heading("details", text="Detalles")
        self.tree.heading("is_emergency", text="Emergencia")
        
        self.tree.column("id", width=40)
        self.tree.column("display_name", width=120)
        self.tree.column("aliases", width=150)
        self.tree.column("method", width=80)
        self.tree.column("details", width=150)
        self.tree.column("is_emergency", width=80, anchor="center")
        
        self.tree.pack(side=LEFT, fill="both", expand=True)

        scrollbar = ttk.Scrollbar(list_frame, orient="vertical", command=self.tree.yview)
        scrollbar.pack(side=RIGHT, fill="y")
        self.tree.configure(yscrollcommand=scrollbar.set)
        
        self.btn_delete = Button(self, text="Eliminar Seleccionado", command=self.delete_selected)
        self.btn_delete.pack(fill="x", padx=10, pady=(0, 10))

        self.load_contacts()

    def load_contacts(self):
        for i in self.tree.get_children():
            self.tree.delete(i)
        
        contacts = list_contacts()
        for contact in contacts:
            emergency_text = "Sí" if contact["is_emergency"] == 1 else "No"
            self.tree.insert("", "end", iid=str(contact["id"]), values=(
                contact["id"],
                contact["display_name"],
                contact["aliases"],
                contact["contact_method"],
                contact["contact_details"],
                emergency_text
            ))

    def save_contact(self):
        # <--- CAMBIO: Obtenemos los nuevos campos del formulario ---
        display_name = self.entry_display_name.get().strip()
        aliases = self.entry_aliases.get().strip()
        method = self.entry_method.get().strip()
        details = self.entry_details.get().strip()
        is_emergency = bool(self.is_emergency_var.get())

        if not all([display_name, aliases, method, details]):
            messagebox.showwarning("Datos incompletos", "Todos los campos son obligatorios.")
            return

        try:
            # <--- CAMBIO: Pasamos los nuevos argumentos a la función de la base de datos ---
            add_contact(display_name, aliases, method, details, is_emergency)
            self.clear_form()
            self.load_contacts()
            messagebox.showinfo("Éxito", "Contacto guardado correctamente.")
        except Exception as e:
            messagebox.showerror("Error", f"No se pudo guardar el contacto: {e}")

    def delete_selected(self):
        selected_items = self.tree.selection()
        if not selected_items:
            messagebox.showinfo("Sin selección", "Por favor, selecciona un contacto de la lista para eliminar.")
            return

        if messagebox.askyesno("Confirmar", "¿Estás seguro de que quieres eliminar el contacto seleccionado?"):
            for item_id in selected_items:
                delete_contact(int(item_id))
            self.load_contacts()
    
    def clear_form(self):
        self.entry_display_name.delete(0, END)
        self.entry_aliases.delete(0, END)
        self.entry_details.delete(0, END)
        self.is_emergency_var.set(0)
