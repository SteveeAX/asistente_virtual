# Guía de Rollback - Sistema Multi-Usuario Kata

## 📋 Información del Rollback

Esta guía describe cómo revertir el sistema Kata al estado anterior si ocurren problemas con el sistema multi-usuario.

## ⚠️ Cuándo Usar el Rollback

Usar este proceso si:
- El servicio web no inicia correctamente
- Las APIs devuelven errores persistentes
- Los datos de usuario no se cargan
- Problemas de rendimiento graves
- Errores en la aplicación principal (`improved_app.py`)

## 🔄 Pasos de Rollback

### 1. Detener el Servicio Actual

```bash
sudo systemctl stop kata-web.service
```

### 2. Restaurar Archivos desde Backup

El sistema creó automáticamente un backup en:
`/home/steveen/asistente_kata/data/backups/service_update_YYYYMMDD_HHMMSS/`

```bash
# Ubicar el backup más reciente
BACKUP_DIR=$(ls -1t /home/steveen/asistente_kata/data/backups/service_update_* | head -1)
echo "Usando backup: $BACKUP_DIR"

# Restaurar configuración systemd
sudo cp "$BACKUP_DIR/kata-web.service" /etc/systemd/system/

# Restaurar archivos web
cp "$BACKUP_DIR/web_server_current.py" /home/steveen/asistente_kata/web_server.py
cp -r "$BACKUP_DIR/templates" /home/steveen/asistente_kata/
cp -r "$BACKUP_DIR/static" /home/steveen/asistente_kata/
```

### 3. Revertir improved_app.py

```bash
# Restaurar imports originales en improved_app.py
sed -i '/# --- Sistema Multi-Usuario ---/,/logging.warning.*Sistema multi-usuario no disponible/d' /home/steveen/asistente_kata/improved_app.py

# Restaurar función get_reminders_service (eliminar)
sed -i '/# === FUNCIÓN HELPER PARA REMINDERS ===/,/return reminders/d' /home/steveen/asistente_kata/improved_app.py

# Restaurar llamadas directas a reminders
sed -i 's/service = get_reminders_service()/# service removed/g' /home/steveen/asistente_kata/improved_app.py
sed -i 's/service\./reminders./g' /home/steveen/asistente_kata/improved_app.py
```

### 4. Revertir RouterCentral

```bash
# Restaurar carga de preferencias JSON en RouterCentral
cp /home/steveen/asistente_kata/modules/generative/router_central.py /home/steveen/asistente_kata/modules/generative/router_central.py.backup

# Editar manualmente _load_user_preferences para usar solo JSON
```

### 5. Restaurar Servicio

```bash
# Recargar configuración systemd
sudo systemctl daemon-reload

# Reiniciar servicio
sudo systemctl restart kata-web.service

# Verificar estado
sudo systemctl status kata-web.service
```

### 6. Verificar Funcionalidad

```bash
# Probar interfaz web
curl http://localhost:5000/

# Probar APIs básicas
curl http://localhost:5000/api/reminders
curl http://localhost:5000/api/contacts
curl http://localhost:5000/api/tasks
```

## 🗂️ Restaurar Datos Legacy

Si necesitas restaurar datos desde el sistema JSON legacy:

```bash
# Los datos originales están en el backup
BACKUP_DIR=$(ls -1t /home/steveen/asistente_kata/data/backups/service_update_* | head -1)

# Restaurar archivos JSON originales
if [ -d "$BACKUP_DIR/data" ]; then
    cp -r "$BACKUP_DIR/data/preferences" /home/steveen/asistente_kata/data/
    cp -r "$BACKUP_DIR/data/contacts" /home/steveen/asistente_kata/data/
    cp -r "$BACKUP_DIR/data/reminders" /home/steveen/asistente_kata/data/
fi
```

## 🔍 Verificación Post-Rollback

Después del rollback, verificar:

1. **Servicio Web**: `http://localhost:5000` carga correctamente
2. **APIs Funcionales**: Recordatorios, contactos y tareas responden
3. **Aplicación Principal**: `improved_app.py` inicia sin errores
4. **Datos Preservados**: Configuraciones y datos de usuario intactos

## 📞 En Caso de Problemas

Si el rollback no resuelve los problemas:

1. **Revisar Logs**:
   ```bash
   sudo journalctl -u kata-web.service --lines=50
   ```

2. **Reinicializar Completamente**:
   ```bash
   sudo systemctl stop kata-web.service
   cd /home/steveen/asistente_kata
   git stash  # Guardar cambios locales
   git checkout HEAD~1  # Ir al commit anterior
   sudo systemctl start kata-web.service
   ```

3. **Contactar Soporte**: Reportar el issue con logs completos

## 🚨 Prevención de Pérdida de Datos

- **IMPORTANTE**: El sistema multi-usuario mantiene copias de todos los datos
- Los datos están en `/home/steveen/asistente_kata/data/users/`
- Nunca eliminar el directorio `data/` sin hacer backup
- Los backups automáticos se crean en cada actualización

---

**Fecha de Creación**: 2025-08-18  
**Versión**: 1.0.0  
**Sistema**: Asistente Kata Multi-Usuario