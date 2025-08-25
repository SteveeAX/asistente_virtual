#!/bin/bash

# Script de respaldo completo del sistema antes de agregar IA generativa
# Autor: Asistente Kata
# Fecha: $(date)

set -e  # Salir si hay errores

# Colores para output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

echo -e "${BLUE}=== RESPALDO COMPLETO SISTEMA ASISTENTE KATA ===${NC}"
echo -e "${YELLOW}Iniciando respaldo en $(date)${NC}"

# Directorio base del proyecto
PROJECT_DIR="/home/steveen/asistente_kata"
BACKUP_DIR="/home/steveen/backups/asistente_kata_$(date +%Y%m%d_%H%M%S)"

# Crear directorio de respaldo
echo -e "${BLUE}Creando directorio de respaldo: ${BACKUP_DIR}${NC}"
mkdir -p "$BACKUP_DIR"

# Respaldar código fuente
echo -e "${BLUE}Respaldando código fuente...${NC}"
cp -r "$PROJECT_DIR"/*.py "$BACKUP_DIR/" 2>/dev/null || echo "Sin archivos .py adicionales"
cp -r "$PROJECT_DIR"/templates "$BACKUP_DIR/" 2>/dev/null || echo "Sin directorio templates"
cp -r "$PROJECT_DIR"/static "$BACKUP_DIR/" 2>/dev/null || echo "Sin directorio static"

# Respaldar archivos de configuración
echo -e "${BLUE}Respaldando configuraciones...${NC}"
cp "$PROJECT_DIR"/requirements.txt "$BACKUP_DIR/" 2>/dev/null || echo "Sin requirements.txt"
cp "$PROJECT_DIR"/launch_kata.sh "$BACKUP_DIR/" 2>/dev/null || echo "Sin launch_kata.sh"
cp "$PROJECT_DIR"/*.json "$BACKUP_DIR/" 2>/dev/null || echo "Sin archivos JSON"

# Respaldar base de datos
echo -e "${BLUE}Respaldando base de datos...${NC}"
cp "$PROJECT_DIR"/app.db "$BACKUP_DIR/" 2>/dev/null || echo "Sin base de datos app.db"

# Respaldar logs importantes
echo -e "${BLUE}Respaldando logs...${NC}"
mkdir -p "$BACKUP_DIR/logs"
cp "$PROJECT_DIR"/*.log "$BACKUP_DIR/logs/" 2>/dev/null || echo "Sin archivos de log"

# Respaldar archivos de documentación
echo -e "${BLUE}Respaldando documentación...${NC}"
cp "$PROJECT_DIR"/*.md "$BACKUP_DIR/" 2>/dev/null || echo "Sin archivos markdown"

# Crear snapshot del git
echo -e "${BLUE}Creando snapshot de git...${NC}"
cd "$PROJECT_DIR"
git status > "$BACKUP_DIR/git_status.txt" 2>/dev/null || echo "Sin repositorio git"
git log --oneline -10 > "$BACKUP_DIR/git_recent_commits.txt" 2>/dev/null || echo "Sin commits recientes"

# Crear archivo de información del sistema
echo -e "${BLUE}Guardando información del sistema...${NC}"
cat > "$BACKUP_DIR/system_info.txt" << EOF
=== INFORMACIÓN DEL SISTEMA ===
Fecha del respaldo: $(date)
Usuario: $(whoami)
Hostname: $(hostname)
Kernel: $(uname -r)
Python version: $(python3 --version)
Pip packages instalados:
$(pip list)

=== VARIABLES DE ENTORNO RELEVANTES ===
GOOGLE_APPLICATION_CREDENTIALS=$GOOGLE_APPLICATION_CREDENTIALS
GOOGLE_API_KEY=${GOOGLE_API_KEY:0:10}... (truncado por seguridad)

=== PROCESOS RELACIONADOS ===
$(ps aux | grep -i kata || echo "Ninguno")
EOF

# Crear checksums para verificación
echo -e "${BLUE}Generando checksums...${NC}"
find "$BACKUP_DIR" -type f -exec md5sum {} \; > "$BACKUP_DIR/checksums.md5"

# Comprimir respaldo
echo -e "${BLUE}Comprimiendo respaldo...${NC}"
tar -czf "${BACKUP_DIR}.tar.gz" -C "$(dirname $BACKUP_DIR)" "$(basename $BACKUP_DIR)"

# Limpiar directorio temporal
rm -rf "$BACKUP_DIR"

echo -e "${GREEN}=== RESPALDO COMPLETADO ===${NC}"
echo -e "${GREEN}Archivo de respaldo: ${BACKUP_DIR}.tar.gz${NC}"
echo -e "${GREEN}Tamaño: $(du -h ${BACKUP_DIR}.tar.gz | cut -f1)${NC}"
echo -e "${YELLOW}Para restaurar: tar -xzf ${BACKUP_DIR}.tar.gz${NC}"

# Mostrar últimos 3 respaldos
echo -e "${BLUE}Últimos respaldos disponibles:${NC}"
ls -lht /home/steveen/backups/asistente_kata_*.tar.gz 2>/dev/null | head -3 || echo "Este es el primer respaldo"

echo -e "${GREEN}¡Respaldo completado exitosamente!${NC}"