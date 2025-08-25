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
        
        // Cargar usuario actual y sus preferencias
        const currentUserResponse = await fetch('/api/users/current');
        const currentUserData = await currentUserResponse.json();
        
        if (currentUserData.success) {
            currentUser = currentUserData.user;
            displayCurrentUserPreferences(currentUserData.preferences);
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
                </div>
            </div>
        `;
        
        container.appendChild(userCard);
    });
}

function displayCurrentUserPreferences(preferences) {
    const container = document.getElementById('current-user-preferences');
    container.innerHTML = '';
    
    if (!preferences || Object.keys(preferences).length === 0) {
        container.innerHTML = '<p>No se encontraron preferencias para el usuario actual.</p>';
        return;
    }
    
    const grid = document.createElement('div');
    grid.className = 'preferences-grid';
    
    Object.entries(preferences).forEach(([category, prefs]) => {
        const categoryDiv = document.createElement('div');
        categoryDiv.className = 'preference-category';
        
        categoryDiv.innerHTML = `
            <h4>${formatCategoryName(category)}</h4>
            <div class="preference-items">
                ${Object.entries(prefs).map(([key, value]) => `
                    <div class="preference-item">
                        <label>${formatPreferenceKey(key)}:</label>
                        <input type="text" 
                               data-category="${category}" 
                               data-key="${key}" 
                               value="${formatPreferenceValue(value)}"
                               onchange="updatePreference('${category}', '${key}', this.value)">
                    </div>
                `).join('')}
            </div>
        `;
        
        grid.appendChild(categoryDiv);
    });
    
    container.appendChild(grid);
}

function formatCategoryName(category) {
    const names = {
        'usuario': '👤 Usuario',
        'ia_generativa': '🤖 IA Generativa',
        'asistente': '🎯 Asistente',
        'intereses': '🎨 Intereses',
        'mascotas': '🐕 Mascotas',
        'comunicacion': '💬 Comunicación',
        'comandos_clasicos': '⌨️ Comandos Clásicos'
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
    
    const aiSettingsForm = document.getElementById('ai-settings-form');
    if (aiSettingsForm) {
        aiSettingsForm.addEventListener('submit', handleSaveAISettings);
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

async function handleSaveAISettings(event) {
    event.preventDefault();
    
    const aiSettings = {
        habilitada: document.getElementById('ai-enabled').value === 'true',
        temperatura: parseFloat(document.getElementById('ai-temperature').value),
        max_tokens_respuesta: parseInt(document.getElementById('ai-max-tokens').value)
    };
    
    try {
        const response = await fetch('/api/preferences/ia_generativa', {
            method: 'PUT',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify(aiSettings)
        });
        
        const data = await response.json();
        
        if (data.success) {
            showMessage('Configuración de IA guardada', 'success');
        } else {
            throw new Error(data.error);
        }
        
    } catch (error) {
        console.error('Error guardando configuración IA:', error);
        showMessage('Error guardando configuración IA: ' + error.message, 'error');
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
        
        // Cargar configuración de IA
        const aiResponse = await fetch('/api/preferences/ia_generativa');
        const aiData = await aiResponse.json();
        
        if (aiData.success && aiData.preferences) {
            const prefs = aiData.preferences;
            document.getElementById('ai-enabled').value = prefs.habilitada ? 'true' : 'false';
            document.getElementById('ai-temperature').value = prefs.temperatura || 0.3;
            document.getElementById('ai-max-tokens').value = prefs.max_tokens_respuesta || 150;
        }
        
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
            const days = Array.isArray(reminder.days) ? reminder.days.join(', ') : reminder.days;
            
            row.innerHTML = `
                <td>${reminder.name || reminder.medication_name}</td>
                <td>${reminder.quantity || '-'}</td>
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
            const days = Array.isArray(task.days) ? task.days.join(', ') : task.days;
            
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

// Exponer funciones globalmente para uso desde HTML
window.showTab = showTab;
window.switchToUser = switchToUser;
window.backupUser = backupUser;
window.editUser = editUser;
window.updatePreference = updatePreference;