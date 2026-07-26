-- missed_queries pasa a llamarse queries: ya no es solo "preguntas fuera de
-- alcance" (ver 002_missed_queries_out_of_scope.sql), sino el log de TODAS
-- las consultas respondidas. El nombre viejo quedó desalineado con lo que la
-- tabla realmente guarda hace rato; este cambio solo alinea nombre y realidad.
--
-- De paso se agrega `sources`: hasta ahora se guardaba el texto de la
-- respuesta pero no de qué artículos/sentencias salió, lo que hacía
-- imposible auditar citas o ver qué partes del corpus se usan de verdad.

alter table public.missed_queries rename to queries;

alter table public.queries
    add column if not exists sources jsonb not null default '[]'::jsonb;

alter index if exists missed_queries_pkey rename to queries_pkey;
alter index if exists missed_queries_created_at_idx rename to queries_created_at_idx;
alter index if exists missed_queries_detected_area_idx rename to queries_detected_area_idx;
alter index if exists missed_queries_out_of_scope_idx rename to queries_out_of_scope_idx;
