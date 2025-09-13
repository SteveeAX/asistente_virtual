# 🚀 AUTOARRANQUE DE KATA ASSISTANT

## ✅ CONFIGURACIÓN COMPLETADA

Tu aplicación **Kata Assistant** y **servidor web** ya están configurados para **arrancar automáticamente** cuando se enciende la Raspberry Pi, **incluido el acceso remoto vía zrok**.

## 🌐 ACCESO AL SISTEMA

- **Local:** `http://localhost:5000` o `http://192.168.10.27:5000`
- **Remoto:** `https://kataadminsteveen.share.zrok.io`

## 📁 SERVICIOS CONFIGURADOS

### 1. **Aplicación Principal** - `kata-assistant.service`
- Ejecuta la aplicación principal de Kata
- Script: `launch_with_logging.sh`

### 2. **Servidor Web** - `kata-web.service`
- Puerto: 5000
- Archivo: `web_server.py` 
- Acceso local: `http://192.168.10.27:5000`

### 3. **Túnel Público** - `zrok.service`
- Ejecutable: `bin/zrok`
- URL pública: `https://kataadminsteveen.share.zrok.io`
- Permite acceso remoto desde cualquier lugar

## 📁 ESTRUCTURA DEL PROYECTO

```
/home/steveen/asistente_kata/
├── bin/zrok              # Ejecutable de zrok (INDEPENDIENTE)
├── web_server.py         # Servidor web Flask
├── reminders.py          # Módulo de compatibilidad
└── launch_with_logging.sh # Script de inicio
```

### Autostart del escritorio
```
/home/steveen/.config/autostart/kata-assistant.desktop
```
- Ejecuta automáticamente cuando se inicia el escritorio
- Llama al script de lanzamiento con logging

### 2. Script de lanzamiento con logging
```
/home/steveen/asistente_kata/launch_with_logging.sh
```
- Verifica el entorno antes de lanzar la aplicación
- Registra todo en logs detallados
- Maneja errores y dependencias

### 3. Script de verificación
```
/home/steveen/asistente_kata/check_autostart.sh
```
- Verifica si la aplicación está corriendo
- Muestra logs recientes
- Proporciona comandos útiles para diagnóstico

## ⚡ COMANDOS ÚTILES

### Ver estado de todos los servicios:
```bash
sudo systemctl status kata-assistant.service
sudo systemctl status kata-web.service  
sudo systemctl status zrok.service
```

### Reiniciar servicios:
```bash
sudo systemctl restart kata-assistant.service
sudo systemctl restart kata-web.service
sudo systemctl restart zrok.service
```

### Ver logs:
```bash
journalctl -u kata-web.service -f
journalctl -u zrok.service -f
tail -f /home/steveen/asistente_kata/logs/launch.log
```

### Proceso de Arranque:

1. **Sistema Gráfico**: Espera a que X11 esté disponible
2. **Entorno Virtual**: Activa `/home/steveen/gcp-tts-venv`
3. **Variables**: Carga configuración desde `.env`
4. **Aplicación**: Ejecuta `src/app/main_app.py`
5. **Recuperación**: Reinicia automáticamente si falla

### Logs y Diagnóstico:

- **Logs del servicio**: `/home/steveen/asistente_kata/logs/service.log`
- **Logs del script**: `/home/steveen/asistente_kata/logs/launch.log`
- **Estado del proceso**: `ps aux | grep main_app.py`

### Notas Importantes:

- La aplicación necesita entorno gráfico (X11) para funcionar
- Requiere que el usuario `steveen` haya iniciado sesión gráfica
- El delay de 20 segundos es necesario para esperar la inicialización completa
- Los fallos se registran y se intenta reinicio automático

### Solución de Problemas:

Si la aplicación no arranca:

1. Verificar logs: `tail -f /home/steveen/asistente_kata/logs/launch.log`
2. Verificar X11: `DISPLAY=:0 xset q`
3. Verificar entorno virtual: `source /home/steveen/gcp-tts-venv/bin/activate`
4. Probar manualmente: `cd /home/steveen/asistente_kata && python3 src/app/main_app.py`

---
**Estado actual**: ✅ FUNCIONANDO - La aplicación arranca automáticamente
**Fecha de configuración**: 8 de Septiembre 2025