#!/bin/bash

# Script para cambiar micrófono manualmente entre ME6S y LCS
# Uso: ./switch_microphone.sh [LCS|ME6S|auto]

set -e

KATA_DIR="/home/steveen/asistente_kata"
ENV_FILE="$KATA_DIR/.env"

# Colores para output
RED='\033[0;31m'
GREEN='\033[0;32m'
BLUE='\033[0;34m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

print_header() {
    echo -e "${BLUE}🎤 KATA MICROPHONE SWITCHER${NC}"
    echo "=================================="
}

list_available_mics() {
    echo -e "${YELLOW}📋 Micrófonos disponibles:${NC}"
    python3 -c "
import sounddevice as sd
devices = sd.query_devices()
input_devices = [(i, d) for i, d in enumerate(devices) if d['max_input_channels'] > 0]

for i, device in input_devices:
    status = '✅ ME6S' if 'ME6S' in device['name'] else '🆕 LCS' if 'LCS' in device['name'] else '📱 Otro'
    print(f'  {status} ID:{i:2d} | {device[\"name\"]} | {device[\"max_input_channels\"]}ch | {device[\"default_samplerate\"]:.0f}Hz')
"
}

get_current_mic() {
    if [ -f "$ENV_FILE" ]; then
        grep "^TARGET_MIC=" "$ENV_FILE" 2>/dev/null | cut -d'=' -f2 | tr -d '"' || echo "ME6S"
    else
        echo "ME6S"
    fi
}

set_microphone() {
    local mic_name="$1"
    local sample_rate="$2"
    
    # Crear o actualizar .env
    if [ ! -f "$ENV_FILE" ]; then
        touch "$ENV_FILE"
    fi
    
    # Actualizar configuración
    if grep -q "^TARGET_MIC=" "$ENV_FILE"; then
        sed -i "s/^TARGET_MIC=.*/TARGET_MIC=\"$mic_name\"/" "$ENV_FILE"
    else
        echo "TARGET_MIC=\"$mic_name\"" >> "$ENV_FILE"
    fi
    
    if grep -q "^MIC_SAMPLE_RATE=" "$ENV_FILE"; then
        sed -i "s/^MIC_SAMPLE_RATE=.*/MIC_SAMPLE_RATE=$sample_rate/" "$ENV_FILE"
    else
        echo "MIC_SAMPLE_RATE=$sample_rate" >> "$ENV_FILE"
    fi
    
    echo -e "${GREEN}✅ Configuración actualizada:${NC}"
    echo "   Micrófono: $mic_name"
    echo "   Frecuencia: ${sample_rate}Hz"
}

verify_mic_connection() {
    local mic_name="$1"
    python3 -c "
import sounddevice as sd
devices = sd.query_devices()
found = any('$mic_name' in device.get('name', '') for device in devices if device['max_input_channels'] > 0)
exit(0 if found else 1)
"
}

main() {
    print_header
    
    case "${1:-}" in
        "LCS"|"lcs")
            echo -e "${BLUE}🔄 Cambiando a micrófono LCS USB Audio...${NC}"
            if verify_mic_connection "LCS"; then
                set_microphone "LCS" "44100"
                echo -e "${GREEN}🎯 Micrófono LCS configurado correctamente${NC}"
                echo "📝 Reinicia el asistente para aplicar cambios"
            else
                echo -e "${RED}❌ Error: Micrófono LCS no encontrado${NC}"
                exit 1
            fi
            ;;
        "ME6S"|"me6s")
            echo -e "${BLUE}🔄 Cambiando a micrófono ME6S...${NC}"
            if verify_mic_connection "ME6S"; then
                set_microphone "ME6S" "48000"
                echo -e "${GREEN}🎯 Micrófono ME6S configurado correctamente${NC}"
                echo "📝 Reinicia el asistente para aplicar cambios"
            else
                echo -e "${RED}❌ Error: Micrófono ME6S no encontrado${NC}"
                exit 1
            fi
            ;;
        "auto")
            echo -e "${BLUE}🔍 Selección automática...${NC}"
            if verify_mic_connection "LCS"; then
                echo "🆕 LCS disponible - configurando como primario"
                set_microphone "LCS" "44100"
            elif verify_mic_connection "ME6S"; then
                echo "✅ ME6S disponible - configurando como respaldo"
                set_microphone "ME6S" "48000"
            else
                echo -e "${RED}❌ No se encontró ningún micrófono conocido${NC}"
                exit 1
            fi
            ;;
        "status"|"")
            echo -e "${YELLOW}📊 Estado actual:${NC}"
            current_mic=$(get_current_mic)
            echo "   Micrófono configurado: $current_mic"
            if [ -f "$ENV_FILE" ] && grep -q "^MIC_SAMPLE_RATE=" "$ENV_FILE"; then
                sample_rate=$(grep "^MIC_SAMPLE_RATE=" "$ENV_FILE" | cut -d'=' -f2)
                echo "   Frecuencia: ${sample_rate}Hz"
            fi
            echo ""
            list_available_mics
            echo ""
            echo -e "${BLUE}💡 Uso:${NC}"
            echo "   ./switch_microphone.sh LCS    # Cambiar a LCS USB Audio"
            echo "   ./switch_microphone.sh ME6S   # Cambiar a ME6S"
            echo "   ./switch_microphone.sh auto   # Selección automática"
            echo "   ./switch_microphone.sh status # Ver estado actual"
            ;;
        *)
            echo -e "${RED}❌ Opción no válida: $1${NC}"
            echo "Uso: $0 [LCS|ME6S|auto|status]"
            exit 1
            ;;
    esac
}

main "$@"