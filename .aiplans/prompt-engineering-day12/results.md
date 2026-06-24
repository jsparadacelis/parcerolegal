# Resultados — 20 queries de prueba (2026-06-24, post-migración Jina)

## Dentro de alcance (15)

| Query | Veredicto | Notas |
|---|---|---|
| ¿Qué es el derecho a la salud en Colombia? | ✅ | Cita T-760-08, C-239-97 correctamente |
| ¿Qué es el habeas corpus? | ✅ | Cita Art. 30 |
| ¿Cuáles son los derechos fundamentales según la Constitución? | ✅ | Lista correcta, cita C-239-97, T-760-08, T-398-19 |
| ¿Qué dice la sentencia T-760 de 2008? | ❌ | **out_of_scope falso positivo** — scores 0.36-0.40, todos bajo el umbral 0.45, ninguno de T-760-08 |
| ¿Qué establece la sentencia C-355 de 2006 sobre el aborto? | ✅ | Cita C-355-06 x5, contenido correcto |
| ¿Qué protege la acción de tutela? | ✅ | Cita Art. 86, T-406-92, SU-214-16 |
| ¿Cuáles son los deberes de los ciudadanos colombianos? | ✅ | Cita Art. 95 correctamente |
| ¿Qué dice el artículo 1 de la Constitución sobre el Estado colombiano? | ✅ | Cita Art. 1 correctamente |
| ¿Qué establece la Constitución sobre el derecho a la igualdad? | ✅ | Cita Art. 13, Art. 43, C-355-06 |
| ¿Qué es el debido proceso según la Constitución? | ✅ | Cita Art. 29 |
| ¿Qué dice la sentencia SU-214 de 2016? | ⚠️ | Retrieval trae T-398-19 (sentencia equivocada); el LLM NO alucina, dice "no disponible" — comportamiento seguro pero UX pobre |
| ¿Qué establece la sentencia T-025 de 2004 sobre desplazamiento forzado? | ✅ | Cita T-025-04 x5, contenido correcto |
| ¿Cuáles son las ramas del poder público en Colombia? | ✅ | Cita Art. 113 correctamente |
| ¿Qué derechos tienen los niños según la Constitución colombiana? | ✅ | Cita Art. 44 correctamente |
| ¿Qué dice la Constitución sobre la libertad de culto? | ✅ | Cita Art. 19 |

## Fuera de alcance (5)

| Query | Veredicto |
|---|---|
| ¿Cuál es la receta para hacer arepas? | ✅ out_of_scope correcto |
| ¿Quién ganó el mundial de fútbol de 2022? | ✅ out_of_scope correcto |
| ¿Cómo configuro un servidor de Python? | ✅ out_of_scope correcto |
| ¿Cuál es la capital de Francia? | ✅ out_of_scope correcto |
| asdkjaslkdj (gibberish) | ✅ out_of_scope correcto |

## Conclusión

- **System prompt**: funciona bien, 0 alucinaciones, formato de citas correcto, tono adecuado.
  No requiere cambios en esta iteración.
- **Out-of-scope detection**: 5/5 correctos para queries claramente irrelevantes.
- **Gap real encontrado**: queries que nombran una sentencia directamente
  ("¿qué dice la sentencia X de YYYY?") tienen mal retrieval porque el embedding de la
  pregunta captura la referencia/cita, no el contenido legal — no se parece semánticamente
  al texto de los chunks. Esto es un problema de **retrieval**, no de prompt.
  - Causa raíz: búsqueda puramente semántica (vector) sin filtro por metadata.
  - Fix recomendado (no implementado en esta iteración): detectar patrones de cita
    (regex tipo `T-760`, `C-355`, `SU-214`) en la pregunta y usar un filtro de payload en
    Qdrant (`sentencia_id` exacto) además de o en lugar de la búsqueda vectorial pura.
  - Queda documentado como tarea de seguimiento — ver `implementation_log.md`.
