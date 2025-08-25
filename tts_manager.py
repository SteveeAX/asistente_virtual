# tts_manager.py (Corregido y listo para personalización)
import os
import uuid
import subprocess
import logging
from google.cloud import texttospeech

logger = logging.getLogger(__name__)
_client = texttospeech.TextToSpeechClient()
TMP_DIR = "/tmp"
DEFAULT_VOICE = "es-US-Neural2-A"

def say(text: str, voice_name: str = None):
    """Genera y reproduce audio usando una voz específica."""
    selected_voice = voice_name if voice_name else DEFAULT_VOICE
    language_code = "-".join(selected_voice.split("-")[:2])
    
    # LOG DE RESPUESTA DEL ASISTENTE
    logger.info(f"ASISTENTE_RESPUESTA: {text}")
    print(f"🔊 RESPUESTA: {text}")  # También mostrar en consola
    
    logger.info(f"TTS: Generando audio con la voz: {selected_voice}")
    try:
        synthesis_input = texttospeech.SynthesisInput(text=text)
        voice = texttospeech.VoiceSelectionParams(language_code=language_code, name=selected_voice)
        audio_config = texttospeech.AudioConfig(audio_encoding=texttospeech.AudioEncoding.MP3)
        response = _client.synthesize_speech(input=synthesis_input, voice=voice, audio_config=audio_config)
        filename = os.path.join(TMP_DIR, f"tts_{uuid.uuid4().hex}.mp3")
        with open(filename, "wb") as out:
            out.write(response.audio_content)
        subprocess.run(["mpg123", "-q", filename], check=True)
    except Exception as e:
        logger.error(f"TTS_ERROR: No se pudo generar o reproducir el audio. Error: {e}")
    finally:
        if 'filename' in locals() and os.path.exists(filename):
            os.remove(filename)
