import os
import logging
import asyncio
import telegram
import sounddevice as sd
import soundfile as sf
import threading

logger = logging.getLogger(__name__)

# --- CONFIGURACIÓN ---
BOT_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")
USER_NAME = os.getenv("USER_NAME", "el usuario") # Carga el nombre del .env

# --- CONFIGURACIÓN DE AUDIO ---
SAMPLE_RATE = 48000 # Usamos la tasa de muestreo alta del micrófono
RECORD_SECONDS = 15
AUDIO_FILENAME = "/tmp/emergency_clip.ogg" # Usamos /tmp para archivos temporales

def _send_alert_task(message: str, chat_id: str):
    """
    Tarea que se ejecuta en un hilo para no bloquear la aplicación principal.
    Envía el texto, graba el audio y luego envía el audio.
    """
    if not BOT_TOKEN or not chat_id:
        logger.error("EMERGENCY_MANAGER: El token del bot o el Chat ID no están configurados.")
        return False

    try:
        # --- 1. Enviar Alerta de Texto ---
        bot = telegram.Bot(token=BOT_TOKEN)
        asyncio.run(bot.send_message(chat_id=chat_id, text=message, parse_mode='Markdown'))
        logger.info(f"EMERGENCY_MANAGER: Alerta de texto enviada a Chat ID: {chat_id}")

        # --- 2. Grabar Audio del Entorno ---
        logger.info(f"EMERGENCY_MANAGER: Iniciando grabación de {RECORD_SECONDS} segundos...")
        audio_data = sd.rec(int(RECORD_SECONDS * SAMPLE_RATE), samplerate=SAMPLE_RATE, channels=1, dtype='int16')
        sd.wait()  # Espera a que la grabación termine
        
        # Guardar el archivo de audio en formato OGG (bueno para notas de voz)
        sf.write(AUDIO_FILENAME, audio_data, SAMPLE_RATE, format='ogg', subtype='vorbis')
        logger.info(f"EMERGENCY_MANAGER: Grabación guardada en {AUDIO_FILENAME}")

        # --- 3. Enviar Mensaje de Voz ---
        logger.info("EMERGENCY_MANAGER: Enviando clip de audio...")
        with open(AUDIO_FILENAME, 'rb') as audio_file:
            asyncio.run(bot.send_voice(chat_id=chat_id, voice=audio_file))
        logger.info("EMERGENCY_MANAGER: Clip de audio enviado exitosamente.")
        
        return True

    except Exception as e:
        logger.error(f"EMERGENCY_MANAGER: Falló el proceso de alerta. Error: {e}", exc_info=True)
        return False
    finally:
        # --- 4. Limpiar ---
        if os.path.exists(AUDIO_FILENAME):
            os.remove(AUDIO_FILENAME)
            logger.info(f"EMERGENCY_MANAGER: Archivo temporal {AUDIO_FILENAME} eliminado.")

def send_emergency_alert(message: str, chat_id: str):
    """
    Inicia el proceso de alerta en un hilo de fondo para no bloquear.
    """
    # Creamos y lanzamos un hilo para que la grabación no congele la app
    alert_thread = threading.Thread(target=_send_alert_task, args=(message, chat_id), daemon=True)
    alert_thread.start()
    return True # La función retorna inmediatamente

def send_medication_alert(medication_name: str, user_name: str = "Usuario"):
    """
    Envía alerta de medicamento no confirmado a TODOS los contactos de emergencia.
    Esta función se llama cuando el usuario NO confirma su medicamento en 5 minutos.
    """
    logger.info(f"MEDICATION_ALERT: Enviando alerta para medicamento '{medication_name}' de {user_name}")
    
    try:
        # Importar aquí para evitar dependencias circulares
        import reminders
        
        # Obtener todos los contactos de emergencia
        all_contacts = reminders.list_contacts()
        emergency_contacts = [contact for contact in all_contacts if contact.get('is_emergency', 0) == 1]
        
        if not emergency_contacts:
            logger.warning("MEDICATION_ALERT: No hay contactos de emergencia configurados")
            return False
        
        # Crear mensaje de alerta específico para medicamento
        from datetime import datetime
        current_time = datetime.now().strftime("%H:%M")
        current_date = datetime.now().strftime("%d/%m/%Y")
        
        alert_message = f"""🚨 ALERTA MEDICAMENTO 🚨

📍 {user_name} NO ha confirmado su medicamento:
💊 {medication_name}

🕐 Hora programada: {current_time}
📅 Fecha: {current_date}

⚠️ Han pasado más de 5 minutos sin confirmación.
Por favor, verifica que esté bien."""
        
        # Enviar a todos los contactos de emergencia
        alerts_sent = 0
        for contact in emergency_contacts:
            try:
                chat_id = contact['contact_details']
                send_emergency_alert(alert_message, chat_id)
                alerts_sent += 1
                logger.info(f"MEDICATION_ALERT: Alerta enviada a {contact['display_name']} ({chat_id})")
            except Exception as e:
                logger.error(f"MEDICATION_ALERT: Error enviando a {contact['display_name']}: {e}")
        
        logger.info(f"MEDICATION_ALERT: {alerts_sent}/{len(emergency_contacts)} alertas enviadas exitosamente")
        return alerts_sent > 0
        
    except Exception as e:
        logger.error(f"MEDICATION_ALERT: Error general enviando alertas de medicamento: {e}")
        return False

# --- Bloque de prueba ---
if __name__ == '__main__':
    logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
    from dotenv import load_dotenv
    load_dotenv()
    BOT_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")
    CHAT_ID = os.getenv("TELEGRAM_CHAT_ID")
    USER_NAME = os.getenv("USER_NAME", "el usuario")

    print("--- Probando el envío de alertas ---")
    
    print("\n1. Prueba de alerta de emergencia general:")
    test_message = f"🚨 *ALERTA DE EMERGENCIA (PRUEBA)* 🚨\nSe ha solicitado ayuda para *{USER_NAME}*.\nA continuación se enviará un audio."
    
    if CHAT_ID:
        send_emergency_alert(test_message, CHAT_ID)
        print("✅ Proceso de alerta iniciado. Revisa tu Telegram.")
        print(f"Se enviará un texto y luego un clip de audio de {RECORD_SECONDS} segundos.")
        
        print("\n2. Prueba de alerta de medicamento:")
        send_medication_alert("Aspirina (PRUEBA)", USER_NAME)
        print("✅ Proceso de alerta de medicamento iniciado")
        
        # Esperamos un poco más para dar tiempo a que el hilo termine en la prueba
        time.sleep(RECORD_SECONDS + 5)
    else:
        print("❌ No se encontró TELEGRAM_CHAT_ID en tu archivo .env para la prueba.")
