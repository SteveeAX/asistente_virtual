# Legacy Backup - Asistente Kata

Este directorio contiene los archivos originales que fueron refactorizados y organizados en la nueva estructura `src/`.

## 📁 Estructura:

### `utils/`
Utilidades centrales (ahora en `src/utils/`)
- `system_actions.py` → `src/utils/system_actions.py`
- `firestore_logger.py` → `src/utils/firestore_logger.py`

### `core/`
Módulos de hardware y audio (ahora en `src/core/`)
- `tts_manager.py` → `src/core/audio/tts_manager.py`
- `stt_manager.py` → `src/core/audio/stt_manager.py`
- `wakeword_detector.py` → `src/core/audio/wakeword_detector.py`
- `button_manager.py` → `src/core/hardware/button_manager.py`
- `smart_home_manager.py` → `src/core/smart_home/smart_home_manager.py`

### `messaging/`
Sistema de mensajes (ahora en `src/messaging/`)
- `voice_message_sender.py` → `src/messaging/voice_sender.py`
- `message_receiver.py` → `src/messaging/message_receiver.py`
- `message_reader.py` → `src/messaging/message_reader.py`
- `message_notifier.py` → `src/messaging/message_notifier.py`
- `contact_normalizer.py` → `src/messaging/contact_normalizer.py`

### `ui/`
Interfaces de usuario (ahora en `src/ui/`)
- `web_server.py` → `src/ui/web/app.py`
- `clock_interface.py` → `src/ui/desktop/clock_interface.py`
- `listening_indicator.py` → `src/ui/desktop/listening_indicator.py`

### `ai/`
Módulos de IA (ahora en `src/ai/`)
- `intent_manager.py` → `src/ai/intent_manager.py`
- `message_ai.py` → `src/ai/message_ai.py`
- `voice_reminder_manager.py` → `src/ai/voice_reminder_manager.py`

### `reminders/`
Sistema de recordatorios (ahora en `src/core/reminders/`)
- `time_interpreter.py` → `src/core/reminders/time_interpreter.py`

### `misc/`
Archivos de testing y utilidades varias
- `contact_tab.py`, `contact_tab_updated.py`
- `reminder_tab.py`, `reminder_tab_updated.py`
- `export_data.py`
- `validate_web_interface.py`
- `quick_web_test.py`
- `simple_mic_test.py`
- `verify_shared_db.py`

## 🚨 Importante:

- **NO eliminar esta carpeta** - es tu respaldo de seguridad
- Los archivos aquí son las versiones originales funcionales
- En caso de problemas con la nueva estructura, puedes usar estos como referencia
- La aplicación actual usa la nueva estructura en `src/`

## 🔄 Recuperación:

Si necesitas restaurar algún archivo:
```bash
cp legacy_backup/categoria/archivo.py ./archivo.py
```

Última actualización: 2025-09-07 - Refactoring v2.0.0