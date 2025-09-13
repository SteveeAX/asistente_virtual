#!/bin/bash

# Script para verificar el estado del autoarranque
# Uso: ./check_autostart.sh

echo "🔍 VERIFICACIÓN DE AUTOARRANQUE - $(date)"
echo "==============================================="

# Verificar si la aplicación está corriendo
APP_PID=$(pgrep -f "main_app.py")
if [ -n "$APP_PID" ]; then
    echo "✅ Aplicación corriendo (PID: $APP_PID)"
    echo "   Comando: $(ps -p $APP_PID -o command --no-headers)"
    echo "   Tiempo: $(ps -p $APP_PID -o etime --no-headers)"
    echo "   CPU: $(ps -p $APP_PID -o %cpu --no-headers)%"
    echo "   Memoria: $(ps -p $APP_PID -o %mem --no-headers)%"
else
    echo "❌ Aplicación NO está corriendo"
fi

echo ""

# Verificar autostart desktop
if [ -f "/home/steveen/.config/autostart/kata-assistant.desktop" ]; then
    echo "✅ Archivo autostart configurado"
    echo "   Comando: $(grep '^Exec=' /home/steveen/.config/autostart/kata-assistant.desktop | cut -d'=' -f2)"
else
    echo "❌ Archivo autostart NO encontrado"
fi

echo ""

# Verificar logs recientes
LOG_FILE="/home/steveen/asistente_kata/logs/autostart.log"
if [ -f "$LOG_FILE" ]; then
    echo "📋 ÚLTIMOS LOGS DE AUTOARRANQUE:"
    echo "================================"
    tail -20 "$LOG_FILE"
else
    echo "⚠️ No hay logs de autoarranque disponibles"
fi

echo ""

# Verificar otros logs
OTHER_LOGS="/home/steveen/asistente_kata/logs"
if [ -d "$OTHER_LOGS" ]; then
    echo "📁 ARCHIVOS DE LOG DISPONIBLES:"
    ls -la "$OTHER_LOGS"/*.log 2>/dev/null | while read line; do
        echo "   $line"
    done
else
    echo "⚠️ Directorio de logs no encontrado"
fi

echo ""
echo "🔧 COMANDOS ÚTILES:"
echo "=================="
echo "• Ver logs en tiempo real: tail -f $LOG_FILE"
echo "• Reiniciar aplicación: pkill -f main_app.py && /home/steveen/asistente_kata/launch_with_logging.sh"
echo "• Verificar procesos: ps aux | grep main_app"