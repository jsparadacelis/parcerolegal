-- Percentiles de latencia de POST /api/query (últimos 7 días).
-- Pegar en el SQL editor de Supabase. Requiere la migración
-- backend/migrations/006_queries_processing_time_ms.sql.
--
-- `processing_time_ms` es la latencia medida en el backend (embedding + Qdrant
-- + LLM); no incluye red ni cola de Railway. Las respuestas fuera de alcance
-- no llaman al LLM, por eso se separan: mezcladas bajarían el p95 real.
--
-- Para excluir corridas de load test (backend/scripts/load_test.py), añade al WHERE
-- los rangos que reporte cada corrida, p. ej.:
--   and created_at not between '2026-09-27 15:00:00+00' and '2026-09-27 15:10:00+00'

select
    case
        when grouping(out_of_scope) = 1 then 'total'
        when out_of_scope then 'fuera de alcance'
        else 'en alcance'
    end                                                                   as tipo,
    count(*)                                                              as consultas,
    round(percentile_cont(0.50) within group (order by processing_time_ms)) as p50_ms,
    round(percentile_cont(0.95) within group (order by processing_time_ms)) as p95_ms,
    round(percentile_cont(0.99) within group (order by processing_time_ms)) as p99_ms,
    max(processing_time_ms)                                               as max_ms
from public.queries
where created_at >= now() - interval '7 days'
  and processing_time_ms is not null
group by rollup (out_of_scope)
order by out_of_scope nulls last;
