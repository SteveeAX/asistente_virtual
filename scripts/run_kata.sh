#!/bin/bash

# Script de autoarranque optimizado para Kata Assistant
# Reproduce las condiciones exactas del arranque manual

# Esperar a que el desktop esté completamente cargado
sleep 10

# Configurar directorio de trabajo
cd /home/steveen/asistente_kata

# Crear directorio de logs si no existe
mkdir -p logs

# Registrar inicio
echo "$(date): Script run_kata.sh iniciado (Desktop Autostart)" >> logs/autostart.log

# Las variables de entorno ya están configuradas por el desktop environment
# Solo necesitamos asegurar PYTHONPATH
export PYTHONPATH="/home/steveen/asistente_kata:$PYTHONPATH"

# Activar entorno virtual
if [ -d "/home/steveen/gcp-tts-venv" ]; then
    source /home/steveen/gcp-tts-venv/bin/activate
    echo "$(date): Entorno virtual activado" >> logs/autostart.log
else
    echo "$(date): ERROR - Entorno virtual no encontrado" >> logs/autostart.log
    exit 1
fi

# Cargar variables de entorno del archivo .env si existe
if [ -f ".env" ]; then
    source .env
    echo "$(date): Variables de entorno cargadas desde .env" >> logs/autostart.log
fi

# Registrar inicio de la aplicación
echo "$(date): Iniciando Kata Assistant desde Desktop Autostart" >> logs/autostart.log

# Ejecutar la aplicación principal
exec python3 src/app/main_app.py >> logs/autostart.log 2>&1