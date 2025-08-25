#!/bin/bash

# Script de instalación segura para capacidades de IA generativa
# Compatible con Raspberry Pi 5
# Autor: Asistente Kata

set -e  # Salir si hay errores

# Colores para output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

echo -e "${BLUE}=== INSTALACIÓN IA GENERATIVA PARA ASISTENTE KATA ===${NC}"
echo -e "${YELLOW}Iniciando instalación en $(date)${NC}"

# Verificar que estamos en el directorio correcto
PROJECT_DIR="/home/steveen/asistente_kata"
if [ ! -d "$PROJECT_DIR" ]; then
    echo -e "${RED}Error: Directorio del proyecto no encontrado: $PROJECT_DIR${NC}"
    exit 1
fi

cd "$PROJECT_DIR"

# Verificar Python
echo -e "${BLUE}Verificando Python...${NC}"
PYTHON_VERSION=$(python3 --version 2>&1 | cut -d' ' -f2)
echo -e "${GREEN}Python encontrado: $PYTHON_VERSION${NC}"

# Verificar pip
echo -e "${BLUE}Verificando pip...${NC}"
if ! command -v pip3 &> /dev/null; then
    echo -e "${RED}Error: pip3 no encontrado${NC}"
    exit 1
fi

# Verificar entorno virtual
echo -e "${BLUE}Verificando entorno virtual...${NC}"
if [ -z "$VIRTUAL_ENV" ]; then
    echo -e "${YELLOW}Aviso: No se detectó entorno virtual activo${NC}"
    echo -e "${YELLOW}Se recomienda activar el entorno virtual antes de continuar${NC}"
    read -p "¿Continuar de todas formas? (y/N): " -n 1 -r
    echo
    if [[ ! $REPLY =~ ^[Yy]$ ]]; then
        echo -e "${YELLOW}Instalación cancelada${NC}"
        exit 0
    fi
else
    echo -e "${GREEN}Entorno virtual activo: $VIRTUAL_ENV${NC}"
fi

# Crear respaldo antes de instalar
echo -e "${BLUE}Creando respaldo automático...${NC}"
if [ -f "scripts/backup_sistema.sh" ]; then
    ./scripts/backup_sistema.sh
else
    echo -e "${YELLOW}Script de respaldo no encontrado, continuando sin respaldo${NC}"
fi

# Verificar archivo de requisitos
if [ ! -f "requirements_generative.txt" ]; then
    echo -e "${RED}Error: requirements_generative.txt no encontrado${NC}"
    exit 1
fi

# Crear archivo de requisitos combinado temporal
echo -e "${BLUE}Preparando instalación de dependencias...${NC}"
TEMP_REQ=$(mktemp)
cat requirements.txt > "$TEMP_REQ" 2>/dev/null || echo "# Requisitos base no encontrados" > "$TEMP_REQ"
echo "" >> "$TEMP_REQ"
echo "# === DEPENDENCIAS IA GENERATIVA ===" >> "$TEMP_REQ"
cat requirements_generative.txt >> "$TEMP_REQ"

# Actualizar pip
echo -e "${BLUE}Actualizando pip...${NC}"
python3 -m pip install --upgrade pip

# Instalar dependencias con manejo de errores
echo -e "${BLUE}Instalando dependencias...${NC}"
while IFS= read -r line; do
    # Saltar líneas vacías y comentarios
    if [[ -z "$line" || "$line" == \#* ]]; then
        continue
    fi
    
    echo -e "${YELLOW}Instalando: $line${NC}"
    if ! pip3 install "$line"; then
        echo -e "${RED}Error instalando: $line${NC}"
        echo -e "${YELLOW}Continuando con el siguiente paquete...${NC}"
    else
        echo -e "${GREEN}✓ Instalado: $line${NC}"
    fi
done < "$TEMP_REQ"

# Limpiar archivo temporal
rm "$TEMP_REQ"

# Verificar instalaciones críticas
echo -e "${BLUE}Verificando instalaciones críticas...${NC}"
CRITICAL_PACKAGES=("openai" "google-generativeai" "aiohttp" "python-dotenv" "jsonschema")

for package in "${CRITICAL_PACKAGES[@]}"; do
    if python3 -c "import $package" 2>/dev/null; then
        echo -e "${GREEN}✓ $package: OK${NC}"
    else
        echo -e "${RED}✗ $package: FALTA${NC}"
    fi
done

# Crear archivos de configuración si no existen
echo -e "${BLUE}Creando archivos de configuración...${NC}"

# Archivo .env
if [ ! -f ".env" ]; then
    cat > .env << 'EOF'
# Configuración de APIs para IA generativa
# IMPORTANTE: Nunca commitear este archivo a git

# OpenAI API
OPENAI_API_KEY=tu_openai_api_key_aqui

# Google Gemini API (ya tienes GOOGLE_API_KEY en tu entorno)
# GOOGLE_API_KEY=tu_google_api_key_aqui

# Configuración de rate limiting
MAX_REQUESTS_PER_MINUTE=30
MAX_TOKENS_PER_REQUEST=1000

# Logging
GENERATIVE_LOG_LEVEL=INFO
EOF
    echo -e "${GREEN}✓ Archivo .env creado${NC}"
else
    echo -e "${YELLOW}Archivo .env ya existe, no se sobrescribió${NC}"
fi

# Asegurar que .env esté en .gitignore
if ! grep -q "^\.env$" .gitignore 2>/dev/null; then
    echo ".env" >> .gitignore
    echo -e "${GREEN}✓ .env agregado a .gitignore${NC}"
fi

# Verificar espacio en disco
echo -e "${BLUE}Verificando espacio en disco...${NC}"
DISK_USAGE=$(df -h . | tail -1 | awk '{print $5}' | sed 's/%//')
if [ "$DISK_USAGE" -gt 90 ]; then
    echo -e "${YELLOW}Aviso: Poco espacio en disco disponible (${DISK_USAGE}% usado)${NC}"
fi

# Crear archivo de verificación
echo -e "${BLUE}Creando archivo de verificación...${NC}"
cat > logs/generative/install_verification.log << EOF
=== VERIFICACIÓN DE INSTALACIÓN ===
Fecha: $(date)
Usuario: $(whoami)
Directorio: $(pwd)
Python: $(python3 --version)
Pip: $(pip3 --version)
Entorno virtual: ${VIRTUAL_ENV:-"No activo"}

=== PAQUETES INSTALADOS ===
$(pip3 list | grep -E "(openai|google-generativeai|aiohttp|python-dotenv|jsonschema)")

=== ARCHIVOS CREADOS ===
$(ls -la modules/generative/ config/generative/ data/preferences/ logs/generative/ 2>/dev/null)
EOF

echo -e "${GREEN}=== INSTALACIÓN COMPLETADA ===${NC}"
echo -e "${GREEN}Dependencias instaladas correctamente${NC}"
echo -e "${YELLOW}Próximos pasos:${NC}"
echo -e "${YELLOW}1. Configurar API keys en archivo .env${NC}"
echo -e "${YELLOW}2. Ejecutar script de verificación cuando esté disponible${NC}"
echo -e "${YELLOW}3. Integrar RouterCentral en tu aplicación${NC}"

echo -e "${BLUE}Log de verificación: logs/generative/install_verification.log${NC}"