import logging

logger = logging.getLogger(__name__)

# El diccionario de intenciones ahora vive aquí
INTENTS = {
    "GET_DATE": ["qué día", "cual dia", "cuál es la fecha", "que fecha"],
    "GET_TIME": ["qué hora es", "dime la hora", "dígame la hora", "cuál es la hora"],
    "PLUG_ON": ["enciende el enchufe", "prende el enchufe"],
    "PLUG_OFF": ["apaga el enchufe"],
    "EMERGENCY_ALERT": ["ayuda", "emergencia", "pide ayuda"],
    "CONTACT_PERSON": ["llama a", "contacta a", "avísale a", "avisa a"],
    "CREATE_REMINDER": ["recuérdame", "recordatorio", "recuerda que", "no olvides"],
    "CREATE_DAILY_REMINDER": ["recuérdame todos los días", "recordatorio diario", "todos los días recuérdame"],
    "LIST_REMINDERS": ["qué recordatorios", "cuáles son mis recordatorios", "mis recordatorios", "lista recordatorios"],
    "DELETE_REMINDER": ["elimina", "borra", "cancela recordatorio", "quita recordatorio", "elimina recordatorio", "borra recordatorio", "elimina el recordatorio"],
}

def parse_intent(text: str):
    """
    Compara el texto con las frases clave y devuelve la intención correspondiente.
    """
    if not text:
        return None
        
    for intent, phrases in INTENTS.items():
        for phrase in phrases:
            if phrase in text:
                logger.info(f"Intent detected: {intent}")
                return intent
    return None
