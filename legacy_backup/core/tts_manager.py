# tts_manager.py (Corregido y listo para personalización)
import os
import uuid
import subprocess
import logging
import threading
import asyncio
import queue
import time
import re
from google.cloud import texttospeech

logger = logging.getLogger(__name__)
_client = texttospeech.TextToSpeechClient()
TMP_DIR = "/tmp"
DEFAULT_VOICE = "es-US-Neural2-A"

def clean_text_for_tts(text: str) -> str:
    """
    Limpia el texto para TTS removiendo caracteres que se pronuncian incorrectamente.
    Google TTS en español pronuncia muchos símbolos como texto literal.
    """
    if not text:
        return text
    
    cleaned = text
    
    # REMOVER símbolos problemáticos que Google TTS pronuncia literalmente
    cleaned = cleaned.replace("*", "")          # "asterisco"
    cleaned = cleaned.replace("#", "")          # "numeral" o "hashtag"  
    cleaned = cleaned.replace("_", "")          # "guión bajo"
    cleaned = cleaned.replace("|", "")          # "barra vertical"
    cleaned = cleaned.replace("~", "")          # "tilde"
    cleaned = cleaned.replace("`", "")          # "acento grave"
    cleaned = cleaned.replace("@", "")          # "arroba"
    cleaned = cleaned.replace("^", "")          # "circunflejo"
    cleaned = cleaned.replace("&", " y ")       # "ampersand" → "y"
    cleaned = cleaned.replace("+", " más ")     # "más"
    cleaned = cleaned.replace("=", " igual ")   # "igual"
    cleaned = cleaned.replace("<", " menor que ")  # "menor que"
    cleaned = cleaned.replace(">", " mayor que ")  # "mayor que"
    cleaned = cleaned.replace("[", "")          # "corchete izquierdo"
    cleaned = cleaned.replace("]", "")          # "corchete derecho"
    cleaned = cleaned.replace("{", "")          # "llave izquierda"
    cleaned = cleaned.replace("}", "")          # "llave derecha"
    cleaned = cleaned.replace("\\", "")         # "barra invertida"
    cleaned = cleaned.replace("/", "")          # "barra"
    
    # Símbolos con conversión específica
    cleaned = cleaned.replace("%", " por ciento")  # "porcentaje"
    cleaned = cleaned.replace("$", " pesos")       # "signo de peso"
    cleaned = cleaned.replace("€", " euros")       # "euros"
    cleaned = cleaned.replace("£", " libras")      # "libras"
    
    # SIGNOS DE PUNTUACIÓN problemáticos en español
    cleaned = cleaned.replace("¿", "")          # Abrir interrogación (se pronuncia)
    cleaned = cleaned.replace("¡", "")          # Abrir exclamación (se pronuncia)
    
    # Limpiar múltiples signos de puntuación consecutivos
    cleaned = re.sub(r'[!]{2,}', '!', cleaned)     # !!!! → !
    cleaned = re.sub(r'[?]{2,}', '?', cleaned)     # ???? → ?
    cleaned = re.sub(r'[.]{3,}', '...', cleaned)   # ...... → ...
    cleaned = re.sub(r'[.]{2}', '.', cleaned)      # .. → .
    
    # Limpiar comillas que se pronuncian
    cleaned = cleaned.replace('"', '')         # "comillas dobles"
    cleaned = cleaned.replace("'", '')         # "comilla simple"
    cleaned = cleaned.replace("«", '')         # "comilla española izq"
    cleaned = cleaned.replace("»", '')         # "comilla española der"
    
    # Limpiar espacios múltiples y caracteres de control
    cleaned = re.sub(r'\s+', ' ', cleaned)
    cleaned = cleaned.strip()
    
    return cleaned

def say(text: str, voice_name: str = None):
    """Genera y reproduce audio usando una voz específica."""
    selected_voice = voice_name if voice_name else DEFAULT_VOICE
    language_code = "-".join(selected_voice.split("-")[:2])
    filename = None
    
    # LIMPIAR TEXTO PARA TTS
    cleaned_text = clean_text_for_tts(text)
    
    # LOG DE RESPUESTA DEL ASISTENTE (mostrar texto original)
    logger.info(f"ASISTENTE_RESPUESTA: {text}")
    print(f"🔊 RESPUESTA: {text}")  # También mostrar en consola
    
    if cleaned_text != text:
        logger.debug(f"TTS_CLEANED: '{text}' → '{cleaned_text}'")
    
    logger.info(f"TTS: Generando audio con la voz: {selected_voice}")
    
    try:
        # 1. Generar audio con Google TTS (usar texto limpio)
        synthesis_input = texttospeech.SynthesisInput(text=cleaned_text)
        voice = texttospeech.VoiceSelectionParams(language_code=language_code, name=selected_voice)
        audio_config = texttospeech.AudioConfig(audio_encoding=texttospeech.AudioEncoding.MP3)
        response = _client.synthesize_speech(input=synthesis_input, voice=voice, audio_config=audio_config)
        
        # 2. Guardar archivo temporal
        filename = os.path.join(TMP_DIR, f"tts_{uuid.uuid4().hex}.mp3")
        with open(filename, "wb") as out:
            out.write(response.audio_content)
        
        logger.info(f"TTS: Archivo de audio creado: {filename}")
        
        # 3. Reproducir con timeout para evitar bloqueos
        logger.info("TTS: Iniciando reproducción con mpg123...")
        result = subprocess.run(
            ["mpg123", "-q", filename], 
            timeout=30,  # Timeout de 30 segundos
            capture_output=True,
            text=True
        )
        
        if result.returncode == 0:
            logger.info("TTS: Reproducción completada exitosamente")
        else:
            logger.warning(f"TTS: mpg123 terminó con código {result.returncode}")
            if result.stderr:
                logger.warning(f"TTS: Error de mpg123: {result.stderr}")
                
    except subprocess.TimeoutExpired:
        logger.error("TTS_ERROR: Timeout en reproducción de audio (30s) - mpg123 no respondió")
        
    except FileNotFoundError as e:
        logger.error(f"TTS_ERROR: mpg123 no encontrado. Instalar con: sudo apt install mpg123. Error: {e}")
        
    except Exception as e:
        logger.error(f"TTS_ERROR: No se pudo generar o reproducir el audio. Error: {e}")
        
    finally:
        # Limpiar archivo temporal siempre
        if filename and os.path.exists(filename):
            try:
                os.remove(filename)
                logger.debug(f"TTS: Archivo temporal eliminado: {filename}")
            except Exception as e:
                logger.warning(f"TTS: No se pudo eliminar archivo temporal {filename}: {e}")
                
        logger.info("TTS: Proceso TTS finalizado")

def say_async(text: str, voice_name: str = None):
    """
    Genera y reproduce audio de forma asíncrona para no bloquear el sistema.
    El sistema queda listo inmediatamente para el siguiente comando.
    """
    def run_tts():
        try:
            say(text, voice_name)
        except Exception as e:
            logger.error(f"TTS_ASYNC_ERROR: {e}")
    
    # Ejecutar TTS en hilo separado para no bloquear
    tts_thread = threading.Thread(target=run_tts, daemon=True)
    tts_thread.start()
    
    # Mostrar texto limpio en log
    cleaned_preview = clean_text_for_tts(text)
    logger.info(f"TTS_ASYNC: Iniciado para texto: '{cleaned_preview[:50]}...' - Sistema no bloqueado")

def get_contextual_filler(user_input: str, domain: str = None) -> str:
    """
    Genera un filler contextual inteligente basado en el input del usuario.
    Respuesta inmediata mientras la IA procesa.
    """
    user_lower = user_input.lower()
    
    # Fillers específicos por contexto
    if any(word in user_lower for word in ['cocina', 'receta', 'comida', 'preparar', 'almuerzo', 'comer', 'seco', 'pollo']):
        return "Perfecto"
    elif any(word in user_lower for word in ['planta', 'regar', 'cuidar']):
        return "Claro"
    elif any(word in user_lower for word in ['tiempo', 'clima', 'lluvia']):
        return "Un momento"
    elif any(word in user_lower for word in ['salud', 'dolor', 'medicina']):
        return "Entiendo"
    elif any(word in user_lower for word in ['café', 'bebida', 'té']):
        return "Perfecto"
    elif any(word in user_lower for word in ['hola', 'buenos', 'buenas']):
        return ""  # No filler para saludos
    else:
        return ""  # No usar filler por defecto para evitar confusión

def speak_with_immediate_feedback(text: str, voice_name: str = None, user_input: str = ""):
    """
    Estrategia de TTS optimizada:
    1. Filler contextual inmediato (0.2s)
    2. Respuesta principal asíncrona
    3. Sistema listo inmediatamente
    """
    # 1. Filler contextual inmediato si es apropiado
    filler = get_contextual_filler(user_input)
    if filler:
        say(filler, voice_name)  # Síncrono solo para filler corto
    
    # 2. Respuesta principal asíncrona
    say_async(text, voice_name)
    
    logger.info(f"TTS_OPTIMIZED: Filler='{filler}', Response iniciado async")

# ============================================================================
# STREAMING TTS - NUEVA FUNCIONALIDAD
# ============================================================================

class StreamingTTSManager:
    """
    Gestor de TTS streaming que procesa texto por chunks y reproduce audio fluido
    """
    
    def __init__(self, voice_name: str = DEFAULT_VOICE):
        self.voice_name = voice_name
        self.audio_queue = queue.Queue()
        self.is_playing = False
        self.player_thread = None
        self.stop_playback = threading.Event()
        
        # Configuración de voz
        self.language_code = "-".join(voice_name.split("-")[:2])
        self.voice = texttospeech.VoiceSelectionParams(
            language_code=self.language_code, 
            name=voice_name
        )
        self.audio_config = texttospeech.AudioConfig(
            audio_encoding=texttospeech.AudioEncoding.MP3
        )
        
        logger.info(f"StreamingTTS: Inicializado con voz {voice_name}")
    
    def start_streaming_session(self):
        """Inicia una sesión de streaming TTS"""
        self.stop_playback.clear()
        
        if not self.is_playing:
            self.player_thread = threading.Thread(target=self._audio_player_loop, daemon=True)
            self.player_thread.start()
            self.is_playing = True
            logger.info("StreamingTTS: Sesión de streaming iniciada")
    
    def add_text_chunk(self, text_chunk: str):
        """
        Añade un chunk de texto para convertir a audio y reproducir
        
        Args:
            text_chunk (str): Fragmento de texto a convertir
        """
        if not text_chunk.strip():
            return
            
        # Dividir en oraciones si es necesario
        sentences = self._split_into_sentences(text_chunk)
        
        for sentence in sentences:
            if sentence.strip():
                # Generar audio para la oración
                audio_data = self._generate_audio(sentence)
                if audio_data:
                    # Añadir a la queue
                    self.audio_queue.put({
                        'audio_data': audio_data,
                        'text': sentence,
                        'timestamp': time.time()
                    })
                    logger.debug(f"StreamingTTS: Chunk añadido: '{sentence[:30]}...'")
    
    def finish_streaming_session(self):
        """Termina la sesión de streaming"""
        # Enviar señal de fin
        self.audio_queue.put({'type': 'end_session'})
        logger.info("StreamingTTS: Sesión de streaming finalizada")
    
    def stop_streaming(self):
        """Detiene completamente el streaming"""
        self.stop_playback.set()
        self.is_playing = False
        
        # Limpiar queue
        while not self.audio_queue.empty():
            try:
                self.audio_queue.get_nowait()
            except queue.Empty:
                break
        
        logger.info("StreamingTTS: Streaming detenido")
    
    def _split_into_sentences(self, text: str) -> list:
        """Divide texto en oraciones para TTS fluido"""
        # Patrones para dividir oraciones
        sentence_endings = r'[.!?]+\s+'
        sentences = re.split(sentence_endings, text.strip())
        
        # Limpiar oraciones vacías
        sentences = [s.strip() for s in sentences if s.strip()]
        
        # Si no hay divisiones claras, dividir por comas largas
        if len(sentences) == 1 and len(text) > 80:
            sentences = [s.strip() + ',' for s in text.split(',') if s.strip()]
            # Quitar última coma
            if sentences:
                sentences[-1] = sentences[-1].rstrip(',')
        
        return sentences
    
    def _generate_audio(self, text: str) -> bytes:
        """Genera audio para un fragmento de texto"""
        try:
            # LIMPIAR TEXTO PARA TTS STREAMING
            cleaned_text = clean_text_for_tts(text)
            if cleaned_text != text:
                logger.debug(f"StreamingTTS_CLEANED: '{text}' → '{cleaned_text}'")
            
            synthesis_input = texttospeech.SynthesisInput(text=cleaned_text)
            response = _client.synthesize_speech(
                input=synthesis_input,
                voice=self.voice,
                audio_config=self.audio_config
            )
            return response.audio_content
        except Exception as e:
            logger.error(f"StreamingTTS: Error generando audio para '{text[:20]}...': {e}")
            return None
    
    def _audio_player_loop(self):
        """Loop principal del reproductor de audio"""
        logger.info("StreamingTTS: Player loop iniciado")
        
        while not self.stop_playback.is_set():
            try:
                # Esperar por audio con timeout
                audio_item = self.audio_queue.get(timeout=1.0)
                
                if isinstance(audio_item, dict) and audio_item.get('type') == 'end_session':
                    logger.info("StreamingTTS: Fin de sesión recibido")
                    break
                
                # Reproducir audio
                if 'audio_data' in audio_item:
                    self._play_audio_data(audio_item['audio_data'], audio_item['text'])
                
                self.audio_queue.task_done()
                
            except queue.Empty:
                continue  # Timeout, verificar stop_playback
            except Exception as e:
                logger.error(f"StreamingTTS: Error en player loop: {e}")
        
        self.is_playing = False
        logger.info("StreamingTTS: Player loop terminado")
    
    def _play_audio_data(self, audio_data: bytes, text: str):
        """Reproduce audio data directamente"""
        filename = None
        try:
            # Crear archivo temporal
            filename = os.path.join(TMP_DIR, f"streaming_tts_{uuid.uuid4().hex}.mp3")
            with open(filename, "wb") as f:
                f.write(audio_data)
            
            logger.debug(f"StreamingTTS: Reproduciendo: '{text[:30]}...'")
            
            # Reproducir con mpg123
            result = subprocess.run(
                ["mpg123", "-q", filename], 
                timeout=10,
                capture_output=True,
                text=True
            )
            
            if result.returncode == 0:
                logger.debug(f"StreamingTTS: Audio reproducido exitosamente")
            else:
                logger.warning(f"StreamingTTS: mpg123 terminó con código {result.returncode}")
                
        except subprocess.TimeoutExpired:
            logger.error("StreamingTTS: Timeout en reproducción de audio")
        except Exception as e:
            logger.error(f"StreamingTTS: Error reproduciendo audio: {e}")
        finally:
            # Limpiar archivo temporal
            if filename and os.path.exists(filename):
                try:
                    os.remove(filename)
                except Exception as e:
                    logger.warning(f"StreamingTTS: No se pudo eliminar {filename}: {e}")

# Instancia global del streaming TTS
_streaming_tts = StreamingTTSManager()

def stream_speak_text(text_chunks_generator, voice_name: str = None):
    """
    Función principal para streaming TTS
    
    Args:
        text_chunks_generator: Generador que yield chunks de texto
        voice_name: Nombre de la voz a usar
    """
    global _streaming_tts
    
    # Configurar voz si se especifica
    if voice_name and voice_name != _streaming_tts.voice_name:
        _streaming_tts = StreamingTTSManager(voice_name)
    
    # Iniciar sesión de streaming
    _streaming_tts.start_streaming_session()
    
    processed_any = False
    
    try:
        # Procesar chunks del generador
        for chunk_data in text_chunks_generator:
            processed_any = True
            
            if isinstance(chunk_data, dict):
                # Si es respuesta completa (cache/instantánea)
                if 'response' in chunk_data and not chunk_data.get('chunk_text'):
                    full_response = chunk_data['response']
                    logger.info(f"TTS_STREAM: Procesando respuesta completa: '{full_response[:30]}...'")
                    _streaming_tts.add_text_chunk(full_response)
                    break
                    
                # Si es chunk de streaming
                elif 'chunk_text' in chunk_data:
                    text_chunk = chunk_data['chunk_text']
                    if text_chunk:
                        _streaming_tts.add_text_chunk(text_chunk)
                        logger.debug(f"TTS_STREAM: Procesando chunk: '{text_chunk[:30]}...'")
                    
                    # Si es el chunk final, terminar
                    if chunk_data.get('is_final', False):
                        logger.info("TTS_STREAM: Chunk final recibido")
                        break
            elif isinstance(chunk_data, str):
                # Chunk de texto simple
                if chunk_data:
                    _streaming_tts.add_text_chunk(chunk_data)
    
    except Exception as e:
        logger.error(f"TTS_STREAM: Error procesando chunks: {e}")
    
    finally:
        # Finalizar sesión
        _streaming_tts.finish_streaming_session()
        
        if processed_any:
            logger.info("TTS_STREAM: Streaming completado")
        else:
            logger.warning("TTS_STREAM: No se procesaron chunks")

def stop_streaming():
    """Detiene el streaming TTS actual"""
    global _streaming_tts
    _streaming_tts.stop_streaming()
    logger.info("TTS: Streaming detenido por interrupción externa")

# ELIMINADO: Funcionalidad de interrupción TTS (revertida al comportamiento original)
