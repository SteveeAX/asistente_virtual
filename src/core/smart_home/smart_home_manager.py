# smart_home_manager.py
import paho.mqtt.client as mqtt
import json
import logging
import time

logger = logging.getLogger(__name__)

# --- Configuración del Broker MQTT ---
MQTT_BROKER_ADDRESS = "localhost" # El broker está en la misma Raspberry Pi
MQTT_PORT = 1883
BASE_TOPIC = "zigbee2mqtt"

def set_device_state(device_friendly_name: str, state: str):
    """
    Publica un mensaje MQTT para cambiar el estado de un dispositivo.

    Args:
        device_friendly_name (str): El nombre amigable del dispositivo en Zigbee2MQTT (ej. 'enchufe').
        state (str): El estado deseado. Usualmente "ON", "OFF", o "TOGGLE".
    """
    try:
        # Crear un cliente MQTT
        client = mqtt.Client(mqtt.CallbackAPIVersion.VERSION2, client_id=f"kata_controller_{time.time()}")
        logger.info(f"SMART_HOME: Conectando al broker MQTT en {MQTT_BROKER_ADDRESS}...")

        # Conectar al broker
        client.connect(MQTT_BROKER_ADDRESS, MQTT_PORT, 60)

        # Construir el topic y el payload
        topic = f"{BASE_TOPIC}/{device_friendly_name}/set"
        payload = json.dumps({"state": state.upper()}) # Convertir a mayúsculas por si acaso

        logger.info(f"SMART_HOME: Publicando en topic '{topic}' con payload: {payload}")

        # Publicar el mensaje
        client.publish(topic, payload)

        # Desconectar del broker
        client.disconnect()
        logger.info("SMART_HOME: Mensaje publicado y desconectado del broker.")
        return True
    except Exception as e:
        logger.error(f"SMART_HOME: Error al enviar comando MQTT: {e}", exc_info=True)
        return False

# --- Bloque de prueba para smart_home_manager.py ---
# Esto solo se ejecuta si corres 'python3 smart_home_manager.py' directamente.
if __name__ == '__main__':
    # Configurar un logger básico para poder ver los mensajes de este script al probarlo
    logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')

    # El nombre amigable que le diste a tu enchufe en la interfaz web de Zigbee2MQTT
    MI_ENCHUFE = "enchufe" 

    print(f"--- Prueba del Módulo Smart Home Manager ---")
    print(f"Se intentará controlar el dispositivo con nombre amigable: '{MI_ENCHUFE}'")

    try:
        print("\nPrueba 1: Encendiendo el enchufe...")
        set_device_state(MI_ENCHUFE, "ON")
        # Deberías escuchar o ver que tu enchufe se enciende

        time.sleep(5) # Esperar 5 segundos

        print("\nPrueba 2: Apagando el enchufe...")
        set_device_state(MI_ENCHUFE, "OFF")
        # Deberías escuchar o ver que tu enchufe se apaga

        time.sleep(2)

        print("\nPrueba 3: Alternando el estado del enchufe (TOGGLE)...")
        set_device_state(MI_ENCHUFE, "TOGGLE") # Si estaba OFF, se encenderá
        time.sleep(2)
        set_device_state(MI_ENCHUFE, "TOGGLE") # Si estaba ON, se apagará

        print("\n--- Prueba finalizada exitosamente ---")

    except Exception as e:
        print(f"\nOcurrió un error durante la prueba: {e}")
