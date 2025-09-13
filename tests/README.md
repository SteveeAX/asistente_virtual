# Tests - Asistente Kata

Esta carpeta contiene todos los archivos de prueba del proyecto para mantener la organización.

## Archivos de Prueba

### `test_message_db.py`
- **Propósito**: Prueba la funcionalidad completa de la base de datos de mensajes Telegram
- **Qué prueba**:
  - Agregar mensajes nuevos
  - Contar mensajes no leídos
  - Obtener mensajes más antiguos (orden correcto)
  - Marcar mensajes como leídos y eliminarlos
  - Gestión automática de contactos

### `test_routing_fix.py`
- **Propósito**: Verifica que la corrección de routing para comandos clásicos funcione
- **Qué prueba**:
  - Detección de frases de hora ("dime la hora", "qué horas son", etc.)
  - Routing correcto hacia sistema clásico
  - Funcionamiento case-insensitive

### `test_telegram_integration.py`
- **Propósito**: Prueba la integración completa del sistema de mensajes Telegram
- **Qué prueba**:
  - Inicialización correcta de MessageReceiver
  - Procesamiento simulado de mensajes de Telegram
  - Identificación automática de contactos
  - Integración con base de datos de mensajes
  - Sistema de callbacks para notificaciones

### `test_notification_system.py`
- **Propósito**: Prueba el sistema completo de notificaciones (audio + visual)
- **Qué prueba**:
  - Flujo completo de notificación desde mensaje nuevo
  - Audio TTS: "Tienes mensaje nuevo de [Contacto]"
  - Actualización visual del contador de mensajes
  - Marcado de mensajes como notificados en BD
  - Integración entre MessageNotifier y UI

### `check_messages.py`
- **Propósito**: Utilidad para verificar estado de mensajes en BD
- **Qué hace**:
  - Muestra contador de mensajes no leídos
  - Lista mensajes recientes con detalles
  - Útil para debugging y verificación manual

## Ejecutar Pruebas

Desde el directorio raíz del proyecto:

```bash
# Probar BD de mensajes
python tests/test_message_db.py

# Probar routing de comandos
python tests/test_routing_fix.py

# Probar integración Telegram
python tests/test_telegram_integration.py

# Probar sistema completo de notificaciones
python tests/test_notification_system.py

# Verificar mensajes en BD (utilidad)
python tests/check_messages.py
```

## Agregar Nuevas Pruebas

1. Crear archivo `test_[nombre].py` en esta carpeta
2. Agregar al inicio del archivo:
   ```python
   import sys
   import os
   # Agregar path del proyecto (ahora estamos en tests/)
   sys.path.append(os.path.join(os.path.dirname(__file__), '..'))
   ```
3. Importar módulos necesarios del proyecto
4. Actualizar este README con descripción de la nueva prueba