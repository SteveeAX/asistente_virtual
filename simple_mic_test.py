# simple_mic_test.py (para probar JBL Tune 770NC a 16kHz)
import sounddevice as sd
import soundfile as sf
import logging
import time
import os
import numpy as np

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s: %(message)s')

# --- CONFIGURACIÓN PARA JBL A 16kHz ---
SAMPLE_RATE = 16000  # Tasa de muestreo para Porcupine y este micrófono
CHANNELS = 1
AUDIO_DTYPE = 'int16'
RECORD_SECONDS = 5   # Duración de la grabación
OUTPUT_FILENAME = "mic_test_JBL_16kHz.wav" # Nuevo nombre de archivo
# Intenta con "JBL", "Tune", "NC", o parte del nombre que veas en la lista de dispositivos
TARGET_MIC_NAME_SUBSTRING = "JBL" # AJUSTA ESTO SI ES NECESARIO

def list_audio_devices():
    logging.info("Listando dispositivos de audio disponibles:")
    logging.info("------------------------------------------------------------------------------------")
    logging.info("Índice | Nombre del Dispositivo                               | Entradas | Salidas")
    logging.info("-------|----------------------------------------------------|----------|----------")
    try:
        devices = sd.query_devices()
        if not devices: logging.warning("  No se encontraron dispositivos de audio."); return False
        found_input_devices = False
        for i, device in enumerate(devices):
            device_name = device.get('name', 'Nombre Desconocido')
            input_channels = device.get('max_input_channels', 0)
            output_channels = device.get('max_output_channels', 0)
            logging.info(f"  {i:<5} | {device_name:<50} | {input_channels:<8} | {output_channels:<8}")
            if input_channels > 0: found_input_devices = True

        if not found_input_devices:
            logging.warning("  No se encontraron dispositivos de ENTRADA (micrófonos) en la lista.")
            return False

        logging.info("------------------------------------------------------------------------------------")
        default_input_idx, default_output_idx = sd.default.device
        default_input_name = "Ninguno"
        default_output_name = "Ninguno"

        if default_input_idx != -1: default_input_name = sd.query_devices(default_input_idx)['name']
        if default_output_idx != -1: default_output_name = sd.query_devices(default_output_idx)['name']

        logging.info(f"Dispositivo de ENTRADA por defecto actual (sounddevice): Índice {default_input_idx} - '{default_input_name}'")
        logging.info(f"Dispositivo de SALIDA por defecto actual (sounddevice): Índice {default_output_idx} - '{default_output_name}'")
        return True
    except Exception as e:
        logging.error(f"No se pudieron consultar los dispositivos de audio: {e}")
        return False

def select_microphone_explicitly():
    try:
        devices = sd.query_devices()
        target_device_index = -1
        logging.info(f"Buscando micrófono que contenga '{TARGET_MIC_NAME_SUBSTRING}'...")
        for i, device in enumerate(devices):
            if TARGET_MIC_NAME_SUBSTRING.lower() in device.get('name', '').lower() and device.get('max_input_channels', 0) > 0:
                target_device_index = i
                logging.info(f"Micrófono objetivo '{TARGET_MIC_NAME_SUBSTRING}' encontrado: Dispositivo #{i} - {device.get('name')}")
                break

        if target_device_index != -1:
            current_default_output_device = sd.default.device[1]
            sd.default.device = (target_device_index, current_default_output_device)
            logging.info(f"Establecido como dispositivo de ENTRADA predeterminado: Dispositivo #{sd.default.device[0]} - '{sd.query_devices(sd.default.device[0])['name']}'")
            return True
        else:
            logging.warning(f"No se encontró micrófono con '{TARGET_MIC_NAME_SUBSTRING}'. Se usará el predeterminado del sistema si existe.")
            # Verificar si hay al menos un dispositivo de entrada por defecto
            if sd.default.device[0] == -1 : # No hay dispositivo de entrada por defecto
                logging.error("No hay un dispositivo de entrada por defecto y no se encontró el micrófono objetivo.")
                return False
            return True # Continuar con el default si existe
    except Exception as e:
        logging.error(f"Error al seleccionar micrófono '{TARGET_MIC_NAME_SUBSTRING}': {e}")
        return False

def record_audio_test():
    logging.info(f"Intentando grabar audio por {RECORD_SECONDS} segundos a {SAMPLE_RATE} Hz...")

    stream = None
    audio_data_list = []
    try:
        def audio_callback(indata, frames, time_info, status):
            if status:
                logging.warning(f"Callback status: {status}")
            audio_data_list.append(indata.copy())

        stream = sd.InputStream(
            samplerate=SAMPLE_RATE,
            # blocksize=None, # Dejar que sounddevice elija un blocksize para esta prueba general
            device=sd.default.device[0], # Usar el dispositivo de entrada configurado
            channels=CHANNELS,
            dtype=AUDIO_DTYPE,
            callback=audio_callback)

        stream.start()
        logging.info(f"InputStream iniciado a {SAMPLE_RATE}Hz. Grabando desde: '{sd.query_devices(sd.default.device[0])['name']}'...")
        time.sleep(RECORD_SECONDS + 0.5)

        if stream.active:
            stream.stop()
        logging.info("InputStream detenido.")

        if not audio_data_list:
            logging.warning("No se grabaron datos de audio.")
            return

        full_audio_data = np.concatenate(audio_data_list, axis=0)

        output_path = os.path.join(os.getcwd(), OUTPUT_FILENAME)
        sf.write(output_path, full_audio_data, SAMPLE_RATE)
        logging.info(f"Audio guardado en: {output_path}")
        print(f"\n¡Audio guardado en {output_path}! Por favor, verifica este archivo.")

    except sd.PortAudioError as pae:
        logging.error(f"Error de PortAudio durante la grabación a {SAMPLE_RATE}Hz: {pae}")
        logging.error("Verifica que el dispositivo seleccionado sea válido y la tasa de muestreo ({SAMPLE_RATE}Hz) sea compatible.")
    except Exception as e:
        logging.error(f"Ocurrió un error durante la grabación a {SAMPLE_RATE}Hz: {e}", exc_info=True)
    finally:
        if stream is not None and stream.active:
            stream.stop()
        if stream is not None:
            stream.close()
            logging.info("InputStream cerrado.")

if __name__ == '__main__':
    print(f"--- Prueba de Micrófono ({TARGET_MIC_NAME_SUBSTRING} a {SAMPLE_RATE} Hz) ---")
    if not list_audio_devices():
        print("No se pudieron listar los dispositivos de audio o no hay dispositivos de entrada. Saliendo.")
    else:
        print("-" * 70)
        if select_microphone_explicitly():
            print(f"Se intentará usar el micrófono que contenga '{TARGET_MIC_NAME_SUBSTRING}' (o el predeterminado si no se encuentra el objetivo pero existe un predeterminado).")
        else:
            print(f"ADVERTENCIA: No se pudo seleccionar el micrófono '{TARGET_MIC_NAME_SUBSTRING}' Y/O no hay un dispositivo de entrada predeterminado utilizable. La grabación podría fallar.")

        print("-" * 70)
        time.sleep(1)

        try:
            input(f"Presiona Enter para intentar grabar a {SAMPLE_RATE}Hz (archivo: {OUTPUT_FILENAME})...")
            record_audio_test()
        except KeyboardInterrupt:
            logging.info("\nPrueba cancelada.")
        except Exception as e_main:
            logging.error(f"Error en la ejecución principal de la prueba: {e_main}")
