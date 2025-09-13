from flask import Flask, jsonify, render_template, request
from datetime import datetime
import reminders
import logging
import os
import sys
import time
from werkzeug.utils import secure_filename

# === SISTEMA HÍBRIDO: COMPARTIDO + POR USUARIO ===
# - Medicamentos, tareas, contactos, configuración → BD compartida (todos los usuarios)
# - Solo preferencias de IA → BD por usuario
# Los endpoints de datos compartidos NO requieren @require_user_context

# === IMPORTAR SISTEMA MULTI-USUARIO ===
# Agregar directorio database al path
sys.path.append(os.path.join(os.path.dirname(__file__), 'database'))

try:
    from database.models.user_context import user_context_middleware, require_user_context
    from database.user_api import user_api
    from database.models.reminders_adapter import reminders_adapter
    MULTI_USER_AVAILABLE = True
    logging.info("Sistema multi-usuario cargado correctamente")
except ImportError as e:
    logging.warning(f"Sistema multi-usuario no disponible: {e}")
    MULTI_USER_AVAILABLE = False
    reminders_adapter = None
    
    # Decorador dummy para compatibilidad
    def require_user_context(f):
        return f

log = logging.getLogger('werkzeug')
log.setLevel(logging.ERROR)

app = Flask(__name__)

# === CONFIGURAR SISTEMA MULTI-USUARIO ===
if MULTI_USER_AVAILABLE:
    # Configurar middleware de contexto de usuario
    user_context_middleware.init_app(app)
    
    # Registrar Blueprint de APIs de usuario
    app.register_blueprint(user_api)
    
    logging.info("Sistema multi-usuario configurado en Flask")
else:
    logging.warning("Aplicación Flask ejecutándose SIN sistema multi-usuario")

# === FUNCIÓN HELPER PARA REMINDERS ===
def get_reminders_service():
    """
    Obtiene el servicio de recordatorios (ahora siempre sistema compartido).
    
    Returns:
        El servicio de recordatorios a usar (datos compartidos)
    """
    if MULTI_USER_AVAILABLE and reminders_adapter:
        return reminders_adapter  # Ahora redirige a BD compartida
    else:
        return reminders  # Fallback legacy

# --- CONFIGURACIÓN PARA SUBIDA DE ARCHIVOS ---
UPLOAD_FOLDER = os.path.join(os.path.dirname(__file__), 'uploads')
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER
if not os.path.exists(UPLOAD_FOLDER):
    os.makedirs(UPLOAD_FOLDER)

# Ruta al archivo de señal
SETTINGS_FLAG_PATH = os.path.join(os.path.dirname(__file__), "settings_updated.flag")

# Lista de voces predefinidas
AVAILABLE_VOICES = {
    "Femenina 1 (Neural2)": "es-US-Neural2-A",
    "Femenina 2 (WaveNet)": "es-US-Wavenet-A",
    "Femenina 3 (WaveNet)": "es-US-Wavenet-C",
    "Masculina 1 (Neural2)": "es-US-Neural2-B",
    "Masculina 2 (WaveNet)": "es-US-Wavenet-B",
}

@app.route('/', methods=['GET'])
def index():
    return render_template('index.html')

# --- API de Contactos (COMPARTIDOS) ---
@app.route('/api/contacts', methods=['GET'])
def get_contacts():
    service = get_reminders_service()
    return jsonify(service.list_contacts())

@app.route('/api/contacts/add', methods=['POST'])
def add_contact_route():
    data = request.json
    try:
        service = get_reminders_service()
        service.add_contact(data['displayName'], data['aliases'], 'telegram', data['details'], data['isEmergency'])
        return jsonify({"success": True})
    except Exception as e:
        return jsonify({"success": False, "error": str(e)}), 500

@app.route('/api/contacts/delete', methods=['POST'])
def delete_contact_route():
    data = request.json
    try:
        service = get_reminders_service()
        service.delete_contact(data['id'])
        return jsonify({"success": True})
    except Exception as e:
        return jsonify({"success": False, "error": str(e)}), 500

# --- API de Recordatorios (COMPARTIDOS) ---
@app.route('/api/reminders', methods=['GET'])
def get_reminders():
    service = get_reminders_service()
    return jsonify(service.list_reminders())

@app.route('/api/reminders/add', methods=['POST'])
def add_reminder_route():
    try:
        medication_name = request.form['medication_name']
        cantidad = request.form.get('cantidad', '').strip()  # Nuevo campo opcional
        prescripcion = request.form.get('prescripcion', '').strip()  # Nuevo campo opcional
        times = request.form['times']
        days_of_week = request.form['days_of_week']
        photo_path = ""
        if 'photo' in request.files and request.files['photo'].filename != '':
            file = request.files['photo']
            filename = secure_filename(f"{int(time.time())}_{file.filename}")
            photo_path = os.path.join(app.config['UPLOAD_FOLDER'], filename)
            file.save(photo_path)
        
        # Pasar los nuevos campos a la función add_reminder
        service = get_reminders_service()
        service.add_reminder(medication_name, photo_path, times, days_of_week, cantidad, prescripcion)
        
        if os.path.exists(SETTINGS_FLAG_PATH): os.remove(SETTINGS_FLAG_PATH)
        with open(SETTINGS_FLAG_PATH, 'w') as f: f.write('update_scheduler')
        return jsonify({"success": True})
    except Exception as e:
        logging.error(f"Error al añadir recordatorio: {e}")
        return jsonify({"success": False, "error": str(e)}), 500

@app.route('/api/reminders/delete', methods=['POST'])
def delete_reminder_route():
    data = request.json
    try:
        service = get_reminders_service()
        service.delete_reminder(data['id'])
        if os.path.exists(SETTINGS_FLAG_PATH): os.remove(SETTINGS_FLAG_PATH)
        with open(SETTINGS_FLAG_PATH, 'w') as f: f.write('update_scheduler')
        return jsonify({"success": True})
    except Exception as e:
        return jsonify({"success": False, "error": str(e)}), 500

# --- RUTAS PARA TAREAS (COMPARTIDAS) ---
@app.route('/api/tasks', methods=['GET'])
def get_tasks():
    try:
        service = get_reminders_service()
        tasks = service.list_tasks()
        return jsonify(tasks)
    except Exception as e:
        return jsonify({"success": False, "error": str(e)}), 500

@app.route('/api/tasks/add', methods=['POST'])
def add_task_route():
    data = request.json
    try:
        service = get_reminders_service()
        service.add_task(data['task_name'], data['times'], data['days_of_week'])
        if os.path.exists(SETTINGS_FLAG_PATH): os.remove(SETTINGS_FLAG_PATH)
        with open(SETTINGS_FLAG_PATH, 'w') as f: f.write('update_scheduler')
        return jsonify({"success": True})
    except Exception as e:
        return jsonify({"success": False, "error": str(e)}), 500

@app.route('/api/tasks/delete', methods=['POST'])
def delete_task_route():
    data = request.json
    try:
        service = get_reminders_service()
        service.delete_task(data['id'])
        if os.path.exists(SETTINGS_FLAG_PATH): os.remove(SETTINGS_FLAG_PATH)
        with open(SETTINGS_FLAG_PATH, 'w') as f: f.write('update_scheduler')
        return jsonify({"success": True})
    except Exception as e:
        return jsonify({"success": False, "error": str(e)}), 500
# --- FIN DE LAS RUTAS PARA TAREAS ---

# --- APIs de Configuración ---
@app.route('/api/available-voices', methods=['GET'])
def get_available_voices():
    return jsonify(AVAILABLE_VOICES)

@app.route('/api/settings', methods=['GET'])
def get_settings():
    service = get_reminders_service()
    return jsonify({'voice_name': service.get_setting('voice_name', 'es-US-Neural2-A')})

@app.route('/api/settings', methods=['POST'])
def save_settings():
    data = request.json
    try:
        service = get_reminders_service()
        service.set_setting('voice_name', data['voice_name'])
        if os.path.exists(SETTINGS_FLAG_PATH): os.remove(SETTINGS_FLAG_PATH)
        with open(SETTINGS_FLAG_PATH, 'w') as f:
            f.write('update_voice')
        return jsonify({"success": True})
    except Exception as e:
        return jsonify({"success": False, "error": str(e)}), 500

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000)
