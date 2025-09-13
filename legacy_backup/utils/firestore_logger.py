# firestore_logger.py
import logging
from google.cloud import firestore
from datetime import datetime, timezone

logger = logging.getLogger(__name__)

try:
    # Intenta inicializar el cliente.
    # Automáticamente usará la variable de entorno GOOGLE_APPLICATION_CREDENTIALS.
    # Usa database específica para el asistente
    db = firestore.Client(database='asistente-kata-db')
    logger.info("LOGGER: Conexión con Cloud Firestore establecida (database: asistente-kata-db).")
    firestore_available = True
except Exception as e:
    logger.error(f"LOGGER: No se pudo conectar a Firestore. El registro en la nube estará desactivado. Error: {e}")
    firestore_available = False

def log_interaction(event_type: str, details: dict = None):
    """
    Registra una interacción en la colección 'interaction_logs' de Firestore.
    """
    if not firestore_available:
        return

    try:
        log_collection = db.collection('interaction_logs')

        log_data = {
            'timestamp': datetime.now(timezone.utc),
            'event_type': event_type,
            'details': details if details is not None else {}
        }

        # Añade un nuevo documento con un ID generado automáticamente
        log_collection.add(log_data)
        logger.debug(f"LOGGER: Evento '{event_type}' registrado en Firestore.")

    except Exception as e:
        logger.error(f"LOGGER: Error al registrar evento en Firestore: {e}")
