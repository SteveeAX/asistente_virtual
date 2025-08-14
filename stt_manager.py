import logging
import queue
import sounddevice as sd
from google.cloud import speech
import threading
import time

logger = logging.getLogger(__name__)

SAMPLE_RATE = 48000
CHUNK_SIZE = int(SAMPLE_RATE / 10)
TARGET_MIC_NAME_SUBSTRING = "ME6S"
LANGUAGE_CODE = "es-EC"

client_stt = speech.SpeechClient()

def select_microphone_stt():
    """
    Busca el micrófono ME6S para STT. Si no lo encuentra, sigue buscando.
    """
    attempt_count = 0
    while True:
        try:
            devices = sd.query_devices()
            target_device_index = -1
            for i, device in enumerate(devices):
                if TARGET_MIC_NAME_SUBSTRING.lower() in device.get('name', '').lower():
                    target_device_index = i; break
            
            if target_device_index != -1:
                sd.default.device = (target_device_index, sd.default.device[1])
                logger.info(f"STT_INFO: ¡Micrófono '{TARGET_MIC_NAME_SUBSTRING}' encontrado y configurado para STT!")
                return True
            else:
                attempt_count += 1
                # Solo mostrar warning cada 5 intentos para STT
                if attempt_count % 5 == 0:
                    logger.warning(f"STT_WARNING: Micrófono '{TARGET_MIC_NAME_SUBSTRING}' no encontrado para STT. Intento {attempt_count}...")
                time.sleep(2)
                
        except Exception as e: 
            logger.error(f"STT_ERROR: Error al buscar micrófono: {e}. Reintentando en 2 segundos...")
            time.sleep(2)

def stream_audio_and_transcribe(adaptation_phrases: list = None) -> str | None:
    # Asegurar que el micrófono ME6S esté disponible antes de iniciar STT
    select_microphone_stt()
    
    _audio_buffer = queue.Queue()
    transcript_result = [None]  # Usamos una lista para poder modificarla desde el hilo

    def _microphone_callback(indata, frames, time_info, status):
        if status: logger.warning(f"STT_MIC_STATUS: {status}")
        _audio_buffer.put(indata.tobytes())

    def _audio_generator():
        while True:
            chunk = _audio_buffer.get()
            if chunk is None: break
            yield speech.StreamingRecognizeRequest(audio_content=chunk)

    def stt_task():
        """La tarea que se ejecuta en un hilo y que podría bloquearse."""
        config = speech.RecognitionConfig(
            encoding=speech.RecognitionConfig.AudioEncoding.LINEAR16,
            sample_rate_hertz=SAMPLE_RATE,
            language_code=LANGUAGE_CODE,
            enable_automatic_punctuation=True,
            adaptation=speech.SpeechAdaptation(phrase_sets=[speech.PhraseSet(phrases=[speech.PhraseSet.Phrase(value=p) for p in adaptation_phrases])]) if adaptation_phrases else None
        )
        streaming_config = speech.StreamingRecognitionConfig(config=config, single_utterance=True)
        
        try:
            responses = client_stt.streaming_recognize(config=streaming_config, requests=_audio_generator())
            for response in responses:
                if response.results and response.results[0].alternatives and response.results[0].is_final:
                    transcript_result[0] = response.results[0].alternatives[0].transcript
                    logger.info(f"STT_INFO: Transcripción final recibida: '{transcript_result[0]}'")
                    break
        except Exception as e:
            # El error OutOfRange es normal si hay silencio
            if "OutOfRange" not in str(e):
                logger.error(f"STT_ERROR: Error en el hilo de streaming: {e}")
        finally:
            # Aseguramos que el generador termine
            _audio_buffer.put(None)

    # --- Lógica Principal con Timeout y Reconexión ---
    mic_stream = None
    max_retries = 3
    retry_count = 0
    
    while retry_count < max_retries:
        try:
            mic_stream = sd.InputStream(samplerate=SAMPLE_RATE, channels=1, dtype='int16', blocksize=CHUNK_SIZE, callback=_microphone_callback)
            mic_stream.start()
            logger.info(f"STT_INFO: Micrófono '{TARGET_MIC_NAME_SUBSTRING}' activado para transcripción. Escuchando...")

            stt_thread = threading.Thread(target=stt_task)
            stt_thread.start()
            
            # El hilo principal espera al hilo de STT con un timeout
            stt_thread.join(timeout=5.0)

            if stt_thread.is_alive():
                logger.warning("STT_WARNING: Timeout de escucha alcanzado. La tarea de STT no finalizó.")
            
            # Si llegamos aquí sin excepción, salimos del bucle de reintentos
            break
            
        except Exception as e:
            retry_count += 1
            logger.error(f"STT_ERROR: Error al gestionar el stream de audio (intento {retry_count}/{max_retries}): {e}")
            
            if mic_stream:
                try:
                    if mic_stream.active: mic_stream.stop()
                    mic_stream.close()
                except:
                    pass
                    
            if retry_count < max_retries:
                logger.info("STT_INFO: Reintentando reconexión del micrófono...")
                select_microphone_stt()
                time.sleep(1)
            else:
                logger.error("STT_ERROR: Máximo número de reintentos alcanzado.")
                
    # Limpieza final
    try:
        if mic_stream:
            if mic_stream.active: mic_stream.stop()
            mic_stream.close()
        # Nos aseguramos de que el generador termine si el hilo sigue vivo
        if _audio_buffer.empty():
            _audio_buffer.put(None)
    except:
        pass
        
    logger.info("STT_INFO: Micrófono desactivado.")
    return transcript_result[0]

def listen_for_confirmation(timeout=7) -> str:
    """
    Escucha directamente para confirmación sin wake word.
    Usado durante ventanas temporales de confirmación.
    Versión robusta con mejor manejo de recursos.
    """
    # Asegurar que el micrófono ME6S esté disponible con retry
    max_retries = 3
    for attempt in range(max_retries):
        try:
            select_microphone_stt()
            break
        except Exception as e:
            logger.warning(f"STT_CONFIRMATION: Intento {attempt + 1} de selección de micrófono falló: {e}")
            if attempt < max_retries - 1:
                time.sleep(1.0)  # Esperar antes del siguiente intento
            else:
                logger.error("STT_CONFIRMATION: No se pudo configurar micrófono después de 3 intentos")
                return ""
    
    _audio_buffer = queue.Queue()
    transcript_result = [None]
    listening_finished = threading.Event()

    def _microphone_callback(indata, frames, time_info, status):
        if status: logger.warning(f"STT_CONFIRMATION_STATUS: {status}")
        _audio_buffer.put(indata.tobytes())

    def _audio_generator():
        while not listening_finished.is_set():
            try:
                chunk = _audio_buffer.get(timeout=0.1)
                if chunk is None: break
                yield speech.StreamingRecognizeRequest(audio_content=chunk)
            except queue.Empty:
                continue

    def stt_confirmation_task():
        """Tarea STT específica para confirmación con timeout"""
        config = speech.RecognitionConfig(
            encoding=speech.RecognitionConfig.AudioEncoding.LINEAR16,
            sample_rate_hertz=SAMPLE_RATE,
            language_code=LANGUAGE_CODE,
            enable_automatic_punctuation=True
        )
        streaming_config = speech.StreamingRecognitionConfig(
            config=config, 
            single_utterance=True,
            interim_results=False
        )
        
        try:
            responses = client_stt.streaming_recognize(config=streaming_config, requests=_audio_generator())
            for response in responses:
                if response.results and response.results[0].alternatives and response.results[0].is_final:
                    transcript_result[0] = response.results[0].alternatives[0].transcript
                    logger.info(f"STT_CONFIRMATION: Respuesta recibida: '{transcript_result[0]}'")
                    listening_finished.set()
                    break
        except Exception as e:
            if "OutOfRange" not in str(e):
                logger.error(f"STT_CONFIRMATION_ERROR: {e}")
        finally:
            listening_finished.set()
            _audio_buffer.put(None)

    # Configurar micrófono con timeout
    mic_stream = None
    try:
        mic_stream = sd.InputStream(
            samplerate=SAMPLE_RATE, 
            channels=1, 
            dtype='int16', 
            blocksize=CHUNK_SIZE, 
            callback=_microphone_callback
        )
        mic_stream.start()
        logger.info(f"STT_CONFIRMATION: Escuchando confirmación por {timeout} segundos...")

        # Iniciar STT en hilo separado
        stt_thread = threading.Thread(target=stt_confirmation_task, daemon=True)
        stt_thread.start()
        
        # Esperar por timeout o resultado
        listening_finished.wait(timeout=timeout)
        
        # Terminar escucha
        listening_finished.set()
        
        if transcript_result[0] is None:
            logger.info("STT_CONFIRMATION: Timeout alcanzado sin respuesta")
            
    except Exception as e:
        logger.error(f"STT_CONFIRMATION_ERROR: Error durante escucha: {e}")
    finally:
        try:
            if mic_stream and mic_stream.active:
                mic_stream.stop()
                mic_stream.close()
        except:
            pass
        logger.info("STT_CONFIRMATION: Micrófono de confirmación desactivado")

    return transcript_result[0] or ""
