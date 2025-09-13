import logging
from gpiozero import Button
from threading import Timer
import time

logger = logging.getLogger(__name__)

# --- CONFIGURACIÓN ---
PIN_BOTON = 17
HOLD_TIME_SECONDS = 5.0  # Aumentado para cuidadores (evitar activación accidental)
SINGLE_PRESS_DELAY = 0.3  # Reducido para respuesta más rápida

# Variables globales para el estado de confirmación
_button = None
_single_press_timer = None
_medication_confirmation_mode = False
_medication_callback = None

# Variables para funcionalidad de mensajes
_message_reader = None
_message_reading_enabled = True

# --- NUEVAS FUNCIONES PARA CONFIRMACIÓN DE MEDICAMENTOS ---
def set_medication_confirmation_mode(medication_callback):
    """
    Activa el modo de confirmación de medicamento.
    En este modo, el botón SOLO responde a confirmación de medicamento.
    """
    global _medication_confirmation_mode, _medication_callback
    _medication_confirmation_mode = True
    _medication_callback = medication_callback
    logger.info("BUTTON_MANAGER: Modo confirmación de medicamento ACTIVADO")

def exit_medication_confirmation_mode():
    """
    Desactiva el modo de confirmación de medicamento.
    El botón vuelve a sus funciones normales para cuidadores.
    """
    global _medication_confirmation_mode, _medication_callback
    _medication_confirmation_mode = False
    _medication_callback = None
    logger.info("BUTTON_MANAGER: Modo confirmación de medicamento DESACTIVADO")

def is_in_medication_confirmation_mode():
    """
    Retorna True si está en modo confirmación de medicamento.
    """
    return _medication_confirmation_mode

# --- NUEVAS FUNCIONES PARA MENSAJES ---
def set_message_reader(message_reader):
    """
    Configura el lector de mensajes para usar con el botón.
    
    Args:
        message_reader: Instancia del MessageReader
    """
    global _message_reader
    _message_reader = message_reader
    logger.info("BUTTON_MANAGER: MessageReader configurado")

def enable_message_reading():
    """Habilita la lectura de mensajes por botón."""
    global _message_reading_enabled
    _message_reading_enabled = True
    logger.info("BUTTON_MANAGER: Lectura de mensajes por botón habilitada")

def disable_message_reading():
    """Deshabilita la lectura de mensajes por botón."""
    global _message_reading_enabled
    _message_reading_enabled = False
    logger.info("BUTTON_MANAGER: Lectura de mensajes por botón deshabilitada")

def start_button_listener(press_callback, hold_callback):
    """
    Inicia la escucha del botón y asigna las funciones a los eventos correctos.
    """
    global _button
    if _button is not None:
        logger.warning("BUTTON_MANAGER: Se intentó iniciar un listener cuando ya existía uno.")
        return

    try:
        _button = Button(PIN_BOTON, pull_up=True, hold_time=HOLD_TIME_SECONDS)
        
        # Asignamos las funciones que manejarán la lógica
        _button.when_pressed = lambda: _handle_press(press_callback)
        _button.when_held = hold_callback
        
        logger.info(f"BUTTON_MANAGER: Escuchando en GPIO {PIN_BOTON}.")
        
        # Mantenemos el hilo principal vivo
        # En la app real, el hilo de la UI principal hace este trabajo.
        # Aquí usamos un bucle infinito para las pruebas.
        while True:
            time.sleep(1)

    except Exception as e:
        logger.error(f"BUTTON_MANAGER: Error al iniciar el listener del botón: {e}")
    finally:
        logger.info("BUTTON_MANAGER: El listener del botón ha finalizado.")

def _handle_press(press_callback):
    """
    Gestiona cada pulsación y cancela el temporizador de pulsación corta.
    """
    global _single_press_timer, _medication_confirmation_mode
    
    # Si hay un temporizador de pulsación corta esperando, lo cancelamos
    if _single_press_timer is not None:
        _single_press_timer.cancel()
        _single_press_timer = None
        
    # Si estamos en modo confirmación, simplificar: solo pulsación simple
    if _medication_confirmation_mode:
        logger.info("BUTTON_MANAGER: Pulsación en modo confirmación de medicamento")
        _execute_single_press(press_callback)
        return
    
    # Lógica normal: programar ejecución de pulsación simple
    _single_press_timer = Timer(SINGLE_PRESS_DELAY, lambda: _execute_single_press(press_callback))
    _single_press_timer.start()

def _execute_single_press(press_callback):
    """
    Esta función se ejecuta solo si el temporizador no fue cancelado.
    Significa que fue una pulsación corta y única.
    """
    global _medication_confirmation_mode, _medication_callback
    
    # PRIORIDAD 1: Si estamos en modo confirmación de medicamento
    if _medication_confirmation_mode and _medication_callback:
        logger.info("BUTTON_MANAGER: Confirmación de medicamento recibida.")
        _medication_callback()
        # NO salimos del modo aquí - lo hará improved_app.py
    else:
        # PRIORIDAD 2: Lectura de mensajes (funcionalidad nueva)
        if _message_reading_enabled and _message_reader:
            if _message_reader.has_unread_messages():
                logger.info("BUTTON_MANAGER: Iniciando lectura de mensajes - leyendo 3 más antiguos")
                # Usar método síncrono para mejor control y logging
                _message_reader.read_messages_sync(max_messages=3)
            else:
                logger.info("BUTTON_MANAGER: No hay mensajes para leer")
        else:
            # PRIORIDAD 3: Funciones normales para cuidadores (si no hay mensajes)
            logger.info("BUTTON_MANAGER: Pulsación corta normal (sin medicamento pendiente).")
            # Para adultos mayores: no hacer nada visible si no hay mensajes
            # Para cuidadores: pueden usar pulsación larga
            # press_callback()  # Comentado para evitar confusión


# --- Bloque de prueba ---
if __name__ == '__main__':
    logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(message)s')
    
    def on_press():
        print("-> ACCIÓN: Pulsación Normal (Sin medicamento pendiente)")
    
    def on_hold():
        print("-> ACCIÓN: Pulsación Larga (Reiniciar App - Solo Cuidadores)")

        
    def on_medication_confirmed():
        print("-> ACCIÓN: ¡Medicamento Confirmado!")
        exit_medication_confirmation_mode()

    print("--- Probando el Button Manager de Confirmación ---")
    print(f"- Pulsación simple: Sin acción visible (adultos mayores)")
    print(f"- Mantén presionado por {HOLD_TIME_SECONDS}s para reiniciar (cuidadores)")
    print("- Presiona 'm' para simular medicamento pendiente")
    print("Presiona Ctrl+C para salir.")
    
    try:
        start_button_listener(on_press, on_hold)
        
        # Simulación interactiva
        while True:
            user_input = input("\nEscribe 'm' para simular medicamento: ")
            if user_input.lower() == 'm':
                print("🔵 MEDICAMENTO PENDIENTE - Presiona el botón para confirmar")
                set_medication_confirmation_mode(on_medication_confirmed)
            elif user_input.lower() == 'q':
                break
                
    except KeyboardInterrupt:
        print("\nPrueba finalizada.")
