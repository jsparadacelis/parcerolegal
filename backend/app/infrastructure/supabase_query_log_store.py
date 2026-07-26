"""Supabase adapter para QueryLogStore — INSERT vía REST (PostgREST).

Habla el REST de Supabase con `requests` directo (misma dependencia HTTP que el
resto de adapters). Best-effort: `save` traga cualquier error y lo loguea, nunca
propaga — persistir el log de una consulta jamás debe romper la respuesta al
usuario. El no-bloqueo (fire-and-forget) se compone en una capa aparte.
"""

from __future__ import annotations

import dataclasses
import logging

import requests

from backend.app.domain.entities import QueryLog

logger = logging.getLogger("parcerolegal")


class SupabaseQueryLogStore:
    def __init__(self, url: str, api_key: str, table: str = "queries") -> None:
        self._insert_url = f"{url.rstrip('/')}/rest/v1/{table}"
        self._headers = {
            "apikey": api_key,
            "Authorization": f"Bearer {api_key}",
            "Content-Type": "application/json",
            "Prefer": "return=minimal",
        }

    def save(self, log: QueryLog) -> None:
        try:
            response = requests.post(
                self._insert_url,
                json=dataclasses.asdict(log),
                headers=self._headers,
                timeout=5,
            )
            response.raise_for_status()
        except Exception:  # noqa: BLE001 — best-effort, no debe afectar la consulta
            logger.warning(
                "no se pudo guardar el log de la consulta en Supabase",
                exc_info=True,
            )
