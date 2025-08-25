# Análisis Detallado: Construcción de Prompt Personalizado

## Resumen Ejecutivo

Este documento analiza en profundidad el sistema de **construcción de prompts personalizados** del Asistente Kata. El PromptBuilder es el componente responsable de crear instrucciones inteligentes y contextualizadas que se envían a la IA Gemini para generar respuestas personalizadas y apropiadas para cada usuario.

---

## 1. Visión General del PromptBuilder

### ¿Qué es un Prompt?
Un **prompt** es el conjunto de instrucciones que se envía a la IA para guiar su comportamiento y respuesta. Es como darle a un humano el contexto completo antes de pedirle que responda algo.

### Objetivo del PromptBuilder
Transformar una consulta simple como *"¿Cómo cuido las plantas?"* en una instrucción completa que incluye:
- **Quién es el usuario** (nombre, edad, intereses)
- **Qué sabe sobre el tema** (conocimientos previos)
- **Cómo debe responder** (tono, estilo, límites)
- **Contexto de la conversación** (intercambios anteriores si son relevantes)

---

## 2. Arquitectura del Sistema de Construcción

### Flujo de Construcción (6 Capas)
```
Consulta del usuario
       ↓
1. Prompt Base del Sistema
       ↓
2. Plantilla de Dominio Específico
       ↓
3. Personalización con Datos del Usuario
       ↓
4. Adaptación a Preferencias
       ↓
5. Contexto de la Consulta
       ↓
6. Memoria Conversacional (si aplica)
       ↓
Prompt Final Completo
```

---

## 3. Análisis Detallado de Cada Capa

### Capa 1: Prompt Base del Sistema
**Función:** Establece la identidad y reglas fundamentales del asistente.

**Estructura:**
```
Eres Kata, un asistente virtual cercano y amigable para [NOMBRE_USUARIO].

REGLAS FUNDAMENTALES:
- Máximo 40 palabras por respuesta (muy importante)
- Usa un tono cercano pero respetuoso (no formal)
- Sé empática, clara y cálida
- Para temas de salud: sugiere consultar médico
- Si no entiendes, pide que repita

Tu objetivo es ser útil y hacer que [NOMBRE_USUARIO] se sienta acompañada.
```

**Características:**
- **Personalización inmediata** con el nombre del usuario
- **Límites claros** (40 palabras, temas de salud)
- **Personalidad definida** (cercana, empática, cálida)
- **Objetivo claro** (hacer sentir acompañado)

### Capa 2: Plantilla de Dominio Específico
**Función:** Añade contexto especializado según el tema de la consulta.

El sistema detecta el **dominio temático** y selecciona la plantilla apropiada:

#### Ejemplo - Dominio "Plantas":
```
CONTEXTO PERSONAL DE [NOMBRE_USUARIO]:
- Le encantan las plantas medicinales: sábila, toronjil, hierbaluisa
- Es experta en cuidado de plantas de interior
- Conoce remedios caseros: [ejemplos específicos]
- Vive en [ciudad]
- Puedes usar: "¿Cómo está su jardincito?"

ESTILO: Reconoce su conocimiento y experiencia
```

#### Ejemplo - Dominio "Cocina":
```
CONTEXTO PERSONAL DE [NOMBRE_USUARIO]:
- Sus comidas favoritas: caldo de bola, chupe de pescado
- Conoce recetas tradicionales ecuatorianas
- Ejemplos: menestrón, tallarín, locro
- De la región de [ciudad]
- Puedes usar: "¿Qué rico ha cocinado hoy?"

ESTILO: Reconoce su experiencia culinaria
```

#### Otros Dominios Disponibles:
- **Mascotas:** Incluye nombres de mascotas, consejos de cuidado
- **Entretenimiento:** Gustos musicales, actividades preferidas
- **Tiempo:** Información climática contextualizada
- **Personal:** Información sobre el asistente y sus capacidades
- **Dispositivos:** Instrucciones de control del hogar
- **Conversacional:** Saludos apropiados según la hora
- **Información:** Consultas educativas y explicativas

### Capa 3: Personalización con Datos del Usuario
**Función:** Reemplaza las variables de plantilla con información real del usuario.

**Variables de Personalización (40+ variables):**

#### Datos Básicos:
- `{nombre_usuario}`: "María López"
- `{edad}`: "68"
- `{ciudad}`: "Quito"
- `{region}`: "Sierra"

#### Contexto Temporal:
- `{hora_actual}`: "14:30"
- `{periodo_dia}`: "tarde"
- `{saludo}`: "Buenas tardes"

#### Datos Específicos por Dominio:
- `{plantas_conoce}`: "sábila, toronjil, hierbaluisa, orégano"
- `{comidas_favoritas}`: "caldo de bola, chupe de pescado, menestrón"
- `{nombres_mascotas}`: "Coco, Troy"
- `{entretenimiento_preferido}`: "telenovelas, música de los 80"

#### Capacidades del Sistema:
- `{mis_capacidades}`: "recordatorios, control dispositivos, respuestas inteligentes"
- `{proposito}`: "asistencia personal integral"

#### Frases Cercanas Contextuales:
- `{frase_cercana_plantas}`: "¿Cómo está su jardincito?"
- `{frase_cercana_cocina}`: "¿Qué rico ha cocinado hoy?"
- `{frase_cercana_mascotas}`: "¿Cómo están Coco y Troy?"

### Capa 4: Adaptación a Preferencias
**Función:** Ajusta el estilo según las preferencias específicas del usuario.

**Tipos de Adaptaciones:**

#### Longitud de Respuestas:
```
IMPORTANTE: Mantén respuestas MUY cortas (máximo 40 palabras).
```

#### Uso de Emojis:
```
NO uses emojis en las respuestas.
```
(Configurable por usuario)

#### Estilo de Conversación:
- **Cercano Respetuoso:** "Tono: Cercano pero respetuoso, como una buena amistad."
- **Formal Profesional:** "Tono: Formal y profesional."
- **Familiar Cariñoso:** "Tono: Familiar y cariñoso."

#### Referencias Personales:
```
Incluye referencias personales cuando sea apropiado.
```

### Capa 5: Contexto de la Consulta
**Función:** Añade información específica sobre la pregunta actual.

**Elementos Analizados:**

#### Tipo de Pregunta:
- **Pregunta sobre qué:** "Tipo: pregunta sobre qué"
- **Pregunta sobre cómo:** "Tipo: pregunta sobre cómo"
- **Pregunta sobre cuándo:** "Tipo: pregunta sobre cuándo"

#### Tono Detectado:
- **Positivo:** "El usuario parece estar de buen ánimo"
- **Negativo:** "El usuario puede estar frustrado, responde con extra empatía"
- **Urgente:** "El usuario necesita una respuesta rápida y directa"

#### Contexto Temporal:
```
Contexto temporal relevante: tarde
```

### Capa 6: Memoria Conversacional
**Función:** Incluye el intercambio anterior si es relevante para la consulta actual.

**Estructura de Memoria:**
```
CONTEXTO CONVERSACIONAL (hace 2 min):
Usuario preguntó: "¿Cómo cuido la sábila?"
Yo respondí: "La sábila necesita poca agua y luz indirecta..."

NOTA: La consulta actual parece relacionada (continuation_request). 
Usa este contexto para dar una respuesta coherente y conectada.
```

**Criterios para Incluir Memoria:**
- Referencias explícitas ("eso", "también", "cuéntame más")
- Solicitudes de continuación ("más información", "explica mejor")
- Conversación activa (menos de 2 minutos)
- Mismo dominio temático sin cambio fuerte

---

## 4. Ejemplo Completo de Prompt Construido

### Escenario:
- **Usuario:** María López, 68 años, Quito
- **Consulta:** "¿Y eso cuándo debo regarlo?"
- **Contexto:** Hace 2 minutos preguntó sobre el cuidado de la sábila
- **Hora:** 14:30 (tarde)
- **Dominio:** Plantas

### Prompt Final Generado:

```
Eres Kata, un asistente virtual cercano y amigable para María López.

REGLAS FUNDAMENTALES:
- Máximo 40 palabras por respuesta (muy importante)
- Usa un tono cercano pero respetuoso (no formal)
- Sé empática, clara y cálida
- Para temas de salud: sugiere consultar médico
- Si no entiendes, pide que repita

Tu objetivo es ser útil y hacer que María López se sienta acompañada.

CONTEXTO PERSONAL DE María López:
- Le encantan las plantas medicinales: sábila, toronjil, hierbaluisa, orégano
- Es experta en cuidado de plantas de interior
- Conoce remedios caseros: té de toronjil para los nervios, sábila para quemaduras
- Vive en Quito
- Puedes usar: "¿Cómo está su jardincito?"

ESTILO: Reconoce su conocimiento y experiencia

ADAPTACIONES ESPECÍFICAS:
- IMPORTANTE: Mantén respuestas MUY cortas (máximo 40 palabras).
- NO uses emojis en las respuestas.
- Tono: Cercano pero respetuoso, como una buena amistad.
- Incluye referencias personales cuando sea apropiado.

CONTEXTO DE LA CONSULTA:
- Tipo: pregunta sobre cuándo
- Contexto temporal relevante: tarde

CONTEXTO CONVERSACIONAL (hace 2 min):
Usuario preguntó: "¿Cómo cuido la sábila?"
Yo respondí: "La sábila necesita poca agua y luz indirecta. Riegue solo cuando la tierra esté seca, María."

NOTA: La consulta actual parece relacionada (explicit_reference). 
Usa este contexto para dar una respuesta coherente y conectada.

CONSULTA DEL USUARIO:
¿Y eso cuándo debo regarlo?

RESPUESTA:
```

### Respuesta Generada por Gemini:
*"Cada 15 días aproximadamente, María. En Quito, con el clima seco, observe si la tierra está seca antes de regar."*

---

## 5. Flujo de Variables y Datos

### Fuentes de Información:

#### Base de Datos del Usuario:
```sql
user_preferences:
  - usuario: {nombre, edad, ciudad}
  - intereses: {plantas_conoce, comidas_favoritas, mascotas}
  - comunicacion: {estilo_respuesta, usar_emojis}
  - configuracion_ai: {estilo_conversacion}
```

#### ContextEnricher:
```python
QueryContext:
  - domain: "plantas"
  - confidence: 0.8
  - temporal_context: {periodo_dia, hora, saludo}
  - query_characteristics: {tipo_pregunta, tono}
  - personalization_data: {todos los datos del usuario}
```

#### ConversationMemory:
```python
MemoryContext:
  - has_memory: true
  - memory_reason: "explicit_reference"
  - last_query: "¿Cómo cuido la sábila?"
  - last_response: "La sábila necesita poca agua..."
  - minutes_ago: 2
```

### Proceso de Integración:
1. **Carga de datos** desde base de datos del usuario
2. **Análisis de contexto** por ContextEnricher
3. **Verificación de memoria** por ConversationMemory
4. **Construcción por capas** en PromptBuilder
5. **Validación final** y envío a Gemini

---

## 6. Ventajas del Sistema Multicapa

### Modularidad
- **Cada capa es independiente** y modificable
- **Fácil añadir nuevos dominios** sin afectar otros
- **Personalización granular** por tipo de usuario

### Escalabilidad
- **Plantillas reutilizables** para diferentes usuarios
- **Variables dinámicas** que se adaptan automáticamente
- **Sistema de fallback** si faltan datos

### Personalización Profunda
- **Contexto cultural** (Ecuador, tradiciones locales)
- **Referencias personales** (nombres, gustos, mascotas)
- **Estilo adaptativo** según preferencias del usuario

### Coherencia Conversacional
- **Memoria inteligente** que mantiene el hilo
- **Detección de cambios de tema** para evitar confusiones
- **Contexto temporal** apropiado (saludo según la hora)

---

## 7. Casos de Uso Especiales

### Primer Uso (Sin Historial):
```
Sin memoria conversacional
+ Contexto personal básico
+ Plantilla de dominio
= Respuesta personalizada inicial
```

### Conversación Continua:
```
Memoria del intercambio anterior
+ Detección de referencia ("eso", "también")
+ Mismo dominio
= Respuesta coherente y conectada
```

### Cambio de Tema:
```
Detección de cambio fuerte (plantas → tiempo)
+ Nuevo contexto de dominio
+ Sin memoria (se resetea)
= Respuesta apropiada al nuevo tema
```

### Usuario Nuevo:
```
Preferencias por defecto
+ Plantilla genérica
+ Sin personalización específica
= Respuesta amigable pero básica
```

---

## 8. Optimizaciones y Eficiencia

### Gestión de Tokens
- **Prompts selectivos:** Solo se incluye información relevante
- **Memoria condicional:** Solo se añade si es útil
- **Plantillas optimizadas:** Información densa y precisa

### Cacheo de Datos
- **Preferencias de usuario** se cargan una vez por sesión
- **Plantillas de dominio** se reutilizan eficientemente
- **Contexto temporal** se calcula dinámicamente

### Fallbacks Robustos
- **Datos faltantes:** Variables por defecto
- **Dominios no reconocidos:** Plantilla general
- **Errores de personalización:** Modo básico sin fallar

---

## 9. Impacto en la Calidad de Respuestas

### Antes del PromptBuilder:
```
Usuario: "¿Cómo cuido las plantas?"
IA: "Las plantas necesitan agua y luz solar."
```

### Después del PromptBuilder:
```
Usuario: "¿Cómo cuido las plantas?"
IA: "María, con su experiencia en sábila y toronjil, 
     ya sabe que necesitan poca agua. En Quito, 
     riegue solo cuando la tierra esté seca."
```

### Diferencias Clave:
- **Usa el nombre** del usuario
- **Reconoce experiencia previa** en plantas
- **Contexto geográfico** (Quito)
- **Referencia conocimientos** específicos (sábila, toronjil)
- **Consejo específico** para el clima local

---

## Conclusión

El sistema de **construcción de prompts personalizados** de Kata representa una **arquitectura avanzada de personalización** que transforma consultas simples en interacciones profundamente personalizadas y contextualmente apropiadas.

Mediante un **sistema de 6 capas modulares**, el PromptBuilder logra:

1. **Personalización profunda** basada en datos reales del usuario
2. **Coherencia conversacional** a través de memoria inteligente
3. **Especialización por dominio** con conocimiento específico
4. **Adaptabilidad cultural** y geográfica
5. **Eficiencia de recursos** con inclusión selectiva de información

Este sistema permite que Kata no solo responda preguntas, sino que **converse de manera natural y personalizada**, haciendo que cada usuario se sienta comprendido y acompañado de manera única.

La **arquitectura modular** garantiza mantenibilidad y escalabilidad, mientras que la **integración de múltiples fuentes de contexto** asegura respuestas que son tanto precisas como personalmente relevantes para cada usuario individual.