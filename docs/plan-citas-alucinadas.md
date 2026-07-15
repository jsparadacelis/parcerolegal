# Plan: citas alucinadas del LLM en las respuestas RAG

## Estado
Detectado — pendiente de arreglar.

## Resumen
El LLM inserta en la respuesta referencias numéricas (`[13]`, `[22]`, `[48]`, …)
que **no corresponden a ningún fragmento** del contexto. El caso de uso solo pasa
`top_k` fragmentos al prompt (por defecto 5, numerados `[1]`–`[5]`), pero el modelo
cita índices fuera de ese rango. Son **citas inventadas**: el usuario ve marcadores
que no apuntan a ninguna fuente real y no hay forma de verificarlos.

Esto es más grave que las fuentes duplicadas: rompe la promesa central del producto
(*"respuestas útiles con fuentes verificables"*, PRD §Objetivo), porque una cita que
no se puede rastrear es peor que ninguna cita.

## Evidencia (consulta real contra producción)
- **Backend:** `https://parcerolegal-production.up.railway.app/api/query`
- **Pregunta:** `¿Cuáles son los derechos fundamentales en Colombia?`
  (una de las de `data/scripts/test_queries.py`)
- **Fragmentos en contexto:** 5 → referencias válidas: solo `[1]`–`[5]`.
- **Respuesta del modelo (fragmento):**

  ```
  * Igualdad [1], [13]
  * Paz [1], [22]
  * Integridad personal [12]
  * Libre desarrollo de la personalidad [1], [16]
  * Derecho a la salud y al saneamiento básico [1], [49]
  * Seguridad social [1], [48]
  ```

- **Índices alucinados observados:** `[12]`, `[13]`, `[16]`, `[22]`, `[48]`, `[49]`
  — todos fuera del rango `[1]`–`[5]`.

## Causa raíz (hipótesis)
1. **El prompt no acota el rango de citas.** En `backend/app/application/query_use_case.py`,
   `_SYSTEM_ROLE` dice *"Cita los fragmentos usando [1], [2], etc."* pero no le indica
   al modelo **cuántos** fragmentos hay ni que **está prohibido** citar fuera de ese
   rango. El modelo, entrenado sobre textos jurídicos con muchas notas al pie,
   "completa" con números plausibles.
2. **No hay validación/saneamiento de la salida.** La respuesta del LLM se devuelve
   tal cual (`answer=self._llm.generate(...)`) sin comprobar que cada `[n]` citado
   exista realmente en `filtered`.
3. Posible agravante: `llm_temperature = 0.0` reduce pero no elimina el problema; es
   estructural del prompt, no del muestreo.

## Opciones de solución
### A. Endurecer el prompt (barato, primero)
- Numerar explícitamente e indicar el total: *"Tienes N fragmentos, numerados [1]…[N].
  Cita ÚNICAMENTE esos números. Nunca uses un número mayor que N."*
- Inyectar `N = len(filtered)` en `_USER_TEMPLATE` / `_SYSTEM_ROLE`.

### B. Validación post-generación (defensa en profundidad)
- Tras `generate()`, extraer con regex todos los `[\d+]` de la respuesta.
- Si algún índice `> len(filtered)` o `< 1`:
  - **Opción B1 (mínima):** eliminar/neutralizar la cita inválida del texto.
  - **Opción B2:** registrar métrica (contador de citas alucinadas) para observabilidad.
- Añadir test unitario con un `llm.generate.return_value` que contenga `[99]` y
  verificar que el resultado no expone la cita inválida.

### C. Reforzar cobertura de tests
- Test que fije un contexto de 5 fragmentos y una respuesta con índices fuera de
  rango, y afirme el comportamiento saneado (según A/B elegidos).
- Seguir convenciones de `backend/CLAUDE.md` (autospec de los Ports, fixtures,
  builders con intención, imports al top).

## Recomendación
Implementar **A + B (B1 y B2)**: acotar el rango en el prompt y, como red de
seguridad, sanear + medir en el caso de uso. A solo reduce la probabilidad; B
garantiza que una cita inválida nunca llega al usuario.

## Alcance / archivos afectados
- `backend/app/application/query_use_case.py` (prompt + saneamiento)
- `backend/tests/application/…` (tests nuevos)
- (Opcional) contador/log de citas alucinadas para observabilidad.

## Fuera de alcance
- El sesgo de retrieval (para "derechos fundamentales" apenas aparece un artículo
  constitucional) — tema aparte.
- La deduplicación de fuentes repetidas (misma sentencia en dos chunks) — se aborda
  por separado.
