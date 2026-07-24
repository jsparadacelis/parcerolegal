-- Respuestas compartibles por link público (feature "Compartir").
--
-- A diferencia de missed_queries (analítica interna, nunca leída por un
-- cliente), esta tabla respalda contenido que SÍ se sirve públicamente vía
-- GET /api/shares/{id}. El `id` es un token corto url-safe generado por el
-- backend (no correlativo, para no permitir enumerar los shares existentes).
--
-- El backend inserta y lee con la SERVICE ROLE key (server-side), que
-- bypassa RLS. Dejamos RLS habilitado sin políticas públicas: el cliente
-- (frontend) nunca habla directo con Supabase, siempre pasa por la API, que
-- decide qué exponer.

create table if not exists public.shared_answers (
    id            text        primary key,
    question      text        not null,
    answer        text        not null,
    sources       jsonb       not null default '[]'::jsonb,
    out_of_scope  boolean     not null,
    created_at    timestamptz not null default now()
);

create index if not exists shared_answers_created_at_idx
    on public.shared_answers (created_at desc);

alter table public.shared_answers enable row level security;
