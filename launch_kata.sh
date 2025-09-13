#!/bin/bash

# Script de inicio para Asistente Kata
# Autor: Asistente Kata

# Configurar directorio de trabajo
cd /home/steveen/asistente_kata

# Crear directorio de logs si no existe
mkdir -p logs

# Registrar inicio del script con información detallada
echo "$(date): ========================================" >> logs/launch.log
echo "$(date): Script launch_kata.sh iniciado" >> logs/launch.log
echo "$(date): PID: $$, PPID: $PPID" >> logs/launch.log
echo "$(date): Usuario: $(whoami), HOME: $HOME" >> logs/launch.log
echo "$(date): ========================================" >> logs/launch.log

# Configurar variables de entorno necesarias para X11
export DISPLAY=:0
export XAUTHORITY="$HOME/.Xauthority"
echo "$(date): Variables X11 configuradas - DISPLAY=$DISPLAY, XAUTHORITY=$XAUTHORITY" >> logs/launch.log

# Función mejorada para esperar X11
wait_for_x11() {
    local max_attempts=30
    local attempt=1
    
    echo "$(date): Iniciando verificación de X11..." >> logs/launch.log
    
    while [ $attempt -le $max_attempts ]; do
        if xset q &>/dev/null; then
            echo "$(date): ✅ X11 disponible después de $attempt intentos" >> logs/launch.log
            return 0
        fi
        
        echo "$(date): Intento $attempt/$max_attempts - X11 no disponible, esperando..." >> logs/launch.log
        sleep 2
        attempt=$((attempt + 1))
    done
    
    echo "$(date): ❌ ERROR - X11 no disponible después de $max_attempts intentos" >> logs/launch.log
    return 1
}

# Esperar X11 con función mejorada
if ! wait_for_x11; then
    echo "$(date): ERROR CRÍTICO - Sistema gráfico no disponible, saliendo" >> logs/launch.log
    exit 1
fi

# Activar entorno virtual con verificación mejorada
echo "$(date): Verificando entorno virtual..." >> logs/launch.log
if [ -d "/home/steveen/gcp-tts-venv" ]; then
    source /home/steveen/gcp-tts-venv/bin/activate
    echo "$(date): ✅ Entorno virtual activado desde /home/steveen/gcp-tts-venv" >> logs/launch.log
    echo "$(date): Python path: $(which python3)" >> logs/launch.log
elif [ -d "gcp-tts-venv" ]; then
    source gcp-tts-venv/bin/activate
    echo "$(date): ✅ Entorno virtual activado desde directorio local" >> logs/launch.log
    echo "$(date): Python path: $(which python3)" >> logs/launch.log
else
    echo "$(date): ❌ ERROR - Entorno virtual no encontrado" >> logs/launch.log
    echo "$(date): Directorios disponibles:" >> logs/launch.log
    ls -la /home/steveen/ | grep venv >> logs/launch.log 2>&1
    exit 1
fi

# Configurar PYTHONPATH con logging
export PYTHONPATH="/home/steveen/asistente_kata:$PYTHONPATH"
echo "$(date): PYTHONPATH configurado: $PYTHONPATH" >> logs/launch.log

# Cargar variables de entorno del archivo .env si existe
if [ -f ".env" ]; then
    set -a  # Exportar automáticamente todas las variables
    source .env
    set +a
    echo "$(date): ✅ Variables de entorno cargadas desde .env" >> logs/launch.log
else
    echo "$(date): ⚠️  Archivo .env no encontrado" >> logs/launch.log
fi

# Verificar dependencias críticas
echo "$(date): Verificando dependencias críticas..." >> logs/launch.log
python3 -c "import sys; print('Python version:', sys.version)" >> logs/launch.log 2>&1
python3 -c "import customtkinter; print('CustomTkinter OK')" >> logs/launch.log 2>&1 || echo "$(date): ⚠️  CustomTkinter no disponible" >> logs/launch.log

# Registrar inicio de la aplicación
echo "$(date): ========================================" >> logs/launch.log
echo "$(date): 🚀 Iniciando Asistente Kata (main_app.py)" >> logs/launch.log
echo "$(date): ========================================" >> logs/launch.log

# Ejecutar la aplicación principal con manejo mejorado de errores
python3 src/app/main_app.py >> logs/launch.log 2>&1
exit_code=$?

echo "$(date): ========================================" >> logs/launch.log
echo "$(date): Asistente Kata terminó con código de salida: $exit_code" >> logs/launch.log

# Análisis del código de salida
if [ $exit_code -eq 0 ]; then
    echo "$(date): ✅ Aplicación terminó normalmente" >> logs/launch.log
elif [ $exit_code -eq 1 ]; then
    echo "$(date): ❌ Error general en la aplicación" >> logs/launch.log
elif [ $exit_code -eq 2 ]; then
    echo "$(date): ❌ Error de argumentos/configuración" >> logs/launch.log
else
    echo "$(date): ❌ Error desconocido (código: $exit_code)" >> logs/launch.log
fi

# Reintento solo en caso de errores específicos
if [ $exit_code -ne 0 ] && [ $exit_code -ne 130 ]; then  # 130 = Ctrl+C
    echo "$(date): 🔄 Reintentando inicio después de fallo..." >> logs/launch.log
    sleep 5
    python3 src/app/main_app.py >> logs/launch.log 2>&1
    final_exit=$?
    echo "$(date): Segundo intento terminó con código: $final_exit" >> logs/launch.log
    if [ $final_exit -eq 0 ]; then
        echo "$(date): ✅ Reintento exitoso" >> logs/launch.log
    else
        echo "$(date): ❌ Reintento también falló" >> logs/launch.log
    fi
fi

echo "$(date): ========================================" >> logs/launch.log