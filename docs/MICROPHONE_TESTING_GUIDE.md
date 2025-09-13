# 🎤 Guía de Pruebas de Micrófono - Kata Assistant

## 📋 Resumen

Esta guía te ayudará a probar y comparar el nuevo micrófono **LCS USB Audio** con el anterior **ME6S** de manera controlada y sin perder configuraciones.

## 🎯 Micrófonos Disponibles

| Micrófono | Frecuencia | Estado Actual |
|-----------|------------|---------------|
| **LCS USB Audio** | 44100Hz | 🆕 Nuevo (a probar) |
| **ME6S** | 48000Hz | ✅ Actual (respaldo) |

## 🛠️ Comandos Disponibles

### 1. Cambiar Micrófono
```bash
# Cambiar a LCS (nuevo)
./switch_microphone.sh LCS

# Cambiar a ME6S (anterior)  
./switch_microphone.sh ME6S

# Selección automática
./switch_microphone.sh auto

# Ver estado actual
./switch_microphone.sh status
```

### 2. Probar Micrófono
```bash
# Prueba rápida (3 segundos de audio)
./test_microphone.sh quick

# Prueba completa (audio + configuración)
./test_microphone.sh full
```

### 3. Reiniciar Asistente
```bash
# Reiniciar para aplicar cambios
./run_kata.sh
```

## 📊 Plan de Evaluación Manual

### Fase 1: Configuración Inicial (5 minutos)
1. **Verificar micrófono actual:**
   ```bash
   ./switch_microphone.sh status
   ```

2. **Cambiar a LCS:**
   ```bash
   ./switch_microphone.sh LCS
   ```

3. **Probar configuración:**
   ```bash
   ./test_microphone.sh quick
   ```

### Fase 2: Pruebas de Wakeword (10 minutos)
1. **Reiniciar asistente:**
   ```bash
   ./run_kata.sh
   ```

2. **Probar detección de "Catalina":**
   - ✅ Distancia normal (1-2 metros)
   - ✅ Distancia lejana (3-4 metros)
   - ✅ Voz baja
   - ✅ Voz normal
   - ✅ Con ruido de fondo

3. **Anotar resultados:**
   - ¿Se detecta "Catalina" consistentemente?
   - ¿Hay falsos positivos?
   - ¿Tiempo de respuesta aceptable?

### Fase 3: Pruebas de Comandos de Voz (15 minutos)
1. **Comandos simples:**
   - "qué hora es"
   - "cuál es la fecha" 
   - "enciende el enchufe"

2. **Comandos complejos:**
   - "cuéntame un chiste"
   - "envía un mensaje a Steven"
   - "recuérdame tomar medicina a las 8"

3. **Evaluar calidad:**
   - ¿Se transcribe correctamente?
   - ¿Hay errores de reconocimiento?
   - ¿Respuesta fluida o con cortes?

### Fase 4: Comparación con ME6S (10 minutos)
1. **Cambiar a ME6S (si está disponible):**
   ```bash
   ./switch_microphone.sh ME6S
   ./run_kata.sh
   ```

2. **Repetir las mismas pruebas**

3. **Comparar resultados**

## 📈 Métricas a Evaluar

### ✅ Criterios de Éxito para LCS:
- **Wakeword Detection:** ≥95% de detección "Catalina"
- **Falsos Positivos:** <5% activaciones incorrectas
- **Transcripción STT:** ≥90% precisión en comandos
- **Distancia Efectiva:** ≥2 metros útiles
- **Experiencia Usuario:** Sin frustración notable

### 📊 Escala de Evaluación:
- **🟢 Excelente:** Mejor que ME6S
- **🟡 Bueno:** Igual a ME6S  
- **🔴 Necesita Mejora:** Peor que ME6S

## 🔍 Troubleshooting

### Problema: "Micrófono no encontrado"
```bash
# Verificar dispositivos disponibles
./switch_microphone.sh status

# Reconectar USB y probar
./switch_microphone.sh auto
```

### Problema: "Audio muy bajo"
- Verificar conexión física
- Ajustar posición del micrófono
- Comprobar niveles de audio del sistema:
  ```bash
  pactl list sources | grep -A5 "LCS"
  ```

### Problema: "Wakeword no funciona"
- Verificar que el asistente se reinició después del cambio
- Comprobar logs:
  ```bash
  tail -f logs/launch.log | grep -i wakeword
  ```

## 📝 Registro de Pruebas

### Plantilla para Anotar Resultados:

**Fecha:** ___________
**Micrófono:** [ ] LCS [ ] ME6S

**Wakeword Detection:**
- Distancia 1m: [ ] ✅ [ ] ❌
- Distancia 3m: [ ] ✅ [ ] ❌  
- Voz baja: [ ] ✅ [ ] ❌
- Con ruido: [ ] ✅ [ ] ❌

**Comandos de Voz:**
- Hora/fecha: [ ] ✅ [ ] ❌
- Enchufes: [ ] ✅ [ ] ❌
- Mensajes: [ ] ✅ [ ] ❌
- Recordatorios: [ ] ✅ [ ] ❌

**Evaluación General:**
- Calidad: [ ] 🟢 [ ] 🟡 [ ] 🔴
- Velocidad: [ ] 🟢 [ ] 🟡 [ ] 🔴
- Confiabilidad: [ ] 🟢 [ ] 🟡 [ ] 🔴

**Notas adicionales:**
_________________________________
_________________________________

## 🏁 Decisión Final

Después de completar las pruebas:

### Si LCS es mejor:
```bash
./switch_microphone.sh LCS
echo "LCS configurado como micrófono principal"
```

### Si ME6S sigue siendo mejor:
```bash
./switch_microphone.sh ME6S  
echo "ME6S mantiene configuración actual"
```

### Para cambios futuros:
- Los scripts quedan listos para alternar fácilmente
- Configuración se guarda automáticamente en `.env`
- Sin riesgo de perder configuraciones anteriores

---

**¡Buena suerte con las pruebas! 🎤✨**