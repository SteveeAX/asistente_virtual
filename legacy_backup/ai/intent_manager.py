import logging
import re
from typing import Tuple, Optional

logger = logging.getLogger(__name__)

# El diccionario de intenciones ahora vive aquí
INTENTS = {
    "GET_DATE": ["qué día", "cual dia", "cuál es la fecha", "que fecha"],
    "GET_TIME": ["qué hora es", "dime la hora", "dígame la hora", "cuál es la hora", "qué horas son", "que hora son"],
    "PLUG_ON": ["enciende el enchufe", "prende el enchufe"],
    "PLUG_OFF": ["apaga el enchufe"],
    "EMERGENCY_ALERT": ["ayuda", "emergencia", "pide ayuda"],
    "CONTACT_PERSON": ["llama a", "contacta a", "avísale a", "avisa a"],
    "CREATE_REMINDER": ["recuérdame", "recordatorio", "recuerda que", "no olvides"],
    "CREATE_DAILY_REMINDER": ["recuérdame todos los días", "recordatorio diario", "todos los días recuérdame"],
    "LIST_REMINDERS": ["qué recordatorios", "cuáles son mis recordatorios", "mis recordatorios", "lista recordatorios"],
    "DELETE_REMINDER": ["elimina", "borra", "cancela recordatorio", "quita recordatorio", "elimina recordatorio", "borra recordatorio", "elimina el recordatorio"],
    "READ_MESSAGES": [
        "lee el mensaje", "lee los mensajes", "leer mensaje", "leer mensajes", 
        "lee mensaje", "lee mensajes", "mostrar mensaje", "mostrar mensajes",
        "muestra mensaje", "muestra mensajes", "revisar mensajes", "revisar mensaje",
        "qué mensajes", "que mensajes", "cuáles mensajes", "cuales mensajes",
        "qué mensaje", "que mensaje", "tienes mensajes", "tengo mensajes",
        "dime los mensajes", "dime que mensajes", "dime qué mensajes",
        "enséñame los mensajes", "enseñame los mensajes", "ver mensajes", "ver mensaje"
    ],
    "SEND_MESSAGE": [
        "dile a", "avisale a", "avísale a", "enviale un mensaje a", "envía un mensaje a", "envia un mensaje a",
        "digale a", "dígale a", "avisa a", "preguntale a", "pregúntale a",
        "mandale un mensaje a", "mándale un mensaje a", "manda un mensaje a",
        "enviale a", "envíale a", "manda mensaje a", "envia mensaje a", "envía mensaje a"
    ],
    "SHUTDOWN_DEVICE": ["apágate", "apagate", "apaga te", "apaga el dispositivo", "apagar sistema", "apagar el sistema"],
}

def parse_intent(text: str):
    """
    Compara el texto con las frases clave y devuelve la intención correspondiente.
    Para SEND_MESSAGE, también extrae contacto y mensaje.
    """
    if not text:
        return None
    
    # Convertir a minúsculas para comparación case-insensitive
    text_lower = text.lower()
        
    for intent, phrases in INTENTS.items():
        for phrase in phrases:
            if phrase.lower() in text_lower:
                logger.info(f"Intent detected: {intent}")
                return intent
    return None

def parse_send_message_intent(text: str) -> Optional[Tuple[str, str, str]]:
    """
    Analiza texto para comandos de envío de mensaje y extrae componentes.
    
    Args:
        text (str): Texto del usuario
        
    Returns:
        Tuple[comando, contacto, mensaje] o None si no es comando de envío
        
    Ejemplos:
        "dile a Marina que llegué bien" → ("dile a", "Marina", "que llegué bien")
        "avisale a la Maria que voy" → ("avisale a", "la Maria", "que voy")
    """
    if not text:
        return None
    
    text_clean = text.strip().lower()
    
    # Patrones para diferentes comandos de envío
    # Usar patrones más específicos que buscan "que" como separador
    send_patterns = [
        r"(dile a|avisale a|avísale a|enviale un mensaje a|envía un mensaje a|envia un mensaje a)\s+(.+?)\s+(que\s+.+)",
        r"(digale a|dígale a|avisa a)\s+(.+?)\s+(que\s+.+)",
        r"(preguntale a|pregúntale a)\s+(.+?)\s+(si\s+.+|que\s+.+|cómo\s+.+|cuándo\s+.+|dónde\s+.+|por qué\s+.+)",
        r"(mandale un mensaje a|mándale un mensaje a|manda un mensaje a)\s+(.+?)\s+(que\s+.+)",
        r"(enviale a|envíale a|manda mensaje a|envia mensaje a|envía mensaje a)\s+(.+?)\s+(que\s+.+)"
    ]
    
    for pattern in send_patterns:
        match = re.search(pattern, text_clean)
        if match:
            command = match.group(1).strip()
            contact_raw = match.group(2).strip()
            message_body = match.group(3).strip()
            
            logger.info(f"SEND_MESSAGE parsed: comando='{command}', contacto='{contact_raw}', mensaje='{message_body}'")
            return (command, contact_raw, message_body)
    
    return None
