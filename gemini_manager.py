# gemini_manager.py (Con Instrucción de Sistema para definir la personalidad de Kata)
import google.generativeai as genai
import os
import logging
from dotenv import load_dotenv

dotenv_loaded_successfully = load_dotenv()

logger = logging.getLogger(__name__)

GOOGLE_API_KEY = os.getenv("GOOGLE_API_KEY")

# --- INSTRUCCIÓN DE SISTEMA PARA KATA ---
KATA_SYSTEM_PROMPT = (
    "Eres Kata, un asistente virtual diseñado específicamente para ayudar y acompañar a adultos mayores. "
    "Tu tono debe ser siempre amigable, paciente, respetuoso y muy claro. "
    "Evita la jerga técnica y las respuestas demasiado largas o complejas. "
    "Ofrece información de manera sencilla y directa. "
    "Tu objetivo principal es ser útil y hacer que el usuario se sienta cómodo. "
    "Habla siempre en español."
    "Cuando te pregunten tu nombre, di que te llamas Kata."
    "No menciones que eres un modelo de lenguaje ni una inteligencia artificial de Google a menos que sea estrictamente necesario para aclarar una limitación."
)

if not dotenv_loaded_successfully:
    logger.warning("python-dotenv: El archivo .env NO fue encontrado o no se pudo cargar.")

if not GOOGLE_API_KEY:
    logger.error("GEMINI_ERROR: GOOGLE_API_KEY no encontrada en el entorno. El servicio Gemini no funcionará.")
else:
    logger.info(f"GEMINI_INFO: GOOGLE_API_KEY encontrada (longitud: {len(GOOGLE_API_KEY)}).")
    try:
        genai.configure(api_key=GOOGLE_API_KEY)
        logger.info("GEMINI_INFO: SDK de Google Generative AI configurado exitosamente.")
    except Exception as e:
        logger.error(f"GEMINI_ERROR: Error configurando la API de Google Generative AI: {e}")
        GOOGLE_API_KEY = None

MODEL_NAME = 'gemini-1.5-flash-latest' # O 'gemini-pro' si prefieres y está disponible

generation_config = {
    "temperature": 0.7, # Un buen balance entre creatividad y coherencia
    "top_p": 0.95,
    "top_k": 40, # Ajustado para permitir más diversidad que top_k=1
    "max_output_tokens": 2048, # Límite de tokens para la respuesta
}

safety_settings = [
    {"category": "HARM_CATEGORY_HARASSMENT", "threshold": "BLOCK_MEDIUM_AND_ABOVE"},
    {"category": "HARM_CATEGORY_HATE_SPEECH", "threshold": "BLOCK_MEDIUM_AND_ABOVE"},
    {"category": "HARM_CATEGORY_SEXUALLY_EXPLICIT", "threshold": "BLOCK_MEDIUM_AND_ABOVE"},
    {"category": "HARM_CATEGORY_DANGEROUS_CONTENT", "threshold": "BLOCK_MEDIUM_AND_ABOVE"},
]

model_instance = None
if GOOGLE_API_KEY:
    try:
        model_instance = genai.GenerativeModel(
            model_name=MODEL_NAME,
            generation_config=generation_config,
            safety_settings=safety_settings,
            system_instruction=KATA_SYSTEM_PROMPT # <--- AQUÍ SE AÑADE LA INSTRUCCIÓN DE SISTEMA
        )
        logger.info(f"GEMINI_INFO: Instancia del modelo Gemini '{MODEL_NAME}' creada exitosamente CON INSTRUCCIÓN DE SISTEMA.")
    except Exception as e:
        logger.error(f"GEMINI_ERROR: Error al crear la instancia del modelo Gemini '{MODEL_NAME}': {e}")
else:
    logger.warning("GEMINI_WARNING: No se intentará crear la instancia del modelo Gemini porque la API Key no está disponible/configurada.")

chat_session = None # Se inicializará cuando sea necesario

def start_new_chat_session():
    global chat_session
    if not model_instance:
        logger.error("GEMINI_ERROR: La instancia del modelo Gemini no está creada/disponible. No se puede iniciar el chat.")
        return False
    try:
        # El historial inicial puede estar vacío ya que la instrucción de sistema se aplica a nivel del modelo.
        chat_session = model_instance.start_chat(history=[])
        logger.info("GEMINI_INFO: Nueva sesión de chat iniciada con Gemini (modelo ya tiene instrucción de sistema).")
        return True
    except Exception as e:
        logger.error(f"GEMINI_ERROR: Error iniciando la sesión de chat con Gemini: {e}")
        chat_session = None
        return False

def ask_gemini_chat(prompt_text: str) -> str | None:
    global chat_session
    if not GOOGLE_API_KEY:
        logger.error("GEMINI_ERROR: API Key no configurada.")
        return "Error: La API Key de Gemini no está configurada."

    if not model_instance:
        logger.error("GEMINI_ERROR: La instancia del modelo Gemini no está disponible.")
        return "Error: El modelo Gemini no está disponible para procesar tu solicitud."

    if chat_session is None:
        logger.warning("GEMINI_WARNING: No hay una sesión de chat activa. Iniciando una nueva...")
        if not start_new_chat_session(): # Intenta iniciar una sesión
             return "Error crítico: No se pudo iniciar una sesión de chat con Gemini."

    try:
        logger.debug(f"Enviando a Gemini (chat): {prompt_text}")
        # Para modelos más nuevos, enviar un mensaje podría requerir un formato específico de "parts"
        # pero para texto simple, esto debería funcionar.
        # response = chat_session.send_message({"role": "user", "parts": [prompt_text]}) # Alternativa más explícita
        response = chat_session.send_message(prompt_text)

        # Extraer el texto de la respuesta.
        # response.text es la forma más directa si la respuesta es simple.
        text_response = response.text

        logger.debug(f"Respuesta de Gemini (chat): {text_response}")
        return text_response
    except Exception as e:
        logger.error(f"GEMINI_ERROR: Error durante la comunicación con Gemini (chat): {e}", exc_info=True)
        # Podrías intentar reiniciar la sesión si es un error recuperable
        # o simplemente devolver un mensaje de error.
        return f"Lo siento, tuve un problema al contactar mi cerebro para responder a eso: Error Interno."


# (Función ask_gemini_simple omitida por consistencia con el uso de chat_session)
