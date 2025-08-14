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

# --- Bloque de prueba ---
if __name__ == '__main__':
    logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
    from dotenv import load_dotenv
    load_dotenv()
    BOT_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")
    CHAT_ID = os.getenv("TELEGRAM_CHAT_ID")
    USER_NAME = os.getenv("USER_NAME", "el usuario")

    print("--- Probando el envío de alerta con audio ---")
    test_message = f"🚨 *ALERTA DE EMERGENCIA (PRUEBA)* 🚨\nSe ha solicitado ayuda para *{USER_NAME}*.\nA continuación se enviará un audio."
    
    if CHAT_ID:
        send_emergency_alert(test_message, CHAT_ID)
        print("Proceso de alerta iniciado. Revisa tu Telegram.")
        print(f"Se enviará un texto y luego un clip de audio de {RECORD_SECONDS} segundos.")
        # Esperamos un poco más para dar tiempo a que el hilo termine en la prueba
        time.sleep(RECORD_SECONDS + 5)
    else:
        print("No se encontró TELEGRAM_CHAT_ID en tu archivo .env para la prueba.")
