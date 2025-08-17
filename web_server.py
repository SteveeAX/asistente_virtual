from flask import Flask, jsonify, render_template, request
from datetime import datetime
import reminders
import logging
import os
import time
from werkzeug.utils import secure_filename

log = logging.getLogger('werkzeug')
log.setLevel(logging.ERROR)

app = Flask(__name__)

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

# --- API de Contactos ---
@app.route('/api/contacts', methods=['GET'])
def get_contacts():
    return jsonify(reminders.list_contacts())

@app.route('/api/contacts/add', methods=['POST'])
def add_contact_route():
    data = request.json
    try:
        reminders.add_contact(data['displayName'], data['aliases'], 'telegram', data['details'], data['isEmergency'])
        return jsonify({"success": True})
    except Exception as e:
        return jsonify({"success": False, "error": str(e)}), 500

@app.route('/api/contacts/delete', methods=['POST'])
def delete_contact_route():
    data = request.json
    try:
        reminders.delete_contact(data['id'])
        return jsonify({"success": True})
    except Exception as e:
        return jsonify({"success": False, "error": str(e)}), 500

# --- API de Recordatorios ---
@app.route('/api/reminders', methods=['GET'])
def get_reminders():
    return jsonify(reminders.list_reminders())

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
        reminders.add_reminder(medication_name, photo_path, times, days_of_week, cantidad, prescripcion)
        
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
        reminders.delete_reminder(data['id'])
        if os.path.exists(SETTINGS_FLAG_PATH): os.remove(SETTINGS_FLAG_PATH)
        with open(SETTINGS_FLAG_PATH, 'w') as f: f.write('update_scheduler')
        return jsonify({"success": True})
    except Exception as e:
        return jsonify({"success": False, "error": str(e)}), 500

# --- NUEVAS RUTAS PARA TAREAS ---
@app.route('/api/tasks', methods=['GET'])
def get_tasks():
    try:
        tasks = reminders.list_tasks()
        return jsonify(tasks)
    except Exception as e:
        return jsonify({"success": False, "error": str(e)}), 500

@app.route('/api/tasks/add', methods=['POST'])
def add_task_route():
    data = request.json
    try:
        reminders.add_task(data['task_name'], data['times'], data['days_of_week'])
        if os.path.exists(SETTINGS_FLAG_PATH): os.remove(SETTINGS_FLAG_PATH)
        with open(SETTINGS_FLAG_PATH, 'w') as f: f.write('update_scheduler')
        return jsonify({"success": True})
    except Exception as e:
        return jsonify({"success": False, "error": str(e)}), 500

@app.route('/api/tasks/delete', methods=['POST'])
def delete_task_route():
    data = request.json
    try:
        reminders.delete_task(data['id'])
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
    return jsonify({'voice_name': reminders.get_setting('voice_name', 'es-US-Neural2-A')})

@app.route('/api/settings', methods=['POST'])
def save_settings():
    data = request.json
    try:
        reminders.set_setting('voice_name', data['voice_name'])
        if os.path.exists(SETTINGS_FLAG_PATH): os.remove(SETTINGS_FLAG_PATH)
        with open(SETTINGS_FLAG_PATH, 'w') as f:
            f.write('update_voice')
        return jsonify({"success": True})
    except Exception as e:
        return jsonify({"success": False, "error": str(e)}), 500

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000)
