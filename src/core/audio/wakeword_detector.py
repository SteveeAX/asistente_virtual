import os, logging, time, sounddevice as sd, pvporcupine, threading
from dotenv import load_dotenv
import numpy as np

logger = logging.getLogger(__name__)
load_dotenv()

PICOVOICE_ACCESS_KEY = "QDkOecdq8GT2AQ6iT4PpzQPk0HIhya85GeWOrmiMML6sfocR5pz/mQ=="
KEYWORD_FILE_NAME = "catalina_es_raspberry-pi_v3_0_0.ppn"
MODEL_FILE_NAME_ES = "porcupine_params_es.pv"

# Configuración dinámica de micrófono
TARGET_MIC_NAME_SUBSTRING = os.getenv('TARGET_MIC', 'ME6S')
CAPTURE_SAMPLE_RATE = int(os.getenv('MIC_SAMPLE_RATE', '48000'))
PORCUPINE_SAMPLE_RATE = 16000

_porcupine_handle = None; _audio_stream = None; _stop_listening_flag = False

def select_microphone():
    """
    Busca continuamente el micrófono configurado hasta encontrarlo.
    Se reconecta automáticamente si se desconecta.
    """
    previous_device_count = 0
    
    while True:
        try:
            devices = sd.query_devices()
            current_device_count = len(devices)
            
            # Solo mostrar dispositivos disponibles la primera vez o si cambia el número
            if current_device_count != previous_device_count:
                logger.info(f"WAKEWORD_INFO: Detectados {current_device_count} dispositivos de audio.")
                input_devices = [d for d in devices if d['max_input_channels'] > 0]
                logger.info("WAKEWORD_INFO: Dispositivos de entrada disponibles:")
                for i, device in enumerate(input_devices):
                    logger.info(f"  {i}: {device['name']} (canales: {device['max_input_channels']})")
                previous_device_count = current_device_count
            
            target_device_index = -1
            for i, device in enumerate(devices):
                if TARGET_MIC_NAME_SUBSTRING.lower() in device.get('name', '').lower():
                    target_device_index = i; break
            
            if target_device_index != -1:
                sd.default.device = (target_device_index, sd.default.device[1])
                logger.info(f"WAKEWORD_INFO: ¡Micrófono '{TARGET_MIC_NAME_SUBSTRING}' encontrado y configurado! → '{sd.query_devices(sd.default.device[0])['name']}'")
                return True
            else:
                # Solo mostrar warning cada 10 intentos para reducir spam
                if previous_device_count % 10 == 0:
                    logger.warning(f"WAKEWORD_WARNING: Micrófono '{TARGET_MIC_NAME_SUBSTRING}' no encontrado. Esperando conexión...")
                time.sleep(3)
                
        except Exception as e: 
            logger.error(f"WAKEWORD_ERROR: Error al buscar micrófono: {e}. Reintentando en 3 segundos...")
            time.sleep(3)

def init_porcupine():
    global _porcupine_handle
    try:
        base_dir = os.path.dirname(os.path.abspath(__file__))
        _porcupine_handle = pvporcupine.create(access_key=PICOVOICE_ACCESS_KEY, keyword_paths=[os.path.join(base_dir, KEYWORD_FILE_NAME)], model_path=os.path.join(base_dir, MODEL_FILE_NAME_ES))
        logger.info("WAKEWORD_INFO: Porcupine inicializado.")
        return True
    except Exception as e: logger.error(f"WAKEWORD_ERROR: Error inicializando Porcupine: {e}"); return False

def listen_for_wake_word(wake_word_detected_callback):
    global _audio_stream, _stop_listening_flag
    if not _porcupine_handle: return
    _stop_listening_flag = False
    
    # Asegurar que el micrófono ME6S esté conectado antes de continuar
    select_microphone()

    resample_factor = CAPTURE_SAMPLE_RATE // PORCUPINE_SAMPLE_RATE
    capture_blocksize = _porcupine_handle.frame_length * resample_factor

    while not _stop_listening_flag:
        try:
            _audio_stream = sd.InputStream(samplerate=CAPTURE_SAMPLE_RATE, channels=1, dtype='int16', blocksize=capture_blocksize)
            _audio_stream.start()
            logger.info(f"WAKEWORD_INFO: *** Escuchando por 'Catalina' con micrófono '{TARGET_MIC_NAME_SUBSTRING}' ***")
            
            while not _stop_listening_flag:
                pcm_frame = _audio_stream.read(capture_blocksize)[0]
                pcm_resampled = pcm_frame[::resample_factor]
                if _porcupine_handle.process(pcm_resampled.flatten().tolist()) >= 0:
                    logger.info("WAKEWORD_INFO: ¡Palabra clave detectada!")
                    if wake_word_detected_callback: wake_word_detected_callback()
                    break # Termina el bucle al detectar la palabra
                    
        except Exception as e:
            logger.error(f"WAKEWORD_ERROR: Error durante escucha (posible desconexión de micrófono): {e}")
            logger.info("WAKEWORD_INFO: Intentando reconectar micrófono...")
            
            # Cerrar stream actual si existe
            if _audio_stream:
                try:
                    if _audio_stream.active: _audio_stream.stop()
                    _audio_stream.close()
                except:
                    pass
                    
            # Buscar nuevamente el micrófono ME6S
            select_microphone()
            time.sleep(1)  # Breve pausa antes de reintentar
            continue
            
        finally:
            if _audio_stream:
                try:
                    if _audio_stream.active: _audio_stream.stop()
                    _audio_stream.close()
                except:
                    pass
        
        # Si llegamos aquí, salimos del bucle principal
        break
        
    logger.info("WAKEWORD_INFO: Proceso de escucha finalizado.")

def stop_listening():
    global _stop_listening_flag
    _stop_listening_flag = True

def pause_listening():
    """Pausa temporalmente la escucha de wake word y espera cierre completo - COMPORTAMIENTO ORIGINAL"""
    global _stop_listening_flag
    _stop_listening_flag = True
    logger.info("WAKEWORD_INFO: Wake word detector pausado temporalmente")
    
    # Esperar hasta 5 segundos para que se liberen los recursos completamente
    import time
    max_wait = 5.0
    wait_interval = 0.1
    elapsed = 0
    
    while elapsed < max_wait:
        # Verificar si hay hilos activos del wake word
        active_threads = [t for t in threading.enumerate() if 'WakeWord' in t.name]
        if not active_threads:
            logger.info("WAKEWORD_INFO: Todos los hilos de wake word terminados")
            break
        time.sleep(wait_interval)
        elapsed += wait_interval
    
    # Tiempo adicional para liberar recursos de audio
    time.sleep(1.0)
    logger.info(f"WAKEWORD_INFO: Pausa completa después de {elapsed:.1f}s")

def resume_listening(callback):
    """Reanuda la escucha de wake word con callback"""
    global _stop_listening_flag
    _stop_listening_flag = False
    logger.info("WAKEWORD_INFO: Wake word detector reanudado")
    
    # Reiniciar escucha en hilo separado
    threading.Thread(target=listen_for_wake_word, args=(callback,), daemon=True, name="WakeWordThread").start()
