import logging
import re
from typing import Tuple, Optional

logger = logging.getLogger(__name__)

# El diccionario de intenciones ahora vive aquí
INTENTS = {
    "GET_DATE": ["qué día", "cual dia", "cuál es la fecha", "que fecha"],
    "GET_TIME": ["qué hora es", "que hora es", "dime la hora", "dame la hora", "dígame la hora", "cuál es la hora", "cual es la hora", "qué horas son", "que hora son", "que horas son", "la hora", "me puede dar la hora", "me puedes dar la hora", "podrías darme la hora"],
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
        # Comandos directos tradicionales
        "dile a", "avisale a", "avísale a", "enviale un mensaje a", "envía un mensaje a", "envia un mensaje a",
        "digale a", "dígale a", "avisa a", "preguntale a", "pregúntale a", "pregunta a",
        "mandale un mensaje a", "mándale un mensaje a", "manda un mensaje a",
        "enviale a", "envíale a", "manda mensaje a", "envia mensaje a", "envía mensaje a",
        
        # Patrones conversacionales corteses - FASE 1
        "quiero saber", "me gustaría saber", "quisiera saber", "me interesa saber",
        "haz el favor de preguntar", "haz el favor de preguntarle", "podrías preguntar", "podrías preguntarle",
        "te pido que preguntes", "te pido que le preguntes", "disculpa podrías preguntar",
        "por favor pregunta", "por favor pregúntale", "será que puedes preguntar",
        "no sé si puedes preguntar", "a ver si puedes preguntar", "me haces el favor de preguntar",
        
        # Patrones indirectos de consulta
        "quiero que sepas", "me gustaría que supieras", "necesito que sepas",
        "será que", "no sé si", "me pregunto si", "quisiera que le dijeras",
        "me gustaría que le dijeras", "haz el favor de decirle", "podrías decirle"
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
            # Para consultas muy cortas como "la hora", requerir coincidencia exacta
            if phrase.lower() == "la hora" and text_lower.strip() == "la hora":
                logger.info(f"Intent detected: {intent} (exact match)")
                return intent
            elif phrase.lower() != "la hora" and phrase.lower() in text_lower:
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
        # Patrones directos tradicionales
        r"(dile a|avisale a|avísale a|enviale un mensaje a|envía un mensaje a|envia un mensaje a)\s+(.+?)\s+(que\s+.+)",
        r"(digale a|dígale a|avisa a)\s+(.+?)\s+(que\s+.+)",
        r"(preguntale a|pregúntale a|pregunta a)\s+(.+?)\s+(si\s+.+|que\s+.+|cómo\s+.+|cuándo\s+.+|dónde\s+.+|por qué\s+.+|a qué\s+.+|cuando\s+.+|donde\s+.+)",
        r"(mandale un mensaje a|mándale un mensaje a|manda un mensaje a)\s+(.+?)\s+(que\s+.+)",
        r"(enviale a|envíale a|manda mensaje a|envia mensaje a|envía mensaje a)\s+(.+?)\s+(que\s+.+)",
        
        # Patrones conversacionales FASE 1 - Preguntas indirectas sobre contactos
        # Captura: "quiero saber de Monica a qué hora viene" → ("quiero saber", "Monica", "a qué hora viene")
        r"(quiero saber|me gustaría saber|quisiera saber|me interesa saber)\s+(?:de\s+|sobre\s+)?(.+?)\s+(a qué\s+.+|qué\s+.+|cuándo\s+.+|dónde\s+.+|cómo\s+.+|si\s+.+|cuando\s+.+|donde\s+.+)",
        
        # Captura: "será que Monica ya llegó" → ("será que", "Monica", "ya llegó")
        r"(será que|no sé si|me pregunto si)\s+(.+?)\s+(ya\s+.+|está\s+.+|viene\s+.+|va\s+.+|llegó\s+.+|puede\s+.+|tiene\s+.+)",
        
        # Captura patrones corteses: "haz el favor de preguntarle a Monica si ya llegó"
        r"(haz el favor de preguntarle? a|podrías preguntarle? a|te pido que le preguntes a)\s+(.+?)\s+(si\s+.+|que\s+.+|cómo\s+.+|cuándo\s+.+|a qué\s+.+|cuando\s+.+)",
        
        # Captura: "por favor pregúntale a Monica a qué hora viene"
        r"(por favor pregúntale? a|disculpa podrías preguntarle? a|me haces el favor de preguntarle? a)\s+(.+?)\s+(a qué\s+.+|qué\s+.+|si\s+.+|cuándo\s+.+|cómo\s+.+|cuando\s+.+)"
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

def parse_conversational_message_intent(text: str) -> Optional[Tuple[str, str, str]]:
    """
    Analiza texto conversacional y lo convierte a formato de comando directo.
    Transforma patrones como "quiero saber de Monica a qué hora viene" 
    en comandos estándar para el sistema de mensajes.
    
    Args:
        text (str): Texto conversacional del usuario
        
    Returns:
        Tuple[comando, contacto, mensaje] o None si no es patrón conversacional
        
    Ejemplos:
        "quiero saber de Monica a qué hora viene" → ("pregúntale a", "Monica", "a qué hora vienes")
        "será que Ana ya llegó" → ("pregúntale a", "Ana", "si ya llegaste")
    """
    if not text:
        return None
        
    text_clean = text.strip().lower()
    
    # Patrones conversacionales específicos con transformaciones
    conversational_patterns = [
        # "quiero saber de Monica a qué hora viene" → ("pregúntale a", "Monica", "a qué hora vienes")
        {
            "pattern": r"(quiero saber|me gustaría saber|quisiera saber|me interesa saber)\s+(?:de\s+|sobre\s+)?(.+?)\s+(a qué\s+.+|qué\s+.+|cuándo\s+.+|dónde\s+.+|cómo\s+.+|cuando\s+.+|donde\s+.+)",
            "command": "pregúntale a",
            "transform_message": lambda msg: msg.replace("viene", "vienes").replace("va", "vas").replace("está", "estás")
        },
        
        # "será que Monica ya llegó" → ("pregúntale a", "Monica", "si ya llegaste")  
        {
            "pattern": r"(será que|no sé si|me pregunto si)\s+(.+?)\s+(ya\s+.+|está\s+.+|viene\s+.+|va\s+.+|llegó\s+.+|puede\s+.+|tiene\s+.+)",
            "command": "pregúntale a",
            "transform_message": lambda msg: f"si {msg}".replace("llegó", "llegaste").replace("está", "estás").replace("viene", "vienes").replace("va", "vas").replace("puede", "puedes").replace("tiene", "tienes")
        },
        
        # Patrones corteses ya tienen estructura correcta, solo necesitan limpieza
        {
            "pattern": r"(haz el favor de preguntarle? a|podrías preguntarle? a|te pido que le preguntes a)\s+(.+?)\s+(si\s+.+|que\s+.+|cómo\s+.+|cuándo\s+.+|a qué\s+.+|cuando\s+.+)",
            "command": "pregúntale a",
            "transform_message": lambda msg: msg
        },
        
        {
            "pattern": r"(por favor pregúntale? a|disculpa podrías preguntarle? a|me haces el favor de preguntarle? a)\s+(.+?)\s+(a qué\s+.+|qué\s+.+|si\s+.+|cuándo\s+.+|cómo\s+.+|cuando\s+.+)",
            "command": "pregúntale a", 
            "transform_message": lambda msg: msg
        }
    ]
    
    for conv_pattern in conversational_patterns:
        match = re.search(conv_pattern["pattern"], text_clean)
        if match:
            command = conv_pattern["command"]
            contact_raw = match.group(2).strip()
            message_body = match.group(3).strip()
            
            # Aplicar transformación al mensaje
            transformed_message = conv_pattern["transform_message"](message_body)
            
            logger.info(f"CONVERSATIONAL_MESSAGE parsed: '{text}' → comando='{command}', contacto='{contact_raw}', mensaje='{transformed_message}'")
            return (command, contact_raw, transformed_message)
    
    return None
