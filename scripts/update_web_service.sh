#!/bin/bash

# ===============================================
# SCRIPT DE ACTUALIZACIÓN DEL SERVICIO WEB
# Actualiza el servicio kata-web con el nuevo sistema multi-usuario
# ===============================================

set -e  # Salir si hay algún error

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_DIR="$(dirname "$SCRIPT_DIR")"
BACKUP_DIR="$PROJECT_DIR/data/backups/service_update_$(date +%Y%m%d_%H%M%S)"

echo "🔄 ACTUALIZANDO SERVICIO WEB CON SISTEMA MULTI-USUARIO"
echo "======================================================"
echo "📁 Directorio del proyecto: $PROJECT_DIR"
echo "💾 Directorio de backup: $BACKUP_DIR"
echo ""

# ===============================================
# VALIDACIONES PREVIAS
# ===============================================

echo "1️⃣ Validando sistema..."

# Verificar que estamos en el directorio correcto
if [[ ! -f "$PROJECT_DIR/web_server.py" ]]; then
    echo "❌ Error: web_server.py no encontrado en $PROJECT_DIR"
    exit 1
fi

# Verificar que el sistema multi-usuario está disponible
cd "$PROJECT_DIR"
python3 -c "
import web_server
if not hasattr(web_server, 'MULTI_USER_AVAILABLE') or not web_server.MULTI_USER_AVAILABLE:
    print('❌ Sistema multi-usuario no disponible')
    exit(1)
print('✅ Sistema multi-usuario validado')
" || exit 1

# Verificar que hay usuarios en el sistema
python3 -c "
from database.models.user_manager import user_manager
users = user_manager.get_users_list()
if len(users) == 0:
    print('❌ No hay usuarios en el sistema')
    exit(1)
print(f'✅ {len(users)} usuarios encontrados')
" || exit 1

echo "✅ Validaciones completadas"
echo ""

# ===============================================
# CREAR BACKUP
# ===============================================

echo "2️⃣ Creando backup del sistema actual..."

mkdir -p "$BACKUP_DIR"

# Backup del servicio actual
sudo cp /etc/systemd/system/kata-web.service "$BACKUP_DIR/"
echo "✅ Servicio respaldado"

# Backup de archivos críticos
cp "$PROJECT_DIR/web_server.py" "$BACKUP_DIR/web_server_current.py"
cp -r "$PROJECT_DIR/templates" "$BACKUP_DIR/"
cp -r "$PROJECT_DIR/static" "$BACKUP_DIR/"
echo "✅ Archivos web respaldados"

# Backup de datos de usuarios
if [[ -d "$PROJECT_DIR/data" ]]; then
    cp -r "$PROJECT_DIR/data" "$BACKUP_DIR/"
    echo "✅ Datos de usuarios respaldados"
fi

echo "💾 Backup completo en: $BACKUP_DIR"
echo ""

# ===============================================
# VERIFICAR INTEGRIDAD DEL NUEVO SISTEMA
# ===============================================

echo "3️⃣ Verificando integridad del nuevo sistema..."

# Ejecutar validador
python3 "$PROJECT_DIR/validate_web_interface.py" > /tmp/validation_result.txt 2>&1

if grep -q "¡Validación exitosa!" /tmp/validation_result.txt; then
    echo "✅ Validación del nuevo sistema exitosa"
else
    echo "❌ Error en validación del nuevo sistema:"
    cat /tmp/validation_result.txt
    echo ""
    echo "🔧 Por favor corrige los errores antes de continuar"
    exit 1
fi

echo ""

# ===============================================
# ACTUALIZAR SERVICIO
# ===============================================

echo "4️⃣ Actualizando servicio systemd..."

# Preguntar confirmación
echo "⚠️  IMPORTANTE: Se reiniciará el servicio web"
echo "⚠️  El servicio estará fuera de línea por unos segundos"
echo ""
read -p "¿Continuar con la actualización? (y/N): " confirm

if [[ ! "$confirm" =~ ^[Yy]$ ]]; then
    echo "❌ Actualización cancelada por el usuario"
    exit 1
fi

echo ""
echo "🔄 Reiniciando servicio con nuevo sistema..."

# Recargar y reiniciar servicio
sudo systemctl daemon-reload
echo "✅ Configuración systemd recargada"

sudo systemctl restart kata-web.service
echo "✅ Servicio reiniciado"

# Esperar un momento para que el servicio inicie
sleep 3

# Verificar que el servicio está ejecutándose
if sudo systemctl is-active --quiet kata-web.service; then
    echo "✅ Servicio activo"
else
    echo "❌ Error: El servicio no está activo"
    
    # Mostrar logs del servicio
    echo "📋 Últimos logs del servicio:"
    sudo journalctl -u kata-web.service --lines=10 --no-pager
    
    echo ""
    echo "🔧 Restaurando backup..."
    # Aquí podrías agregar lógica de rollback si es necesario
    exit 1
fi

# ===============================================
# VERIFICAR FUNCIONAMIENTO
# ===============================================

echo ""
echo "5️⃣ Verificando funcionamiento del nuevo sistema..."

# Esperar a que el servicio esté completamente listo
sleep 5

# Probar que el servicio responde
if curl -s http://localhost:5000/ | grep -q "Gestor de Kata"; then
    echo "✅ Interfaz web respondiendo"
else
    echo "⚠️ La interfaz web no responde correctamente"
fi

# Probar API de usuarios
if curl -s http://localhost:5000/api/users | grep -q "success"; then
    echo "✅ API multi-usuario funcionando"
else
    echo "⚠️ API multi-usuario no responde correctamente"
fi

# Mostrar estado del servicio
echo ""
echo "📊 Estado del servicio:"
sudo systemctl status kata-web.service --no-pager --lines=5

echo ""
echo "🎉 ACTUALIZACIÓN COMPLETADA"
echo "=============================="
echo "✅ Servicio web actualizado con sistema multi-usuario"
echo "🌐 Interfaz disponible en: http://localhost:5000"
echo "👥 Nueva pestaña 'Usuarios' disponible para gestión multi-usuario"
echo "💾 Backup disponible en: $BACKUP_DIR"
echo ""
echo "🔧 Para ver logs en tiempo real:"
echo "   sudo journalctl -u kata-web.service -f"
echo ""
echo "🔄 Para rollback (si es necesario):"
echo "   sudo cp $BACKUP_DIR/kata-web.service /etc/systemd/system/"
echo "   sudo systemctl daemon-reload && sudo systemctl restart kata-web.service"