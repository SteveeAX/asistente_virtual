# system_actions.py
import os
import subprocess
import logging
import sys

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(message)s')

def restart_app():
    """
    Reinicia el script principal de la aplicación.
    Busca el proceso de 'improved_app.py' y lo termina,
    el servicio systemd (si está configurado) debería reiniciarlo.
    """
    logging.info("Intentando reiniciar la aplicación Kata...")
    try:
        # Este comando busca el ID del proceso que ejecuta 'improved_app.py' y lo mata.
        # Es una forma un poco brusca, pero efectiva.
        # pkill es más directo que una combinación de ps, grep y awk.
        subprocess.run(["pkill", "-f", "improved_app.py"], check=True)
        logging.info("Señal de reinicio enviada a improved_app.py.")
    except subprocess.CalledProcessError:
        logging.warning("No se encontró el proceso de improved_app.py para reiniciar.")
    except Exception as e:
        logging.error(f"Error al intentar reiniciar la aplicación: {e}")

def shutdown_pi():
    """
    Apaga la Raspberry Pi de forma segura.
    """
    logging.info("INICIANDO APAGADO DEL SISTEMA EN 5 SEGUNDOS...")
    try:
        # Usamos 'shutdown' con el argumento '-h now' para apagar ahora.
        subprocess.run(["sudo", "shutdown", "-h", "now"], check=True)
    except Exception as e:
        logging.error(f"Error al intentar apagar la Raspberry Pi: {e}")

if __name__ == '__main__':
    # Esto permite llamar al script desde la línea de comandos con argumentos
    if len(sys.argv) > 1:
        action = sys.argv[1]
        if action == 'restart':
            restart_app()
        elif action == 'shutdown':
            shutdown_pi()
        else:
            print(f"Acción desconocida: {action}")
    else:
        print("Uso: python3 system_actions.py [restart|shutdown]")
