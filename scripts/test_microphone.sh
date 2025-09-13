#!/bin/bash

# Script simple para probar micrófono actual
# Uso: ./test_microphone.sh [quick|full]

set -e

KATA_DIR="/home/steveen/asistente_kata"
ENV_FILE="$KATA_DIR/.env"

# Colores
RED='\033[0;31m'
GREEN='\033[0;32m'
BLUE='\033[0;34m'
YELLOW='\033[1;33m'
NC='\033[0m'

get_current_config() {
    local mic_name="ME6S"
    local sample_rate="48000"
    
    if [ -f "$ENV_FILE" ]; then
        mic_name=$(grep "^TARGET_MIC=" "$ENV_FILE" 2>/dev/null | cut -d'=' -f2 | tr -d '"' || echo "ME6S")
        sample_rate=$(grep "^MIC_SAMPLE_RATE=" "$ENV_FILE" 2>/dev/null | cut -d'=' -f2 || echo "48000")
    fi
    
    echo "$mic_name:$sample_rate"
}

test_audio_detection() {
    echo -e "${BLUE}🎤 Probando detección de audio...${NC}"
    
    python3 -c "
import sounddevice as sd
import numpy as np
import sys
import os
from dotenv import load_dotenv
load_dotenv()

# Obtener configuración actual
target_mic = os.getenv('TARGET_MIC', 'ME6S')
sample_rate = int(os.getenv('MIC_SAMPLE_RATE', '48000'))

print(f'🔧 Configuración: {target_mic} @ {sample_rate}Hz')

# Buscar micrófono
devices = sd.query_devices()
mic_found = False
mic_index = None

for i, device in enumerate(devices):
    if target_mic in device.get('name', '') and device['max_input_channels'] > 0:
        mic_found = True
        mic_index = i
        print(f'✅ Micrófono encontrado: {device[\"name\"]}')
        break

if not mic_found:
    print(f'❌ Error: Micrófono {target_mic} no encontrado')
    sys.exit(1)

# Test de captura
print('🎧 Capturando 3 segundos de audio...')
try:
    duration = 3  # segundos
    audio_data = sd.rec(int(duration * sample_rate), 
                       samplerate=sample_rate, 
                       channels=1, 
                       device=mic_index)
    sd.wait()
    
    # Análisis básico
    volume = np.sqrt(np.mean(audio_data**2))
    max_amplitude = np.max(np.abs(audio_data))
    
    print(f'📊 Volumen RMS: {volume:.4f}')
    print(f'📊 Amplitud máxima: {max_amplitude:.4f}')
    
    if volume > 0.001:
        print('✅ Audio detectado correctamente')
    else:
        print('⚠️  Volumen muy bajo - verificar conexión')
        
except Exception as e:
    print(f'❌ Error en captura: {str(e)}')
    sys.exit(1)
"
}

test_wakeword_config() {
    echo -e "${BLUE}🔊 Verificando configuración de wakeword...${NC}"
    
    python3 -c "
import sys
sys.path.insert(0, 'src')
import os
from dotenv import load_dotenv
load_dotenv()

# Verificar configuración
target_mic = os.getenv('TARGET_MIC', 'ME6S')
sample_rate = int(os.getenv('MIC_SAMPLE_RATE', '48000'))

print(f'🎯 Micrófono objetivo: {target_mic}')
print(f'🎵 Frecuencia de muestreo: {sample_rate}Hz')

# Verificar archivos de wakeword
keyword_file = 'catalina_es_raspberry-pi_v3_0_0.ppn'
model_file = 'porcupine_params_es.pv'

if os.path.exists(keyword_file):
    print(f'✅ Archivo keyword encontrado: {keyword_file}')
else:
    print(f'❌ Archivo keyword no encontrado: {keyword_file}')

if os.path.exists(model_file):
    print(f'✅ Archivo modelo encontrado: {model_file}')
else:
    print(f'❌ Archivo modelo no encontrado: {model_file}')

print('\\n💡 Configuración lista para wakeword detection')
"
}

quick_test() {
    echo -e "${YELLOW}⚡ PRUEBA RÁPIDA DE MICRÓFONO${NC}"
    echo "================================"
    
    config=$(get_current_config)
    mic_name=$(echo $config | cut -d':' -f1)
    sample_rate=$(echo $config | cut -d':' -f2)
    
    echo "📋 Configuración actual: $mic_name @ ${sample_rate}Hz"
    echo ""
    
    test_audio_detection
}

full_test() {
    echo -e "${YELLOW}🔍 PRUEBA COMPLETA DE MICRÓFONO${NC}"
    echo "=================================="
    
    config=$(get_current_config)
    mic_name=$(echo $config | cut -d':' -f1)
    sample_rate=$(echo $config | cut -d':' -f2)
    
    echo "📋 Configuración actual: $mic_name @ ${sample_rate}Hz"
    echo ""
    
    test_audio_detection
    echo ""
    test_wakeword_config
    echo ""
    
    echo -e "${GREEN}✅ Prueba completa finalizada${NC}"
    echo ""
    echo -e "${BLUE}📝 Próximos pasos para evaluar:${NC}"
    echo "1. Decir 'Catalina' para probar wakeword"
    echo "2. Probar comandos de voz diferentes"
    echo "3. Evaluar calidad a diferentes distancias"
    echo "4. Comparar con el otro micrófono usando:"
    echo "   ./switch_microphone.sh ME6S"
    echo "   ./test_microphone.sh full"
}

main() {
    case "${1:-quick}" in
        "quick"|"q")
            quick_test
            ;;
        "full"|"f")
            full_test
            ;;
        *)
            echo "Uso: $0 [quick|full]"
            echo "  quick - Prueba rápida de audio"
            echo "  full  - Prueba completa con configuración"
            exit 1
            ;;
    esac
}

main "$@"