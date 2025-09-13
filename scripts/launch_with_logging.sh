#!/bin/bash

# Script de lanzamiento con logging detallado para autoarranque

LOG_FILE="/home/steveen/asistente_kata/logs/autostart.log"
APP_PATH="/home/steveen/asistente_kata/src/app/main_app.py"
VENV_PATH="/home/steveen/gcp-tts-venv/bin/python"

# Crear directorio de logs si no existe
mkdir -p /home/steveen/asistente_kata/logs

# Función de logging con timestamp
log() {
    echo "$(date '+%Y-%m-%d %H:%M:%S') - AUTOSTART: $1" | tee -a "$LOG_FILE"
}

log "========================================="
log "🚀 INICIO DE AUTOARRANQUE"
log "========================================="
log "Script: $0"
log "PID: $$, PPID: $PPID"
log "Usuario: $(whoami)"
log "HOME: $HOME"
log "DISPLAY: $DISPLAY"
log "PWD: $(pwd)"

# Verificar entorno gráfico
log "🖥️ Verificando entorno gráfico..."
if command -v xset >/dev/null 2>&1; then
    if xset q >/dev/null 2>&1; then
        log "✅ Entorno gráfico disponible"
        xset -display :0 q 2>&1 | head -3 | while read line; do
            log "X11_INFO: $line"
        done
    else
        log "❌ ERROR: xset q falló"
        exit 1
    fi
else
    log "⚠️ ADVERTENCIA: xset no disponible"
fi

# Verificar directorio de trabajo
log "📁 Verificando directorio de trabajo..."
if [ -d "/home/steveen/asistente_kata" ]; then
    cd /home/steveen/asistente_kata
    log "✅ Directorio de trabajo: $(pwd)"
else
    log "❌ ERROR: Directorio del proyecto no encontrado"
    exit 1
fi

# Verificar entorno virtual
log "🐍 Verificando entorno virtual..."
if [ -f "$VENV_PATH" ]; then
    log "✅ Python virtual encontrado: $VENV_PATH"
    PYTHON_VERSION=$($VENV_PATH --version 2>&1)
    log "PYTHON_VERSION: $PYTHON_VERSION"
else
    log "❌ ERROR: Python virtual no encontrado en $VENV_PATH"
    exit 1
fi

# Verificar aplicación principal
log "📱 Verificando aplicación principal..."
if [ -f "$APP_PATH" ]; then
    log "✅ Aplicación encontrada: $APP_PATH"
    APP_SIZE=$(wc -l < "$APP_PATH")
    log "APP_SIZE: $APP_SIZE líneas"
else
    log "❌ ERROR: Aplicación no encontrada en $APP_PATH"
    exit 1
fi

# Verificar conectividad de red
log "🌐 Verificando conectividad..."
if ping -c 1 8.8.8.8 >/dev/null 2>&1; then
    log "✅ Conectividad de red OK"
else
    log "⚠️ ADVERTENCIA: Sin conectividad de red"
fi

# Verificar credenciales de Google Cloud
log "🔑 Verificando credenciales..."
CREDS_FILE="/home/steveen/asistente_kata/config/credentials/gleaming-terra-454706-r0-0b19bb6937f8.json"
if [ -f "$CREDS_FILE" ]; then
    log "✅ Credenciales de Google Cloud encontradas"
else
    log "⚠️ ADVERTENCIA: Credenciales de Google Cloud no encontradas"
fi

# Verificar dependencias críticas
log "📦 Verificando dependencias..."
$VENV_PATH -c "import customtkinter" 2>/dev/null
if [ $? -eq 0 ]; then
    log "✅ CustomTkinter disponible"
else
    log "❌ ERROR: CustomTkinter no disponible"
    exit 1
fi

# Configurar variables de entorno
export PYTHONPATH="/home/steveen/asistente_kata:$PYTHONPATH"
export GOOGLE_APPLICATION_CREDENTIALS="$CREDS_FILE"
log "🔧 Variables de entorno configuradas"

# Cargar .env si existe
if [ -f ".env" ]; then
    set -a
    source .env
    set +a
    log "✅ Variables de .env cargadas"
else
    log "⚠️ Archivo .env no encontrado"
fi

# Esperar un poco para que el sistema esté completamente listo
log "⏳ Esperando 5 segundos para estabilización del sistema..."
sleep 5

# Lanzar aplicación
log "🚀 LANZANDO APLICACIÓN PRINCIPAL..."
log "COMANDO: $VENV_PATH $APP_PATH"

# Ejecutar con redirección de logs
exec "$VENV_PATH" "$APP_PATH" 2>&1 | while IFS= read -r line; do
    echo "$(date '+%Y-%m-%d %H:%M:%S') - APP: $line" | tee -a "$LOG_FILE"
done

# Esta línea solo se ejecuta si la aplicación falla al iniciar
log "❌ APLICACIÓN TERMINÓ INESPERADAMENTE"