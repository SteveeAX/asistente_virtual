#!/bin/bash

# Exporta la variable de pantalla para aplicaciones GUI
export DISPLAY=:0

# Espera 10 segundos para dar tiempo a que el escritorio cargue
sleep 10

# Navega al directorio del proyecto
cd /home/steveen/asistente_kata

# Activa el entorno virtual
source /home/steveen/gcp-tts-venv/bin/activate

# Exporta la variable de credenciales de Google
export GOOGLE_APPLICATION_CREDENTIALS="/home/steveen/asistente_kata/gleaming-terra-454706-r0-0b19bb6937f8.json"

# Ejecuta la aplicación y guarda toda la salida (normal y de error) en un archivo de log
python3 improved_app.py >> /home/steveen/kata_autostart.log 2>&1
