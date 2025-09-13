# system_actions.py
import os
import subprocess
import logging
import sys

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(message)s')

def restart_app():
    """
    Reinicia el script principal de la aplicación.
    Si no hay servicio systemd, usa exec para reiniciar directamente.
    """
    logging.info("Intentando reiniciar la aplicación Kata...")
    try:
        # Verificar si hay servicio systemd configurado
        result = subprocess.run(["systemctl", "--user", "is-active", "asistente-kata.service"], 
                              capture_output=True, text=True)
        
        if result.returncode == 0:  # Servicio existe y está activo
            logging.info("Reiniciando vía systemd...")
            subprocess.run(["systemctl", "--user", "restart", "asistente-kata.service"], check=True)
        else:
            # No hay servicio systemd, hacer reinicio directo
            logging.info("No hay servicio systemd, reiniciando directamente...")
            
            # Buscar el script principal actual
            import __main__
            script_path = os.path.abspath(__main__.__file__ if hasattr(__main__, '__file__') else 'improved_app.py')
            
            # Si no podemos determinar el script, usar improved_app.py por defecto
            if not script_path.endswith('improved_app.py'):
                script_path = os.path.join(os.path.dirname(__file__), 'improved_app.py')
            
            logging.info(f"Reiniciando script: {script_path}")
            
            # Ejecutar el reinicio en segundo plano para evitar bloquear
            subprocess.Popen(["python3", script_path], 
                           cwd=os.path.dirname(script_path),
                           stdout=subprocess.DEVNULL, 
                           stderr=subprocess.DEVNULL)
            
            # Dar tiempo para que inicie el nuevo proceso
            import time
            time.sleep(1)
            
            # Terminar el proceso actual después de iniciar el nuevo
            os._exit(0)
            
    except Exception as e:
        logging.error(f"Error al intentar reiniciar la aplicación: {e}")
        # Como último recurso, intentar pkill
        try:
            subprocess.run(["pkill", "-f", "improved_app.py"], check=False)
        except:
            pass

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
