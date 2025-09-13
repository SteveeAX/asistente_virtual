// ===================================================
// GESTOR MULTI-USUARIO PARA ASISTENTE KATA
// ===================================================

// Variables globales
let currentUser = null;
let systemData = null;

document.addEventListener('DOMContentLoaded', function() {
    // Inicializar sistema
    initializeSystem();
    
    // Setup event listeners
    setupEventListeners();
});

// ===================================================
// INICIALIZACIÓN DEL SISTEMA
// ===================================================

async function initializeSystem() {
    showMessage('Cargando sistema...', 'info');
    
    try {
        // Cargar estado del sistema
        await loadSystemStatus();
        
        // Cargar datos iniciales según la pestaña activa
        await loadInitialData();
        
        // Mostrar status bar
        document.getElementById('status-bar').style.display = 'block';
        
        showMessage('Sistema cargado correctamente', 'success');
        
        // Auto-hide success message
        setTimeout(() => hideMessage(), 3000);
        
    } catch (error) {
        console.error('Error inicializando sistema:', error);
        showMessage('Error cargando el sistema: ' + error.message, 'error');
    }
}

async function loadSystemStatus() {
    try {
        const response = await fetch('/api/system/status');
        const data = await response.json();
        
        if (data.success) {
            systemData = data.system;
            
            // Actualizar status bar
            document.getElementById('current-user-display').innerHTML = 
                `👤 Usuario: <strong>${systemData.current_user}</strong>`;
            
            // Actualizar dashboard si estamos en la pestaña de usuarios
            updateUserDashboard(data);
            
        } else {
            throw new Error(data.error || 'Error obteniendo estado del sistema');
        }
    } catch (error) {
        console.error('Error cargando estado del sistema:', error);
        throw error;
    }
}

async function loadInitialData() {
    const activeTab = document.querySelector('.tab-content.active').id;
    
    switch (activeTab) {
        case 'usuarios-tab':
            await loadUsersData();
            break;
        case 'configuracion-tab':
            await loadSettings();
            break;
        case 'recordatorios-tab':
            await loadReminders();
            break;
        case 'tareas-tab':
            await loadTasks();
            break;
        case 'contactos-tab':
            await loadContacts();
            break;
    }
}

// ===================================================
// GESTIÓN DE PESTAÑAS
// ===================================================

function showTab(tabName) {
    // Ocultar todas las pestañas
    document.querySelectorAll('.tab-content').forEach(tab => {
        tab.classList.remove('active');
    });
    
    // Desactivar todos los botones
    document.querySelectorAll('.tab-button').forEach(btn => {
        btn.classList.remove('active');
    });
    
    // Mostrar pestaña seleccionada
    document.getElementById(tabName + '-tab').classList.add('active');
    
    // Activar botón correspondiente
    event.target.classList.add('active');
    
    // Cargar datos específicos de la pestaña
    loadInitialData();
}

// ===================================================
// GESTIÓN DE USUARIOS
// ===================================================

async function loadUsersData() {
    try {
        // Cargar lista de usuarios
        const usersResponse = await fetch('/api/users');
        const usersData = await usersResponse.json();
        
        if (usersData.success) {
            displayUsersList(usersData.users);
            updateUserDashboard(usersData);
        }
        
        // Cargar usuario actual
        const currentUserResponse = await fetch('/api/users/current');
        const currentUserData = await currentUserResponse.json();
        
        if (currentUserData.success) {
            currentUser = currentUserData.user;
        }
        
    } catch (error) {
        console.error('Error cargando datos de usuarios:', error);
        showMessage('Error cargando usuarios: ' + error.message, 'error');
    }
}

function updateUserDashboard(data) {
    if (data.users) {
        document.getElementById('total-users').textContent = data.users.length;
        
        const currentUserData = data.users.find(u => u.is_current);
        if (currentUserData) {
            document.getElementById('current-user-name').textContent = currentUserData.username;
            document.getElementById('user-preferences').textContent = currentUserData.preferences_count || 0;
        }
    }
    
    if (data.system) {
        document.getElementById('total-backups').textContent = data.system.total_backups || 0;
    }
}

function displayUsersList(users) {
    const container = document.getElementById('users-list');
    container.innerHTML = '';
    
    users.forEach(user => {
        const userCard = document.createElement('div');
        userCard.className = `user-card ${user.is_current ? 'current-user' : ''}`;
        
        userCard.innerHTML = `
            <div class="user-info">
                <div>
                    <div class="user-name">
                        ${user.display_name}
                        ${user.is_current ? '<span class="current-user-indicator">Actual</span>' : ''}
                    </div>
                    <div class="user-stats">
                        Usuario: ${user.username} | 
                        Preferencias: ${user.preferences_count || 0} | 
                        Recordatorios: ${user.reminders_count || 0} | 
                        Contactos: ${user.contacts_count || 0}
                    </div>
                </div>
                <div class="user-actions">
                    ${!user.is_current ? `<button class="btn btn-primary" onclick="switchToUser('${user.username}')">Cambiar</button>` : ''}
                    <button class="btn btn-warning" onclick="backupUser('${user.username}')">Backup</button>
                    <button class="btn btn-success" onclick="editUser('${user.username}')">Editar</button>
                    ${!user.is_current ? `<button class="btn btn-danger" onclick="deleteUser('${user.username}')">Eliminar</button>` : ''}
                </div>
            </div>
        `;
        
        container.appendChild(userCard);
    });
}

function formatCategoryName(category) {
    const names = {
        'usuario': '👤 Información Personal',
        'contexto_cultural': '🌍 Contexto Cultural',
        'mascotas': '🐕 Mascotas',
        'intereses': '🎨 Intereses y Hobbies',
        'religion': '⛪ Información Religiosa',
        'ejemplos_personalizacion': '💬 Personalización de Conversación'
    };
    return names[category] || category.replace('_', ' ').toUpperCase();
}

function formatPreferenceKey(key) {
    return key.replace('_', ' ').replace(/\b\w/g, l => l.toUpperCase());
}

function formatPreferenceValue(value) {
    if (typeof value === 'object') {
        return JSON.stringify(value);
    }
    return value.toString();
}

async function updatePreference(category, key, value) {
    try {
        // Obtener preferencias actuales de la categoría
        const response = await fetch(`/api/preferences/${category}`);
        const data = await response.json();
        
        if (!data.success) {
            throw new Error(data.error);
        }
        
        // Actualizar el valor
        const preferences = data.preferences || {};
        
        // Intentar parsear como JSON si es necesario
        try {
            preferences[key] = JSON.parse(value);
        } catch {
            preferences[key] = value;
        }
        
        // Guardar preferencias actualizadas
        const updateResponse = await fetch(`/api/preferences/${category}`, {
            method: 'PUT',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify(preferences)
        });
        
        const updateData = await updateResponse.json();
        
        if (updateData.success) {
            showMessage(`Preferencia ${key} actualizada`, 'success');
            setTimeout(hideMessage, 2000);
        } else {
            throw new Error(updateData.error);
        }
        
    } catch (error) {
        console.error('Error actualizando preferencia:', error);
        showMessage('Error actualizando preferencia: ' + error.message, 'error');
    }
}

async function switchToUser(username) {
    if (!confirm(`¿Cambiar al usuario '${username}'? Esto requerirá reiniciar el sistema.`)) {
        return;
    }
    
    try {
        const response = await fetch('/api/users/switch', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ username: username })
        });
        
        const data = await response.json();
        
        if (data.success) {
            showMessage(`Usuario cambiado a '${username}'. El sistema necesita reiniciarse.`, 'info');
            
            // Recargar página después de 3 segundos
            setTimeout(() => {
                window.location.reload();
            }, 3000);
        } else {
            throw new Error(data.error);
        }
        
    } catch (error) {
        console.error('Error cambiando usuario:', error);
        showMessage('Error cambiando usuario: ' + error.message, 'error');
    }
}

async function backupUser(username) {
    try {
        showMessage(`Creando backup para ${username}...`, 'info');
        
        const response = await fetch(`/api/users/${username}/backup`, {
            method: 'POST'
        });
        
        const data = await response.json();
        
        if (data.success) {
            showMessage(`Backup creado: ${data.backup_file || 'archivo generado'}`, 'success');
        } else {
            throw new Error(data.error);
        }
        
    } catch (error) {
        console.error('Error creando backup:', error);
        showMessage('Error creando backup: ' + error.message, 'error');
    }
}

function editUser(username) {
    // Por ahora, simplemente mostrar mensaje
    showMessage(`Función de edición para ${username} estará disponible pronto`, 'info');
}

// ===================================================
// EVENT LISTENERS
// ===================================================

function setupEventListeners() {
    // Formulario de crear usuario
    const createUserForm = document.getElementById('create-user-form');
    if (createUserForm) {
        createUserForm.addEventListener('submit', handleCreateUser);
    }
    
    // Formularios existentes
    const settingsForm = document.getElementById('settings-form');
    if (settingsForm) {
        settingsForm.addEventListener('submit', handleSaveSettings);
    }
    
    
    const addContactForm = document.getElementById('add-contact-form');
    if (addContactForm) {
        addContactForm.addEventListener('submit', handleAddContact);
    }
    
    const addReminderForm = document.getElementById('add-reminder-form');
    if (addReminderForm) {
        addReminderForm.addEventListener('submit', handleAddReminder);
    }
    
    const addTaskForm = document.getElementById('add-task-form');
    if (addTaskForm) {
        addTaskForm.addEventListener('submit', handleAddTask);
    }
    
    // Event delegation para botones dinámicos
    document.addEventListener('click', function(e) {
        if (e.target.classList.contains('delete-btn')) {
            handleDelete(e.target.dataset.id, e.target.dataset.type);
        }
    });
}

async function handleCreateUser(event) {
    event.preventDefault();
    
    const formData = {
        username: document.getElementById('new-username').value.trim().toLowerCase(),
        display_name: document.getElementById('new-display-name').value.trim()
    };
    
    try {
        const response = await fetch('/api/users/create', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify(formData)
        });
        
        const data = await response.json();
        
        if (data.success) {
            showMessage(`Usuario '${formData.username}' creado exitosamente`, 'success');
            
            // Limpiar formulario
            event.target.reset();
            
            // Recargar lista de usuarios
            await loadUsersData();
        } else {
            throw new Error(data.error);
        }
        
    } catch (error) {
        console.error('Error creando usuario:', error);
        showMessage('Error creando usuario: ' + error.message, 'error');
    }
}


// ===================================================
// FUNCIONES LEGACY (ADAPTADAS)
// ===================================================

async function loadSettings() {
    try {
        // Cargar voces disponibles
        const voicesResponse = await fetch('/api/available-voices');
        const voices = await voicesResponse.json();
        
        const voiceSelect = document.getElementById('voice-select');
        voiceSelect.innerHTML = '';
        
        for (const [name, id] of Object.entries(voices)) {
            const option = document.createElement('option');
            option.value = id;
            option.textContent = name;
            voiceSelect.appendChild(option);
        }
        
        // Cargar configuración actual
        const settingsResponse = await fetch('/api/settings');
        const settings = await settingsResponse.json();
        voiceSelect.value = settings.voice_name;
        
        
    } catch (error) {
        console.error('Error cargando configuración:', error);
        showMessage('Error cargando configuración: ' + error.message, 'error');
    }
}

async function handleSaveSettings(event) {
    event.preventDefault();
    
    const settings = {
        voice_name: document.getElementById('voice-select').value
    };
    
    try {
        const response = await fetch('/api/settings', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify(settings)
        });
        
        const data = await response.json();
        
        if (data.success) {
            showMessage('Configuración guardada', 'success');
        } else {
            throw new Error('Error guardando configuración');
        }
        
    } catch (error) {
        console.error('Error guardando configuración:', error);
        showMessage('Error guardando configuración: ' + error.message, 'error');
    }
}

async function loadContacts() {
    try {
        const response = await fetch('/api/contacts');
        const data = await response.json();
        
        const list = document.getElementById('contact-list-body');
        list.innerHTML = '';
        
        data.forEach(contact => {
            const row = list.insertRow();
            row.innerHTML = `
                <td>${contact.displayName || contact.display_name}</td>
                <td>${Array.isArray(contact.aliases) ? contact.aliases.join(', ') : contact.aliases}</td>
                <td>${contact.details || contact.contact_details}</td>
                <td>${contact.isEmergency || contact.is_emergency ? 'Sí' : 'No'}</td>
                <td><button class="delete-btn" data-id="${contact.id}" data-type="contact">Eliminar</button></td>
            `;
        });
        
    } catch (error) {
        console.error('Error cargando contactos:', error);
        showMessage('Error cargando contactos: ' + error.message, 'error');
    }
}

async function handleAddContact(event) {
    event.preventDefault();
    
    const contactData = {
        displayName: document.getElementById('displayName').value,
        aliases: document.getElementById('aliases').value.split(',').map(s => s.trim()),
        details: document.getElementById('details').value,
        isEmergency: document.getElementById('isEmergency').value === 'true'
    };
    
    try {
        const response = await fetch('/api/contacts/add', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify(contactData)
        });
        
        const data = await response.json();
        
        if (data.success) {
            showMessage('Contacto agregado', 'success');
            event.target.reset();
            await loadContacts();
        } else {
            throw new Error(data.error || 'Error agregando contacto');
        }
        
    } catch (error) {
        console.error('Error agregando contacto:', error);
        showMessage('Error agregando contacto: ' + error.message, 'error');
    }
}

async function loadReminders() {
    try {
        const response = await fetch('/api/reminders');
        const data = await response.json();
        
        const list = document.getElementById('reminder-list-body');
        list.innerHTML = '';
        
        data.forEach(reminder => {
            const row = list.insertRow();
            const times = Array.isArray(reminder.times) ? reminder.times.join(', ') : reminder.times;
            const days = Array.isArray(reminder.days_of_week) ? reminder.days_of_week.join(', ') : reminder.days_of_week;
            
            row.innerHTML = `
                <td>${reminder.name || reminder.medication_name}</td>
                <td>${reminder.cantidad || '-'}</td>
                <td>${times}</td>
                <td>${days}</td>
                <td><button class="delete-btn" data-id="${reminder.id}" data-type="reminder">Eliminar</button></td>
            `;
        });
        
    } catch (error) {
        console.error('Error cargando recordatorios:', error);
        showMessage('Error cargando recordatorios: ' + error.message, 'error');
    }
}

async function handleAddReminder(event) {
    event.preventDefault();
    
    const formData = new FormData();
    formData.append('medication_name', document.getElementById('medicationName').value);
    formData.append('cantidad', document.getElementById('medicationQuantity').value);
    formData.append('prescripcion', document.getElementById('medicationPrescription').value);
    formData.append('times', document.getElementById('remindTimes').value);
    
    // Obtener días seleccionados
    const selectedDays = [];
    document.querySelectorAll('#remind-days input[type="checkbox"]:checked').forEach(checkbox => {
        selectedDays.push(checkbox.value);
    });
    formData.append('days_of_week', selectedDays.join(','));
    
    // Foto opcional
    const photoFile = document.getElementById('medicationPhoto').files[0];
    if (photoFile) {
        formData.append('photo', photoFile);
    }
    
    try {
        const response = await fetch('/api/reminders/add', {
            method: 'POST',
            body: formData
        });
        
        const data = await response.json();
        
        if (data.success) {
            showMessage('Recordatorio agregado', 'success');
            event.target.reset();
            await loadReminders();
        } else {
            throw new Error(data.error || 'Error agregando recordatorio');
        }
        
    } catch (error) {
        console.error('Error agregando recordatorio:', error);
        showMessage('Error agregando recordatorio: ' + error.message, 'error');
    }
}

async function loadTasks() {
    try {
        const response = await fetch('/api/tasks');
        const data = await response.json();
        
        const list = document.getElementById('task-list-body');
        list.innerHTML = '';
        
        data.forEach(task => {
            const row = list.insertRow();
            const times = Array.isArray(task.times) ? task.times.join(', ') : task.times;
            const days = Array.isArray(task.days_of_week) ? task.days_of_week.join(', ') : task.days_of_week;
            
            row.innerHTML = `
                <td>${task.name || task.task_name}</td>
                <td>${times}</td>
                <td>${days}</td>
                <td><button class="delete-btn" data-id="${task.id}" data-type="task">Eliminar</button></td>
            `;
        });
        
    } catch (error) {
        console.error('Error cargando tareas:', error);
        showMessage('Error cargando tareas: ' + error.message, 'error');
    }
}

async function handleAddTask(event) {
    event.preventDefault();
    
    const selectedDays = [];
    document.querySelectorAll('#task-days input[type="checkbox"]:checked').forEach(checkbox => {
        selectedDays.push(checkbox.value);
    });
    
    const taskData = {
        task_name: document.getElementById('taskName').value,
        times: document.getElementById('taskTimes').value,
        days_of_week: selectedDays.join(',')
    };
    
    try {
        const response = await fetch('/api/tasks/add', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify(taskData)
        });
        
        const data = await response.json();
        
        if (data.success) {
            showMessage('Tarea agregada', 'success');
            event.target.reset();
            await loadTasks();
        } else {
            throw new Error(data.error || 'Error agregando tarea');
        }
        
    } catch (error) {
        console.error('Error agregando tarea:', error);
        showMessage('Error agregando tarea: ' + error.message, 'error');
    }
}

async function handleDelete(id, type) {
    if (!confirm(`¿Eliminar este ${type}?`)) return;
    
    const endpoints = {
        'contact': '/api/contacts/delete',
        'reminder': '/api/reminders/delete',
        'task': '/api/tasks/delete'
    };
    
    try {
        const response = await fetch(endpoints[type], {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ id: id })
        });
        
        const data = await response.json();
        
        if (data.success) {
            showMessage(`${type.charAt(0).toUpperCase() + type.slice(1)} eliminado`, 'success');
            
            // Recargar datos correspondientes
            switch (type) {
                case 'contact': await loadContacts(); break;
                case 'reminder': await loadReminders(); break;
                case 'task': await loadTasks(); break;
            }
        } else {
            throw new Error(data.error || `Error eliminando ${type}`);
        }
        
    } catch (error) {
        console.error(`Error eliminando ${type}:`, error);
        showMessage(`Error eliminando ${type}: ` + error.message, 'error');
    }
}

// ===================================================
// SISTEMA DE MENSAJES
// ===================================================

function showMessage(text, type = 'info') {
    const messageArea = document.getElementById('message-area');
    
    // Limpiar mensajes anteriores
    messageArea.innerHTML = '';
    
    const alert = document.createElement('div');
    alert.className = `alert alert-${type}`;
    alert.textContent = text;
    
    messageArea.appendChild(alert);
    
    // Scroll to message
    alert.scrollIntoView({ behavior: 'smooth', block: 'nearest' });
}

function hideMessage() {
    const messageArea = document.getElementById('message-area');
    messageArea.innerHTML = '';
}

// ===================================================
// UTILIDADES
// ===================================================

function formatDate(dateString) {
    if (!dateString) return '-';
    return new Date(dateString).toLocaleDateString('es-ES');
}

function formatTime(timeString) {
    if (!timeString) return '-';
    return timeString;
}

// ===================================================
// FUNCIÓN PARA ELIMINAR USUARIOS
// ===================================================

async function deleteUser(username) {
    // Confirmar eliminación
    if (!confirm(`¿Estás seguro de que quieres eliminar el usuario "${username}"?\n\nEsta acción no se puede deshacer.`)) {
        return;
    }
    
    try {
        showMessage(`Eliminando usuario ${username}...`, 'info');
        
        const response = await fetch(`/api/users/${username}/delete`, {
            method: 'DELETE',
            headers: {
                'Content-Type': 'application/json'
            }
        });
        
        const data = await response.json();
        
        if (data.success) {
            showMessage(`Usuario "${username}" eliminado exitosamente`, 'success');
            
            // Recargar lista de usuarios
            await loadUsersData();
            
            // Auto-hide success message
            setTimeout(() => hideMessage(), 3000);
        } else {
            throw new Error(data.error || 'Error desconocido eliminando usuario');
        }
        
    } catch (error) {
        console.error('Error eliminando usuario:', error);
        showMessage('Error eliminando usuario: ' + error.message, 'error');
    }
}

// ===================================================
// MODAL DE EDICIÓN DE USUARIO
// ===================================================

// Estado del editor de usuario
const userEditor = {
    currentUser: null,
    originalData: {},
    pendingChanges: {},
    changeCount: 0,
    isOpen: false
};

async function openUserEditor(username) {
    if (!username) {
        showMessage('Error: No se especificó usuario para editar', 'error');
        return;
    }
    
    try {
        showMessage('Cargando datos del usuario...', 'info');
        
        // Cargar datos del usuario
        const response = await fetch(`/api/users/current`);
        const data = await response.json();
        
        if (!data.success) {
            throw new Error(data.error || 'Error cargando datos del usuario');
        }
        
        // Si no es el usuario actual, necesitamos cambiar primero
        if (data.user.username !== username) {
            showMessage('Cambiando a usuario seleccionado...', 'info');
            const switchResponse = await fetch('/api/users/switch', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ username: username })
            });
            
            const switchData = await switchResponse.json();
            if (!switchData.success) {
                throw new Error(switchData.error || 'Error cambiando de usuario');
            }
            
            // Recargar datos después del cambio
            const newResponse = await fetch(`/api/users/current`);
            const newData = await newResponse.json();
            
            if (!newData.success) {
                throw new Error(newData.error || 'Error recargando datos del usuario');
            }
            
            data.user = newData.user;
            data.preferences = newData.preferences;
        }
        
        // Configurar estado del editor
        userEditor.currentUser = username;
        userEditor.originalData = JSON.parse(JSON.stringify(data.preferences));
        userEditor.pendingChanges = {};
        userEditor.changeCount = 0;
        userEditor.isOpen = true;
        
        // Actualizar UI del modal
        document.getElementById('edit-username-display').textContent = data.user.display_name;
        
        // Cargar datos en el formulario
        loadUserDataToForm(data.preferences);
        
        // Mostrar modal
        document.getElementById('user-edit-modal').style.display = 'flex';
        
        // Configurar event listeners
        setupFormChangeListeners();
        
        hideMessage();
        
    } catch (error) {
        console.error('Error abriendo editor de usuario:', error);
        showMessage('Error abriendo editor: ' + error.message, 'error');
    }
}

function loadUserDataToForm(preferences) {
    // Cargar datos de usuario
    if (preferences.usuario) {
        const usuario = preferences.usuario;
        document.getElementById('edit-nombre').value = usuario.nombre || '';
        document.getElementById('edit-edad').value = usuario.edad || '';
        document.getElementById('edit-ciudad').value = usuario.ciudad || '';
        document.getElementById('edit-timezone').value = usuario.timezone || 'America/Guayaquil';
        document.getElementById('edit-idioma').value = usuario.idioma_preferido || 'es';
        document.getElementById('edit-verbose').value = usuario.modo_verbose ? 'true' : 'false';
    }
    
    // Cargar contexto cultural
    if (preferences.contexto_cultural) {
        const ctx = preferences.contexto_cultural;
        document.getElementById('edit-pais').value = ctx.pais || '';
        document.getElementById('edit-region').value = ctx.region || '';
        document.getElementById('edit-tradiciones').value = Array.isArray(ctx.tradiciones_conoce) 
            ? ctx.tradiciones_conoce.join(', ') : (ctx.tradiciones_conoce || '');
    }
    
    // Cargar mascotas
    if (preferences.mascotas) {
        const mascotas = preferences.mascotas;
        document.getElementById('edit-tiene-mascotas').value = mascotas.tiene_mascotas ? 'true' : 'false';
        document.getElementById('edit-tipo-mascota').value = mascotas.tipo || '';
        document.getElementById('edit-nombres-mascotas').value = Array.isArray(mascotas.nombres) 
            ? mascotas.nombres.join(', ') : (mascotas.nombres || '');
        togglePetFields();
    }
    
    // Cargar intereses
    if (preferences.intereses) {
        const intereses = preferences.intereses;
        document.getElementById('edit-hobbies').value = Array.isArray(intereses.hobbies_principales) 
            ? intereses.hobbies_principales.join(', ') : (intereses.hobbies_principales || '');
        document.getElementById('edit-musica').value = Array.isArray(intereses.musica_preferida) 
            ? intereses.musica_preferida.join(', ') : (intereses.musica_preferida || '');
        document.getElementById('edit-comidas').value = Array.isArray(intereses.comidas_favoritas) 
            ? intereses.comidas_favoritas.join(', ') : (intereses.comidas_favoritas || '');
        document.getElementById('edit-actividades').value = Array.isArray(intereses.actividades_sociales) 
            ? intereses.actividades_sociales.join(', ') : (intereses.actividades_sociales || '');
        document.getElementById('edit-entretenimiento').value = Array.isArray(intereses.entretenimiento) 
            ? intereses.entretenimiento.join(', ') : (intereses.entretenimiento || '');
        document.getElementById('edit-plantas').value = Array.isArray(intereses.plantas_conoce) 
            ? intereses.plantas_conoce.join(', ') : (intereses.plantas_conoce || '');
    }
    
    // Cargar religión
    if (preferences.religion) {
        const religion = preferences.religion;
        document.getElementById('edit-practica-religion').value = religion.practica ? 'true' : 'false';
        document.getElementById('edit-tipo-religion').value = religion.tipo || '';
        toggleReligionFields();
    }
    
    // Cargar personalización
    if (preferences.ejemplos_personalizacion) {
        const ejemplos = preferences.ejemplos_personalizacion;
        document.getElementById('edit-frases-cercanas').value = Array.isArray(ejemplos.frases_cercanas) 
            ? ejemplos.frases_cercanas.join(', ') : (ejemplos.frases_cercanas || '');
        
        // Contextos
        if (ejemplos.cuando_hablar_comida) {
            document.getElementById('edit-contexto-comida').value = ejemplos.cuando_hablar_comida.contexto || '';
            document.getElementById('edit-incluir-comida').value = Array.isArray(ejemplos.cuando_hablar_comida.incluir) 
                ? ejemplos.cuando_hablar_comida.incluir.join(', ') : (ejemplos.cuando_hablar_comida.incluir || '');
        }
        if (ejemplos.cuando_hablar_entretenimiento) {
            document.getElementById('edit-contexto-entretenimiento').value = ejemplos.cuando_hablar_entretenimiento.contexto || '';
            document.getElementById('edit-incluir-entretenimiento').value = Array.isArray(ejemplos.cuando_hablar_entretenimiento.incluir) 
                ? ejemplos.cuando_hablar_entretenimiento.incluir.join(', ') : (ejemplos.cuando_hablar_entretenimiento.incluir || '');
        }
        if (ejemplos.cuando_hablar_mascotas) {
            document.getElementById('edit-contexto-mascotas').value = ejemplos.cuando_hablar_mascotas.contexto || '';
            document.getElementById('edit-incluir-mascotas').value = Array.isArray(ejemplos.cuando_hablar_mascotas.incluir) 
                ? ejemplos.cuando_hablar_mascotas.incluir.join(', ') : (ejemplos.cuando_hablar_mascotas.incluir || '');
        }
        if (ejemplos.cuando_hablar_plantas) {
            document.getElementById('edit-contexto-plantas').value = ejemplos.cuando_hablar_plantas.contexto || '';
            document.getElementById('edit-incluir-plantas').value = Array.isArray(ejemplos.cuando_hablar_plantas.incluir) 
                ? ejemplos.cuando_hablar_plantas.incluir.join(', ') : (ejemplos.cuando_hablar_plantas.incluir || '');
        }
    }
}

function setupFormChangeListeners() {
    const form = document.getElementById('user-edit-form');
    const inputs = form.querySelectorAll('input, select, textarea');
    
    inputs.forEach(input => {
        input.addEventListener('input', trackFormChanges);
        input.addEventListener('change', trackFormChanges);
    });
}

function trackFormChanges(event) {
    const field = event.target;
    const fieldName = field.name;
    
    if (!fieldName) return;
    
    // Obtener valor original
    const originalValue = getOriginalValue(fieldName);
    const currentValue = field.value;
    
    // Verificar si cambió
    const hasChanged = originalValue !== currentValue;
    
    if (hasChanged) {
        if (!userEditor.pendingChanges[fieldName]) {
            userEditor.changeCount++;
        }
        userEditor.pendingChanges[fieldName] = currentValue;
        field.classList.add('changed');
    } else {
        if (userEditor.pendingChanges[fieldName]) {
            userEditor.changeCount--;
        }
        delete userEditor.pendingChanges[fieldName];
        field.classList.remove('changed');
    }
    
    updateChangesIndicator();
}

function getOriginalValue(fieldName) {
    const parts = fieldName.split('.');
    let value = userEditor.originalData;
    
    for (const part of parts) {
        if (value && typeof value === 'object' && value.hasOwnProperty(part)) {
            value = value[part];
        } else {
            return '';
        }
    }
    
    // Convertir arrays a strings
    if (Array.isArray(value)) {
        return value.join(', ');
    }
    
    return value ? value.toString() : '';
}

function updateChangesIndicator() {
    const indicator = document.getElementById('changes-indicator');
    const countElement = document.getElementById('changes-count');
    const saveButton = document.getElementById('save-changes-btn');
    
    countElement.textContent = userEditor.changeCount;
    
    if (userEditor.changeCount > 0) {
        indicator.style.display = 'flex';
        saveButton.disabled = false;
    } else {
        indicator.style.display = 'none';
        saveButton.disabled = true;
    }
}

function closeUserEditor() {
    if (userEditor.changeCount > 0) {
        if (!confirm('Tienes cambios sin guardar. ¿Estás seguro de que quieres cerrar el editor?')) {
            return;
        }
    }
    
    document.getElementById('user-edit-modal').style.display = 'none';
    userEditor.isOpen = false;
    userEditor.currentUser = null;
    userEditor.originalData = {};
    userEditor.pendingChanges = {};
    userEditor.changeCount = 0;
    
    // Limpiar clases de cambios
    const form = document.getElementById('user-edit-form');
    const inputs = form.querySelectorAll('input, select, textarea');
    inputs.forEach(input => {
        input.classList.remove('changed');
    });
}

function toggleCategory(categoryName) {
    const section = document.querySelector(`[data-category="${categoryName}"]`);
    const content = section.querySelector('.category-content');
    const toggle = section.querySelector('.category-toggle');
    
    // Verificar si está visible actualmente
    const isCurrentlyVisible = content.style.display === 'block' || 
                              (content.style.display === '' && section.classList.contains('expanded'));
    
    if (isCurrentlyVisible) {
        // Colapsar
        section.classList.remove('expanded');
        content.style.display = 'none';
        toggle.textContent = '+';
    } else {
        // Expandir
        section.classList.add('expanded');
        content.style.display = 'block';
        toggle.textContent = '−';
    }
}

function togglePetFields() {
    const tieneMascotas = document.getElementById('edit-tiene-mascotas').value === 'true';
    const petFields = document.querySelectorAll('.pet-field');
    
    petFields.forEach(field => {
        if (tieneMascotas) {
            field.classList.add('enabled');
        } else {
            field.classList.remove('enabled');
        }
    });
}

function toggleReligionFields() {
    const practicaReligion = document.getElementById('edit-practica-religion').value === 'true';
    const religionFields = document.querySelectorAll('.religion-field');
    
    religionFields.forEach(field => {
        if (practicaReligion) {
            field.classList.add('enabled');
        } else {
            field.classList.remove('enabled');
        }
    });
}

function cancelEditing() {
    closeUserEditor();
}

function resetForm() {
    if (!confirm('¿Estás seguro de que quieres resetear todos los campos a sus valores originales?')) {
        return;
    }
    
    loadUserDataToForm(userEditor.originalData);
    userEditor.pendingChanges = {};
    userEditor.changeCount = 0;
    updateChangesIndicator();
    
    // Limpiar clases de cambios
    const form = document.getElementById('user-edit-form');
    const inputs = form.querySelectorAll('input, select, textarea');
    inputs.forEach(input => {
        input.classList.remove('changed');
    });
    
    showMessage('Formulario reseteado a valores originales', 'info');
    setTimeout(hideMessage, 2000);
}

async function saveAllChanges() {
    if (userEditor.changeCount === 0) {
        showMessage('No hay cambios para guardar', 'info');
        return;
    }
    
    try {
        showMessage('Guardando cambios...', 'info');
        
        // Recopilar datos del formulario por categorías
        const categoriesData = {
            usuario: collectUserData(),
            contexto_cultural: collectContextoCulturalData(),
            mascotas: collectMascotasData(),
            intereses: collectInteresesData(),
            religion: collectReligionData(),
            ejemplos_personalizacion: collectPersonalizacionData()
        };
        
        // Guardar cada categoría que tenga cambios
        const savePromises = [];
        for (const [category, data] of Object.entries(categoriesData)) {
            if (hasChangesInCategory(category)) {
                savePromises.push(saveCategory(category, data));
            }
        }
        
        await Promise.all(savePromises);
        
        showMessage('Todos los cambios guardados exitosamente', 'success');
        
        // Actualizar datos originales
        userEditor.originalData = JSON.parse(JSON.stringify(categoriesData));
        userEditor.pendingChanges = {};
        userEditor.changeCount = 0;
        updateChangesIndicator();
        
        // Limpiar clases de cambios
        const form = document.getElementById('user-edit-form');
        const inputs = form.querySelectorAll('input, select, textarea');
        inputs.forEach(input => {
            input.classList.remove('changed');
        });
        
        // Recargar lista de usuarios
        setTimeout(async () => {
            await loadUsersData();
            closeUserEditor();
        }, 1500);
        
    } catch (error) {
        console.error('Error guardando cambios:', error);
        showMessage('Error guardando cambios: ' + error.message, 'error');
    }
}

function hasChangesInCategory(category) {
    return Object.keys(userEditor.pendingChanges).some(field => field.startsWith(category + '.'));
}

async function saveCategory(category, data) {
    const response = await fetch(`/api/preferences/${category}`, {
        method: 'PUT',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(data)
    });
    
    const result = await response.json();
    if (!result.success) {
        throw new Error(result.error || `Error guardando categoría ${category}`);
    }
    
    return result;
}

// Funciones para recopilar datos del formulario
function collectUserData() {
    return {
        nombre: document.getElementById('edit-nombre').value,
        edad: parseInt(document.getElementById('edit-edad').value) || 0,
        ciudad: document.getElementById('edit-ciudad').value,
        timezone: document.getElementById('edit-timezone').value,
        idioma_preferido: document.getElementById('edit-idioma').value,
        modo_verbose: document.getElementById('edit-verbose').value === 'true'
    };
}

function collectContextoCulturalData() {
    return {
        pais: document.getElementById('edit-pais').value,
        region: document.getElementById('edit-region').value,
        tradiciones_conoce: document.getElementById('edit-tradiciones').value
            .split(',').map(s => s.trim()).filter(s => s.length > 0)
    };
}

function collectMascotasData() {
    return {
        tiene_mascotas: document.getElementById('edit-tiene-mascotas').value === 'true',
        tipo: document.getElementById('edit-tipo-mascota').value,
        nombres: document.getElementById('edit-nombres-mascotas').value
            .split(',').map(s => s.trim()).filter(s => s.length > 0)
    };
}

function collectInteresesData() {
    return {
        hobbies_principales: document.getElementById('edit-hobbies').value
            .split(',').map(s => s.trim()).filter(s => s.length > 0),
        musica_preferida: document.getElementById('edit-musica').value
            .split(',').map(s => s.trim()).filter(s => s.length > 0),
        comidas_favoritas: document.getElementById('edit-comidas').value
            .split(',').map(s => s.trim()).filter(s => s.length > 0),
        actividades_sociales: document.getElementById('edit-actividades').value
            .split(',').map(s => s.trim()).filter(s => s.length > 0),
        entretenimiento: document.getElementById('edit-entretenimiento').value
            .split(',').map(s => s.trim()).filter(s => s.length > 0),
        plantas_conoce: document.getElementById('edit-plantas').value
            .split(',').map(s => s.trim()).filter(s => s.length > 0)
    };
}

function collectReligionData() {
    return {
        practica: document.getElementById('edit-practica-religion').value === 'true',
        tipo: document.getElementById('edit-tipo-religion').value
    };
}

function collectPersonalizacionData() {
    return {
        frases_cercanas: document.getElementById('edit-frases-cercanas').value
            .split(',').map(s => s.trim()).filter(s => s.length > 0),
        cuando_hablar_comida: {
            contexto: document.getElementById('edit-contexto-comida').value,
            incluir: document.getElementById('edit-incluir-comida').value
                .split(',').map(s => s.trim()).filter(s => s.length > 0)
        },
        cuando_hablar_entretenimiento: {
            contexto: document.getElementById('edit-contexto-entretenimiento').value,
            incluir: document.getElementById('edit-incluir-entretenimiento').value
                .split(',').map(s => s.trim()).filter(s => s.length > 0)
        },
        cuando_hablar_mascotas: {
            contexto: document.getElementById('edit-contexto-mascotas').value,
            incluir: document.getElementById('edit-incluir-mascotas').value
                .split(',').map(s => s.trim()).filter(s => s.length > 0)
        },
        cuando_hablar_plantas: {
            contexto: document.getElementById('edit-contexto-plantas').value,
            incluir: document.getElementById('edit-incluir-plantas').value
                .split(',').map(s => s.trim()).filter(s => s.length > 0)
        }
    };
}

// Exponer funciones globalmente para uso desde HTML
window.showTab = showTab;
window.switchToUser = switchToUser;
window.backupUser = backupUser;
window.editUser = openUserEditor; // Actualizar para usar el nuevo editor
window.updatePreference = updatePreference;
window.deleteUser = deleteUser;
window.openUserEditor = openUserEditor;
window.closeUserEditor = closeUserEditor;
window.toggleCategory = toggleCategory;
window.togglePetFields = togglePetFields;
window.toggleReligionFields = toggleReligionFields;
window.cancelEditing = cancelEditing;
window.resetForm = resetForm;
window.saveAllChanges = saveAllChanges;