import logging
from gpiozero import Button
from threading import Timer
import time

logger = logging.getLogger(__name__)

# --- CONFIGURACIÓN ---
PIN_BOTON = 17
HOLD_TIME_SECONDS = 2.5
TRIPLE_PRESS_WINDOW = 2 # Ventana de tiempo para la triple pulsación
SINGLE_PRESS_DELAY = 0.7 # Tiempo de espera para confirmar una pulsación corta

# Variables globales
_button = None
_press_timestamps = []
_single_press_timer = None

def start_button_listener(press_callback, hold_callback, triple_press_callback):
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
        _button.when_pressed = lambda: _handle_press(press_callback, triple_press_callback)
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

def _handle_press(press_callback, triple_press_callback):
    """
    Gestiona cada pulsación, cancela el temporizador de pulsación corta,
    y comprueba si se ha completado una triple pulsación.
    """
    global _press_timestamps, _single_press_timer
    
    # Si hay un temporizador de pulsación corta esperando, lo cancelamos
    if _single_press_timer is not None:
        _single_press_timer.cancel()
        _single_press_timer = None
        
    current_time = time.time()
    
    # Limpiamos timestamps viejos
    _press_timestamps = [t for t in _press_timestamps if current_time - t < TRIPLE_PRESS_WINDOW]
    _press_timestamps.append(current_time)
    
    if len(_press_timestamps) >= 3:
        logger.info("BUTTON_MANAGER: ¡Triple pulsación detectada!")
        triple_press_callback()
        _press_timestamps.clear() # Reseteamos el contador
    else:
        # Si no es una triple pulsación, programamos que se ejecute la acción de pulsación corta
        # después de un breve retraso. Si llega otra pulsación, este temporizador se cancelará.
        _single_press_timer = Timer(SINGLE_PRESS_DELAY, lambda: _execute_single_press(press_callback))
        _single_press_timer.start()

def _execute_single_press(press_callback):
    """
    Esta función se ejecuta solo si el temporizador no fue cancelado.
    Significa que fue una pulsación corta y única.
    """
    global _press_timestamps
    logger.info("BUTTON_MANAGER: Pulsación corta confirmada.")
    press_callback()
    # Limpiamos los timestamps para la próxima secuencia
    _press_timestamps.clear()


# --- Bloque de prueba ---
if __name__ == '__main__':
    logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(message)s')
    
    def on_press():
        print("-> ACCIÓN: Pulsación Corta (Emergencia)")
    
    def on_hold():
        print("-> ACCIÓN: Pulsación Larga (Reiniciar App)")

    def on_triple_press():
        print("-> ACCIÓN: Triple Pulsación (Apagar Pi)")

    print("--- Probando el Button Manager Avanzado ---")
    print(f"- Pulsa una vez para la alerta (se confirmará después de {SINGLE_PRESS_DELAY}s).")
    print(f"- Mantén presionado por {HOLD_TIME_SECONDS}s para reiniciar.")
    print(f"- Pulsa tres veces rápido (en menos de {TRIPLE_PRESS_WINDOW}s) para apagar.")
    print("Presiona Ctrl+C para salir.")
    
    try:
        start_button_listener(on_press, on_hold, on_triple_press)
    except KeyboardInterrupt:
        print("\nPrueba finalizada.")
