-- Preguntas fuera de alcance (bajo el umbral de similitud).
-- Persistidas best-effort (fire-and-forget) para analizar vacíos del corpus.
--
-- El backend inserta con la SERVICE ROLE key (server-side), que bypassa RLS.
-- Dejamos RLS habilitado sin políticas públicas: ningún cliente anónimo puede
-- leer ni escribir esta tabla.

create table if not exists public.missed_queries (
    id            bigint generated always as identity primary key,
    question      text        not null,
    answer        text        not null,
    top_score     real,                      -- mayor similitud recuperada; null si no hubo chunks
    detected_area text,                      -- área del derecho detectada por heurística; null si desconocida
    created_at    timestamptz not null default now()
);

-- Consultas típicas de análisis: por fecha y por área.
create index if not exists missed_queries_created_at_idx
    on public.missed_queries (created_at desc);
create index if not exists missed_queries_detected_area_idx
    on public.missed_queries (detected_area);

alter table public.missed_queries enable row level security;
