# PRD: Parcerolegal.co — MVP v1.0

## Meta
- **Timeline:** 30 días
- **Equipo:** 1 desarrollador
- **Objetivo:** Validar que ciudadanos colombianos pueden consultar legislación en lenguaje natural y recibir respuestas útiles con fuentes verificables.

---

## 1. Alcance del MVP

### 1.1 Qué SÍ incluye (Must Have)
| Funcionalidad | Descripción |
|---------------|-------------|
| Búsqueda en lenguaje natural | Caja de texto única, estilo Google |
| RAG funcional | Recuperación de fragmentos relevantes + generación de respuesta |
| Fuentes clickeables | Enlace directo al artículo/sentencia citada |
| Corpus inicial | Constitución Política (380 arts) + 25 sentencias clave de la Corte Constitucional |
| Responsive básico | Funciona en desktop y móvil |
| Disclaimer legal | Aviso de que no reemplaza asesoría profesional |
| Sin registro | Acceso inmediato, sin auth |

### 1.2 Qué NO incluye (V2+)
| Funcionalidad | Razón para diferir |
|---------------|---------------------|
| Selector de jerga (Abogado/Adulto/Niño) | Complejidad de prompts, validar primero el core |
| Glosario hover | Esfuerzo frontend alto, bajo impacto inicial |
| ETL automatizado diario | Actualizaciones manuales son suficientes para MVP |
| Múltiples fuentes legales | Un corpus bien hecho > muchos corpus mal hechos |
| Optimización <15s | Aceptable 30-45s en MVP |
| Descarga de PDFs | Nice-to-have, el link al original es suficiente |

---

## 2. Arquitectura Técnica

### 2.1 Stack Confirmado
```
┌─────────────────────────────────────────────────────────┐
│                      FRONTEND                           │
│              Next.js (Vercel)                           │
│         - Página única con search box                   │
│         - Renderizado de respuestas con markdown        │
│         - Links a fuentes                               │
└─────────────────────┬───────────────────────────────────┘
                      │ API calls
                      ▼
┌─────────────────────────────────────────────────────────┐
│                      BACKEND                            │
│              FastAPI (Railway)                          │
│         - /query endpoint                               │
│         - Orquestación RAG                              │
│         - Prompt engineering                            │
└───────────┬─────────────────────────┬───────────────────┘
            │                         │
            ▼                         ▼
┌───────────────────────┐   ┌─────────────────────────────┐
│    VECTOR DB          │   │         LLM                 │
│    Qdrant (Cloud)     │   │    Llama 3.1 70B            │
│    - Embeddings       │   │    (via Groq / Together.ai) │
│    - Similarity search│   │    - Temperatura: 0         │
└───────────────────────┘   └─────────────────────────────┘
```

### 2.2 Decisiones Clave

| Decisión | Elección | Justificación |
|----------|----------|---------------|
| LLM Provider | **Groq** (Llama 3.1 70B) | Gratis hasta 14K tokens/min, muy rápido |
| Embeddings | **sentence-transformers/paraphrase-multilingual-MiniLM-L12-v2** | Optimizado para español, ligero |
| Vector DB | **Qdrant Cloud** (free tier) | 1GB gratis, fácil setup, buen rendimiento |
| Frontend hosting | **Vercel** | Deploy automático, edge functions |
| Backend hosting | **Railway** | $5/mes, fácil para FastAPI |
| Chunk size | **800-1000 caracteres** | Balance entre contexto y precisión |
| Chunk overlap | **150 caracteres** | Evita cortar ideas a la mitad |

---

## 3. Corpus MVP

### 3.1 Constitución Política de Colombia (1991)
- **Fuente:** https://www.corteconstitucional.gov.co/inicio/Constitucion%20politica%20de%20Colombia.pdf
- **Estructura:** 380 artículos + preámbulo + títulos
- **Chunking strategy:** 
  - Cada artículo como chunk individual
  - Artículos largos divididos en párrafos
  - Metadata: `{numero_articulo, titulo, capitulo}`

### 3.2 Sentencias Corte Constitucional (25 seleccionadas)
Criterios de selección:
1. Alto impacto ciudadano (tutela, salud, trabajo, educación)
2. Frecuentemente citadas
3. Diversidad temática

**Lista inicial sugerida:**
| # | Sentencia | Tema |
|---|-----------|------|
| 1 | T-760/2008 | Derecho a la salud |
| 2 | C-355/2006 | Despenalización parcial aborto |
| 3 | SU-214/2016 | Matrimonio igualitario |
| 4 | T-025/2004 | Desplazamiento forzado |
| 5 | C-141/2010 | Referendo reelección |
| 6 | T-406/1992 | Estado Social de Derecho |
| 7 | C-221/1994 | Dosis personal |
| 8 | T-120/2024 | IA y derechos fundamentales |
| 9 | C-239/1997 | Eutanasia |
| 10 | T-881/2002 | Dignidad humana |
| 11-25 | ... | (completar según disponibilidad) |

- **Fuente:** https://www.corteconstitucional.gov.co/relatoria/
- **Chunking strategy:**
  - Extraer: Hechos, Problema jurídico, Ratio decidendi, Decisión
  - Ignorar: Salvamentos de voto, notas al pie extensas
  - Metadata: `{numero_sentencia, año, tema, magistrado_ponente}`

---

## 4. Flujo de Usuario

```
[Usuario llega a parcerolegal.co]
            │
            ▼
┌─────────────────────────────────┐
│  "¿Puedo grabar una llamada     │
│   sin permiso de la otra        │
│   persona?"                     │
│         [Buscar]                │
└─────────────────────────────────┘
            │
            ▼ (backend procesa)
┌─────────────────────────────────┐
│  1. Query → Embedding           │
│  2. Búsqueda en Qdrant          │
│  3. Top 5 chunks relevantes     │
│  4. Prompt + chunks → Llama     │
│  5. Respuesta estructurada      │
└─────────────────────────────────┘
            │
            ▼
┌─────────────────────────────────────────────────────────┐
│                                                         │
│  **Respuesta:**                                         │
│                                                         │
│  En Colombia, grabar una conversación telefónica sin    │
│  el consentimiento de la otra parte puede violar el     │
│  derecho a la intimidad protegido por el Artículo 15    │
│  de la Constitución...                                  │
│                                                         │
│  **Fuentes:**                                           │
│  📄 Constitución Política, Art. 15 [Ver original]       │
│  📄 Sentencia T-XXX/20XX [Ver original]                 │
│                                                         │
│  ⚠️ Esta información es orientativa. Consulta a un      │
│  abogado para tu caso específico.                       │
│                                                         │
└─────────────────────────────────────────────────────────┘
```

---

## 5. API Specification

### 5.1 Endpoint Principal

```
POST /api/query
```

**Request:**
```json
{
  "question": "¿Qué es una acción de tutela?"
}
```

**Response:**
```json
{
  "answer": "La acción de tutela es un mecanismo constitucional...",
  "sources": [
    {
      "title": "Constitución Política, Artículo 86",
      "url": "https://www.corteconstitucional.gov.co/...",
      "snippet": "Toda persona tendrá acción de tutela para reclamar..."
    },
    {
      "title": "Sentencia T-406/1992",
      "url": "https://www.corteconstitucional.gov.co/relatoria/...",
      "snippet": "La tutela procede contra acciones u omisiones..."
    }
  ],
  "processing_time_ms": 2340
}
```

### 5.2 Manejo de Consultas Fuera de Alcance

Si la query no tiene chunks relevantes (similarity < 0.65):

```json
{
  "answer": "A mí lo de alucinar no me va. Tu pregunta parece estar fuera del alcance de la legislación que tengo disponible (Constitución Política y sentencias clave de la Corte Constitucional). Intenta reformular tu pregunta o consulta sobre derechos fundamentales, tutelas, o temas constitucionales.",
  "sources": [],
  "out_of_scope": true
}
```

---

## 6. Prompt Engineering

### 6.1 System Prompt (v1)

```
Eres Parcerolegal, un asistente legal colombiano. Tu función es ayudar a ciudadanos a entender la legislación colombiana de forma clara y accesible.

REGLAS ESTRICTAS:
1. SOLO responde basándote en los fragmentos de documentos proporcionados.
2. Si los fragmentos no contienen información suficiente, di: "No encontré información específica sobre esto en mi base de datos actual."
3. NUNCA inventes artículos, sentencias, o información legal.
4. Cita SIEMPRE la fuente específica (artículo o sentencia).
5. Usa lenguaje claro que un ciudadano sin formación legal pueda entender.
6. Estructura tu respuesta así:
   - Respuesta directa a la pregunta (2-3 oraciones)
   - Explicación más detallada si es necesario
   - Menciona las fuentes específicas usadas

CONTEXTO DISPONIBLE:
{chunks}

PREGUNTA DEL USUARIO:
{question}
```

### 6.2 Parámetros LLM

```python
{
    "model": "llama-3.1-70b-versatile",
    "temperature": 0,
    "max_tokens": 1024,
    "top_p": 1,
    "frequency_penalty": 0,
    "presence_penalty": 0
}
```

---

## 7. Cronograma Detallado (30 días)

### Semana 1: Data Pipeline (Días 1-7)

| Día | Tarea | Entregable |
|-----|-------|------------|
| 1-2 | Scraping Constitución | `constitucion.json` con 380+ artículos estructurados |
| 3-4 | Scraping 10 sentencias | `sentencias/` folder con JSONs parseados |
| 5 | Setup Qdrant Cloud + embeddings model | Conexión funcionando |
| 6 | Script de chunking + embedding | `embed.py` funcional |
| 7 | Carga inicial a Qdrant | Base de datos poblada, queries de prueba |

**Checkpoint Semana 1:** Puedo hacer similarity search desde Python y obtener chunks relevantes.

### Semana 2: Backend RAG (Días 8-14)

| Día | Tarea | Entregable |
|-----|-------|------------|
| 8 | Setup FastAPI + estructura proyecto | Repo con `/app`, `/tests`, `requirements.txt` |
| 9 | Integración Groq API | Llamadas a Llama funcionando |
| 10-11 | Endpoint `/query` completo | RAG pipeline end-to-end |
| 12 | Prompt engineering + testing | 20 queries de prueba documentadas |
| 13 | Manejo de errores + edge cases | Out-of-scope detection, timeouts |
| 14 | Deploy a Railway | Backend live en URL pública |

**Checkpoint Semana 2:** Puedo hacer curl a mi API en Railway y obtener respuestas con fuentes.

### Semana 3: Frontend (Días 15-21)

| Día | Tarea | Entregable |
|-----|-------|------------|
| 15 | Setup Next.js + Tailwind | Repo frontend inicializado |
| 16-17 | UI: Search box + results | Componentes funcionales |
| 18 | Integración con backend | Queries reales funcionando |
| 19 | Responsive + loading states | UX pulida en móvil |
| 20 | Disclaimer + about page | Contenido legal listo |
| 21 | Deploy a Vercel | Frontend live |

**Checkpoint Semana 3:** parcerolegal.co resuelve preguntas reales end-to-end.

### Semana 4: Testing + Launch (Días 22-30)

| Día | Tarea | Entregable |
|-----|-------|------------|
| 22-23 | Testing con 10 usuarios beta | Feedback documentado |
| 24-25 | Bug fixes + ajustes de prompts | Issues resueltos |
| 26 | Agregar 15 sentencias más | Corpus expandido a 25 |
| 27 | Performance testing | Métricas de latencia |
| 28 | SEO básico + meta tags | Indexable por Google |
| 29 | Soft launch | Compartir en círculo cercano |
| 30 | Documentación | README completo, arquitectura documentada |

**Checkpoint Semana 4:** MVP usable, con feedback real incorporado.

---

## 8. Métricas de Éxito MVP

| Métrica | Target MVP | Cómo Medir |
|---------|------------|------------|
| Queries resueltas | >70% útiles | Feedback manual de beta testers |
| Latencia p95 | <45 segundos | Logs de Railway |
| Uptime | >95% | Railway/Vercel dashboards |
| Zero alucinaciones | 100% respuestas con fuente o "no sé" | Testing manual de 50 queries |
| Mobile usable | Sin scroll horizontal, botones clickeables | Testing en 3 dispositivos |

---

## 9. Riesgos y Mitigaciones

| Riesgo | Probabilidad | Impacto | Mitigación |
|--------|--------------|---------|------------|
| Groq rate limits | Media | Alto | Tener Together.ai como backup |
| Scraping bloqueado | Baja | Alto | Descargar PDFs manualmente como fallback |
| Chunks mal cortados | Alta | Medio | Testing intensivo semana 1, ajustar overlap |
| Respuestas irrelevantes | Media | Alto | Threshold de similarity estricto (0.65+) |
| Scope creep | Alta | Alto | Revisar este PRD cada lunes, decir NO |

---

## 10. Post-MVP Roadmap (Preview)

Para después del MVP, en orden de prioridad:

1. **V1.1 (Mes 2):** Agregar Código Civil completo
2. **V1.2 (Mes 2-3):** Selector de jerga (empezar con Adulto vs Abogado)
3. **V1.3 (Mes 3):** ETL automatizado + más sentencias
4. **V2.0 (Mes 4+):** Comparador de normas, historial de búsquedas, API pública

---

## 11. Decisiones Pendientes

Antes de empezar a construir, confirmar:

- [ ] ¿Dominio `parcerolegal.co` disponible/comprado?
- [ ] ¿Cuenta de Groq creada con API key?
- [ ] ¿Qdrant Cloud free tier activado?
- [ ] ¿Las 25 sentencias específicas definidas?

---

*Última actualización: [Fecha de hoy]*
*Versión: 1.0-MVP*