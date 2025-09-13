import logging
import queue
import sounddevice as sd
from google.cloud import speech
from google.protobuf import duration_pb2
import threading
import time
# from stt_domain_phrases import get_all_domain_phrases  # Archivo eliminado en limpieza
# from stt_post_processor import post_process_stt_text  # Archivo eliminado en limpieza

logger = logging.getLogger(__name__)

SAMPLE_RATE = 48000  # Requerido por micrófono ME6S
CHUNK_SIZE = int(SAMPLE_RATE / 10)  # 4800 samples - mejor para palabras cortas
TARGET_MIC_NAME_SUBSTRING = "ME6S"
LANGUAGE_CODE = "es-US"  # Mejor modelo de entrenamiento que es-EC

client_stt = speech.SpeechClient()

# Variables globales para optimización de micrófono
_current_mic_initialized = False
_current_mic_index = None

# Cache para configuración STT
_stt_config_cached = None

def get_stt_config(adaptation_phrases: list = None):
    """
    OPTIMIZACIÓN: Obtiene configuración STT con cache.
    Ahorra 1-2 segundos en la creación de la configuración.
    """
    global _stt_config_cached
    
    # Cache de configuración base (siempre igual)
    if not _stt_config_cached:
        _stt_config_cached = speech.RecognitionConfig(
            encoding=speech.RecognitionConfig.AudioEncoding.LINEAR16,
            sample_rate_hertz=SAMPLE_RATE,
            language_code=LANGUAGE_CODE,
            enable_automatic_punctuation=True,
            enable_word_time_offsets=True,  # Mejor alineación temporal
            model='latest_long',  # Modelo más reciente y preciso
            use_enhanced=True,  # Modelo mejorado cuando disponible
            profanity_filter=False  # Evita censura de palabras técnicas
        )
        logger.info("STT_INFO: Configuración STT cacheada - optimización aplicada")
    
    # Si no hay frases de adaptación, devolver configuración base
    if not adaptation_phrases:
        return _stt_config_cached
    
    # Crear nueva configuración con adaptación (no se puede cachear por las frases variables)
    config_with_adaptation = speech.RecognitionConfig(
        encoding=speech.RecognitionConfig.AudioEncoding.LINEAR16,
        sample_rate_hertz=SAMPLE_RATE,
        language_code=LANGUAGE_CODE,
        enable_automatic_punctuation=True,
        enable_word_time_offsets=True,
        model='latest_long',
        use_enhanced=True,
        profanity_filter=False,
        adaptation=speech.SpeechAdaptation(phrase_sets=[speech.PhraseSet(phrases=[
            speech.PhraseSet.Phrase(value=p, boost=10.0) for p in adaptation_phrases  # Boost de 10x
        ])])
    )
    
    return config_with_adaptation

def reset_microphone_cache():
    """
    Resetea el cache del micrófono. Útil para reconexión forzada.
    Llamar cuando se detecten problemas de conexión.
    """
    global _current_mic_initialized, _current_mic_index
    _current_mic_initialized = False
    _current_mic_index = None
    logger.info("STT_INFO: Cache de micrófono reseteado - próxima búsqueda será completa")

def select_microphone_stt():
    """
    Busca el micrófono ME6S para STT con optimización de cache.
    Mantiene funcionalidad completa de reconexión automática.
    """
    global _current_mic_initialized, _current_mic_index
    
    # OPTIMIZACIÓN: Verificación rápida si ya está configurado
    if _current_mic_initialized and _current_mic_index is not None:
        try:
            devices = sd.query_devices()
            if (_current_mic_index < len(devices) and 
                TARGET_MIC_NAME_SUBSTRING.lower() in devices[_current_mic_index]['name'].lower()):
                # Micrófono ya configurado y disponible - ahorro de 2-3 segundos
                logger.info(f"STT_INFO: Micrófono pre-configurado válido (índice {_current_mic_index}) - optimización aplicada")
                sd.default.device = (_current_mic_index, sd.default.device[1])
                return True
        except Exception as e:
            logger.warning(f"STT_WARNING: Error verificando micrófono pre-configurado: {e}")
            # Reset cache y continuar con búsqueda completa
            _current_mic_initialized = False
            _current_mic_index = None
    
    # BÚSQUEDA COMPLETA: Mantiene lógica original para reconexión
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
                
                # OPTIMIZACIÓN: Guardar en cache para próximas veces
                _current_mic_index = target_device_index
                _current_mic_initialized = True
                
                logger.info(f"STT_INFO: ¡Micrófono '{TARGET_MIC_NAME_SUBSTRING}' encontrado y configurado para STT! (guardado en cache)")
                return True
            else:
                attempt_count += 1
                # Solo mostrar warning cada 5 intentos para STT
                if attempt_count % 5 == 0:
                    logger.warning(f"STT_WARNING: Micrófono '{TARGET_MIC_NAME_SUBSTRING}' no encontrado para STT. Intento {attempt_count}...")
                time.sleep(2)
                
        except Exception as e: 
            logger.error(f"STT_ERROR: Error al buscar micrófono: {e}. Reintentando en 2 segundos...")
            # Reset cache en caso de error
            _current_mic_initialized = False
            _current_mic_index = None
            time.sleep(2)

def stream_audio_and_transcribe(adaptation_phrases: list = None) -> str | None:
    # Si no se proporcionan frases específicas, usar frases de dominio general
    if adaptation_phrases is None:
        adaptation_phrases = []  # Frases de dominio simplificadas por ahora
        logger.info(f"STT_INFO: Usando {len(adaptation_phrases)} frases de dominio para mejor precisión")
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
        # OPTIMIZACIÓN: Usar configuración cacheada
        config = get_stt_config(adaptation_phrases)
        # FALLBACK: VoiceActivityTimeout solo funciona en v1p1beta1, no en v1
        # Por ahora usar single_utterance=True que funciona bien
        streaming_config = speech.StreamingRecognitionConfig(
            config=config, 
            single_utterance=True,
            interim_results=True,  # ⚡ Resultados intermedios para mejor continuidad
            # TODO: Implementar VoiceActivityTimeout cuando migre a v1p1beta1
        )
        
        try:
            responses = client_stt.streaming_recognize(config=streaming_config, requests=_audio_generator())
            for response in responses:
                if response.results and response.results[0].alternatives and response.results[0].is_final:
                    raw_transcript = response.results[0].alternatives[0].transcript
                    # ⚡ POST-PROCESAR para corregir segmentación de palabras
                    transcript_result[0] = raw_transcript  # post_process_stt_text() - función eliminada en limpieza
                    logger.info(f"STT_INFO: Transcripción final recibida: '{transcript_result[0]}'")
                    if raw_transcript != transcript_result[0]:
                        logger.info(f"STT_CORRECTION: '{raw_transcript}' → '{transcript_result[0]}'")
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
            
            # El hilo principal espera al hilo de STT con un timeout más largo
            stt_thread.join(timeout=8.0)  # ⚡ Aumentado de 5s a 8s

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
        # OPTIMIZACIÓN: Usar configuración cacheada (sin phrases para confirmación)
        config = get_stt_config()
        # FALLBACK: VoiceActivityTimeout solo funciona en v1p1beta1, no en v1
        streaming_config = speech.StreamingRecognitionConfig(
            config=config, 
            single_utterance=True,
            interim_results=True,  # ⚡ Resultados intermedios para mejor continuidad
            # TODO: Implementar VoiceActivityTimeout cuando migre a v1p1beta1
        )
        
        try:
            responses = client_stt.streaming_recognize(config=streaming_config, requests=_audio_generator())
            for response in responses:
                if response.results and response.results[0].alternatives and response.results[0].is_final:
                    raw_transcript = response.results[0].alternatives[0].transcript
                    # ⚡ POST-PROCESAR para corregir segmentación de palabras
                    transcript_result[0] = raw_transcript  # post_process_stt_text() - función eliminada en limpieza
                    logger.info(f"STT_CONFIRMATION: Respuesta recibida: '{transcript_result[0]}'")
                    if raw_transcript != transcript_result[0]:
                        logger.info(f"STT_CORRECTION: '{raw_transcript}' → '{transcript_result[0]}'")
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
