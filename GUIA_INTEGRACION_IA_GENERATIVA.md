# Guía de Integración IA Generativa - Asistente Kata

## 📋 Resumen

Esta guía te ayuda a integrar las capacidades de IA generativa en tu Asistente Kata manteniendo **100% de compatibilidad** con el sistema existente.

**Estado actual**: El RouterCentral está implementado pero **solo usa la ruta clásica**. La IA generativa se agregará en fases posteriores.

## 🚀 Instalación Rápida

### 1. Crear Respaldo
```bash
# Ejecutar respaldo completo
./scripts/backup_sistema.sh
```

### 2. Instalar Dependencias
```bash
# Activar tu entorno virtual actual
source /home/steveen/gcp-tts-venv/bin/activate

# Instalar nuevas dependencias
./scripts/install_generative.sh
```

### 3. Configurar Variables de Entorno
```bash
# Copiar template de configuración
cp .env.template .env

# Editar con tus API keys reales
nano .env
```

## 🔧 Integración en improved_app.py

### Opción A: Integración Mínima (RECOMENDADA)

Agrega estas líneas al inicio de `improved_app.py`:

```python
# === IMPORTACIONES NUEVAS ===
import sys
import os

# Agregar el directorio modules al path
sys.path.append(os.path.join(os.path.dirname(__file__), 'modules'))

try:
    from generative.router_central import RouterCentral
    ROUTER_AVAILABLE = True
except ImportError as e:
    print(f"RouterCentral no disponible: {e}")
    ROUTER_AVAILABLE = False
```

En la clase `ImprovedVoiceAssistant`, modifica el `__init__`:

```python
def __init__(self):
    # ... código existente ...
    
    # === NUEVA LÍNEA AL FINAL DEL __init__ ===
    if ROUTER_AVAILABLE:
        self.router_central = RouterCentral(intent_manager)
        print("RouterCentral inicializado correctamente")
    else:
        self.router_central = None
        print("Usando solo sistema clásico")
```

En el método que procesa texto (busca donde usas `intent_manager`), reemplaza:

```python
# ANTES:
intent_result = intent_manager.classify_intent(text)

# DESPUÉS:
if self.router_central:
    intent_result = self.router_central.process_user_input(text)
else:
    intent_result = intent_manager.classify_intent(text)
```

### Opción B: Wrapper de Compatibilidad

Si quieres máxima seguridad, crea un wrapper:

```python
class IntentWrapper:
    def __init__(self, original_intent_manager):
        self.original_manager = original_intent_manager
        if ROUTER_AVAILABLE:
            self.router = RouterCentral(original_intent_manager)
        else:
            self.router = None
    
    def classify_intent(self, text):
        if self.router:
            result = self.router.process_user_input(text)
            # Convertir resultado del router al formato clásico
            return {
                'intent': result.get('intent'),
                'confidence': result.get('confidence', 0.0),
                'response': result.get('response', ''),
                'entities': result.get('entities', {})
            }
        else:
            return self.original_manager.classify_intent(text)

# Usar el wrapper
intent_manager = IntentWrapper(intent_manager)
```

## 📁 Estructura de Archivos Creados

```
asistente_kata/
├── modules/
│   └── generative/
│       ├── __init__.py
│       └── router_central.py
├── config/
│   └── generative/
├── data/
│   └── preferences/
│       └── user_preferences.json
├── logs/
│   └── generative/
├── scripts/
│   ├── backup_sistema.sh
│   └── install_generative.sh
├── requirements_generative.txt
├── .env.template
└── GUIA_INTEGRACION_IA_GENERATIVA.md
```

## ⚙️ Configuración

### user_preferences.json

El archivo `data/preferences/user_preferences.json` controla:

- **`ia_generativa.habilitada`**: `false` por defecto
- **`confianza_minima_clasica`**: 0.7 (umbral para sistema clásico)
- **`comandos_clasicos.siempre_preferir`**: Lista de comandos que siempre van al sistema clásico
- **`comandos_clasicos.nunca_derivar_ia`**: Comandos críticos que nunca van a IA

### Variables de Entorno (.env)

```bash
# APIs (configura solo las que uses)
OPENAI_API_KEY=tu_api_key_aqui
# GOOGLE_API_KEY ya está configurada en tu sistema

# Límites de seguridad
MAX_REQUESTS_PER_MINUTE=30
MAX_TOKENS_PER_REQUEST=1000

# Logging
GENERATIVE_LOG_LEVEL=INFO
```

## 🔍 Verificación

### 1. Test Básico
```python
# En terminal Python
from modules.generative.router_central import RouterCentral
import intent_manager

router = RouterCentral(intent_manager)
result = router.process_user_input("¿qué hora es?")
print(result)
```

### 2. Verificar Logs
```bash
# Ver logs del router
tail -f logs/generative/router_decisions.log

# Ver estadísticas
python3 -c "
from modules.generative.router_central import RouterCentral
import intent_manager
router = RouterCentral(intent_manager)
print(router.get_stats())
"
```

### 3. Test de Compatibilidad
```bash
# Ejecutar tu app normal y verificar que funciona igual
python3 improved_app.py
```

## 📊 Logging y Debugging

El RouterCentral registra todas las decisiones en:
- `logs/generative/router_decisions.log`
- Métricas en memoria accesibles via `router.get_stats()`
- Decisiones recientes via `router.get_recent_decisions()`

## 🛡️ Seguridad

- ✅ **Sin modificación** del código existente
- ✅ **Fallback automático** al sistema clásico en caso de errores
- ✅ **Comandos críticos** siempre van al sistema clásico
- ✅ **Logging completo** para auditoria
- ✅ **Configuración granular** de preferencias

## 🔄 Próximos Pasos

1. **Fase 1** (Actual): Router implementado, solo ruta clásica
2. **Fase 2**: Implementar GenerativeManager
3. **Fase 3**: Integrar OpenAI/Gemini
4. **Fase 4**: Context management y memoria
5. **Fase 5**: Aprendizaje y personalización

## 🚨 Troubleshooting

### Error: "Module not found"
```bash
# Verificar instalación
python3 -c "import sys; print(sys.path)"
# Asegurar que modules/ está en el path
```

### Error: "RouterCentral not available"
```bash
# Verificar dependencias
pip3 list | grep -E "(openai|google-generativeai)"
# Reinstalar si es necesario
./scripts/install_generative.sh
```

### Sistema no responde
```bash
# Verificar logs
tail logs/generative/router_decisions.log
# Verificar configuración
cat data/preferences/user_preferences.json | jq .ia_generativa
```

## 📞 Soporte

1. Revisar logs en `logs/generative/`
2. Verificar configuración en `data/preferences/user_preferences.json`
3. Probar con `habilitada: false` para deshabilitar temporalmente
4. Usar respaldo en caso de problemas: `tar -xzf backup_file.tar.gz`

---

**¡El sistema está listo para funcionar manteniendo 100% compatibilidad!**