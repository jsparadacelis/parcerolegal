-- Compartir deja de volver a llamar al RAG: en vez de regenerar la
-- respuesta y guardarla aparte (shared_answers, ver 003), ahora el share
-- apunta directo al registro que QueryUseCase ya guarda en `queries` para
-- CADA consulta respondida (ver 004). share_token se genera en el momento
-- de responder (no correlativo, no adivinable) y es lo que se expone en
-- GET /api/shares/{share_token}.

alter table public.queries
    add column if not exists share_token text;

create unique index if not exists queries_share_token_idx
    on public.queries (share_token)
    where share_token is not null;

-- shared_answers ya no se usa: todo lo que guardaba ahora vive en `queries`.
drop table if exists public.shared_answers;
