"""Supabase adapter para QueryLogStore/QueryLogFinder — REST directo (PostgREST).

Habla el REST de Supabase con `requests` directo (misma dependencia HTTP que el
resto de adapters). Un único adapter concreto respalda los dos ports:
- `save` es best-effort (traga cualquier error y lo loguea, nunca propaga —
  persistir el log de una consulta jamás debe romper la respuesta al usuario;
  el no-bloqueo fire-and-forget se compone en una capa aparte).
- `find_by_share_token` SÍ propaga errores: un link compartible que falla en
  silencio es peor que un error visible a quien intenta abrirlo.
"""

from __future__ import annotations

import dataclasses
import logging

import requests

from backend.app.domain.entities import QueryLog, Source

logger = logging.getLogger("parcerolegal")


class SupabaseQueryLogStore:
    def __init__(self, url: str, api_key: str, table: str = "queries") -> None:
        self._table_url = f"{url.rstrip('/')}/rest/v1/{table}"
        self._headers = {"apikey": api_key, "Authorization": f"Bearer {api_key}"}

    def save(self, log: QueryLog) -> None:
        try:
            response = requests.post(
                self._table_url,
                json=dataclasses.asdict(log),
                headers={
                    **self._headers,
                    "Content-Type": "application/json",
                    "Prefer": "return=minimal",
                },
                timeout=5,
            )
            response.raise_for_status()
        except Exception:  # noqa: BLE001 — best-effort, no debe afectar la consulta
            logger.warning(
                "no se pudo guardar el log de la consulta en Supabase",
                exc_info=True,
            )

    def find_by_share_token(self, share_token: str) -> QueryLog | None:
        response = requests.get(
            self._table_url,
            headers=self._headers,
            params={"share_token": f"eq.{share_token}", "select": "*", "limit": 1},
            timeout=5,
        )
        response.raise_for_status()
        rows = response.json()
        if not rows:
            return None
        return _row_to_query_log(rows[0])


def _row_to_query_log(row: dict) -> QueryLog:
    return QueryLog(
        question=row["question"],
        answer=row["answer"],
        sources=[Source(**s) for s in row["sources"]],
        top_score=row["top_score"],
        detected_area=row["detected_area"],
        out_of_scope=row["out_of_scope"],
        share_token=row["share_token"],
    )
