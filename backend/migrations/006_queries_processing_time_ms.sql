-- Latencia de cada consulta, para medir p50/p95/p99 de POST /api/query en
-- producción (ver docs/latencia-p95.sql). Hasta ahora solo se logueaba
-- `elapsed_ms` en Railway, que no se puede agregar ni consultar después.
--
-- Es el mismo `processing_time_ms` que se devuelve al cliente (medido dentro
-- de QueryUseCase: embedding + Qdrant + LLM), redondeado a ms enteros. No
-- incluye red ni cola de uvicorn/Railway.
--
-- Nullable: las filas anteriores a esta migración no tienen el dato.
--
-- APLICAR ANTES de desplegar el backend que la usa: el adapter de Supabase
-- manda esta columna en cada insert y PostgREST rechaza columnas
-- desconocidas, así que sin ella se perderían todos los logs (y los links
-- de compartir de las consultas nuevas).

alter table public.queries
    add column if not exists processing_time_ms integer;
