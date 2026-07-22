-- A partir de ahora se persisten TODAS las consultas respondidas (no solo las
-- que caían bajo el umbral de similitud), para analizar también respuestas en
-- alcance. `out_of_scope` distingue unas de otras.
--
-- Default true en el backfill: las filas existentes en esta tabla son, todas,
-- consultas que sí cayeron bajo el umbral (era la única razón por la que se
-- guardaban antes de este cambio).

alter table public.missed_queries
    add column if not exists out_of_scope boolean not null default true;

alter table public.missed_queries
    alter column out_of_scope drop default;

create index if not exists missed_queries_out_of_scope_idx
    on public.missed_queries (out_of_scope);
