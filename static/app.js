document.addEventListener('DOMContentLoaded', function() {
    // Cargar todos los datos al iniciar
    loadInitialData();

    // Listeners para los formularios
    document.getElementById('add-contact-form').addEventListener('submit', handleAddContact);
    document.getElementById('add-reminder-form').addEventListener('submit', handleAddReminder);
    document.getElementById('add-task-form').addEventListener('submit', handleAddTask); // <-- Nuevo listener
    document.getElementById('settings-form').addEventListener('submit', handleSaveSettings);
});

function loadInitialData() {
    fetchContacts();
    fetchReminders();
    fetchTasks(); // <-- Nueva función de carga
    fetchSettings();
}

// --- FUNCIONES DE CONFIGURACIÓN (sin cambios) ---
function fetchSettings() {
    fetch('/api/available-voices').then(res => res.json()).then(voices => {
        const voiceSelect = document.getElementById('voice-select');
        voiceSelect.innerHTML = '';
        for (const [name, id] of Object.entries(voices)) {
            const option = document.createElement('option');
            option.value = id; option.textContent = name; voiceSelect.appendChild(option);
        }
        fetch('/api/settings').then(res => res.json()).then(settings => {
            voiceSelect.value = settings.voice_name;
        });
    });
}
function handleSaveSettings(event) {
    event.preventDefault();
    const settings = { voice_name: document.getElementById('voice-select').value };
    fetch('/api/settings', { method: 'POST', headers: { 'Content-Type': 'application/json' }, body: JSON.stringify(settings)
    }).then(res => res.json()).then(data => {
        if (data.success) { alert('Configuración guardada.'); } 
        else { alert('Error al guardar la configuración.'); }
    });
}

// --- FUNCIONES DE CONTACTOS (sin cambios) ---
function fetchContacts() {
    fetch('/api/contacts').then(res => res.json()).then(data => {
        const list = document.getElementById('contact-list-body');
        list.innerHTML = '';
        data.forEach(c => {
            const row = list.insertRow();
            row.innerHTML = `<td>${c.display_name}</td><td>${c.aliases}</td><td>${c.contact_details}</td><td>${c.is_emergency === 1 ? 'Sí' : 'No'}</td><td><button class="delete-btn" data-id="${c.id}" data-type="contact">Eliminar</button></td>`;
        });
        addDeleteListeners();
    });
}
function handleAddContact(event) {
    event.preventDefault();
    const contact = { displayName: document.getElementById('displayName').value, aliases: document.getElementById('aliases').value, details: document.getElementById('details').value, isEmergency: document.getElementById('isEmergency').checked };
    fetch('/api/contacts/add', { method: 'POST', headers: { 'Content-Type': 'application/json' }, body: JSON.stringify(contact)
    }).then(res => res.json()).then(data => {
        if (data.success) { document.getElementById('add-contact-form').reset(); fetchContacts(); } 
        else { alert('Error al guardar.'); }
    });
}

// --- FUNCIONES DE RECORDATORIOS (actualizada con nuevos campos) ---
function fetchReminders() {
    fetch('/api/reminders').then(res => res.json()).then(data => {
        const list = document.getElementById('reminder-list-body');
        list.innerHTML = '';
        data.forEach(r => {
            const row = list.insertRow();
            const cantidad = r.cantidad || 'No especificada';
            const prescripcion = r.prescripcion ? (r.prescripcion.length > 30 ? r.prescripcion.substring(0, 30) + '...' : r.prescripcion) : '';
            
            // Tooltip para prescripción completa si es muy larga
            const prescripcionCell = r.prescripcion ? `<span title="${r.prescripcion}">${prescripcion}</span>` : '';
            
            row.innerHTML = `
                <td>
                    <strong>${r.medication_name}</strong>
                    ${prescripcionCell ? '<br><small style="color: #666; font-style: italic;">📋 ' + prescripcionCell + '</small>' : ''}
                </td>
                <td><span style="color: #2e86ab; font-weight: bold;">${cantidad}</span></td>
                <td>${r.times}</td>
                <td>${r.days_of_week}</td>
                <td><button class="delete-btn" data-id="${r.id}" data-type="reminder">Eliminar</button></td>`;
        });
        addDeleteListeners();
    });
}
function handleAddReminder(event) {
    event.preventDefault();
    const formData = new FormData();
    formData.append('medication_name', document.getElementById('medicationName').value);
    formData.append('cantidad', document.getElementById('medicationQuantity').value);  // Nuevo campo
    formData.append('prescripcion', document.getElementById('medicationPrescription').value);  // Nuevo campo
    formData.append('times', document.getElementById('remindTimes').value);
    const days = [];
    document.querySelectorAll('#remind-days input:checked').forEach(cb => days.push(cb.value));
    formData.append('days_of_week', days.join(','));
    const photoInput = document.getElementById('medicationPhoto');
    if (photoInput.files.length > 0) formData.append('photo', photoInput.files[0]);
    fetch('/api/reminders/add', { method: 'POST', body: formData
    }).then(res => res.json()).then(data => {
        if (data.success) { 
            document.getElementById('add-reminder-form').reset(); 
            fetchReminders(); 
            alert('Recordatorio añadido con éxito!');
        } 
        else { alert('Error al guardar: ' + (data.error || 'Error desconocido')); }
    });
}

// --- NUEVAS FUNCIONES PARA TAREAS ---
function fetchTasks() {
    fetch('/api/tasks').then(res => res.json()).then(data => {
        const list = document.getElementById('task-list-body');
        list.innerHTML = '';
        data.forEach(t => {
            const row = list.insertRow();
            row.innerHTML = `<td>${t.task_name}</td><td>${t.times}</td><td>${t.days_of_week}</td><td><button class="delete-btn" data-id="${t.id}" data-type="task">Eliminar</button></td>`;
        });
        addDeleteListeners();
    });
}
function handleAddTask(event) {
    event.preventDefault();
    const days = [];
    document.querySelectorAll('#task-days input:checked').forEach(cb => days.push(cb.value));
    const task = {
        task_name: document.getElementById('taskName').value,
        times: document.getElementById('taskTimes').value,
        days_of_week: days.join(',')
    };
    fetch('/api/tasks/add', { method: 'POST', headers: { 'Content-Type': 'application/json' }, body: JSON.stringify(task)
    }).then(res => res.json()).then(data => {
        if (data.success) { document.getElementById('add-task-form').reset(); fetchTasks(); } 
        else { alert('Error al guardar.'); }
    });
}

// --- FUNCIÓN GENÉRICA PARA BORRAR (actualizada) ---
function addDeleteListeners() {
    document.querySelectorAll('.delete-btn').forEach(button => button.replaceWith(button.cloneNode(true)));
    document.querySelectorAll('.delete-btn').forEach(button => button.addEventListener('click', handleDelete));
}
function handleDelete(event) {
    const id = event.target.getAttribute('data-id');
    const type = event.target.getAttribute('data-type');
    if (confirm(`¿Eliminar este ${type}?`)) {
        fetch(`/api/${type}s/delete`, { method: 'POST', headers: { 'Content-Type': 'application/json' }, body: JSON.stringify({ id: id })
        }).then(res => res.json()).then(data => {
            if (data.success) {
                if (type === 'contact') fetchContacts();
                else if (type === 'reminder') fetchReminders();
                else if (type === 'task') fetchTasks(); // <-- Se añade la actualización de tareas
            } else { alert(`Error al eliminar.`); }
        });
    }
}
