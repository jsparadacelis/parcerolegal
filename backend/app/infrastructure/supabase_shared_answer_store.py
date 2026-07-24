"""Supabase adapter para SharedAnswerStore — REST directo (PostgREST).

A diferencia de SupabaseMissedQueryStore, NO es best-effort: save/get
propagan cualquier error de red o HTTP. Un share es contenido público que el
usuario espera poder abrir; tragar el error en silencio dejaría un link roto
sin que nadie se entere.
"""

from __future__ import annotations

import dataclasses

import requests

from backend.app.domain.entities import SharedAnswer, Source


class SupabaseSharedAnswerStore:
    def __init__(self, url: str, api_key: str, table: str = "shared_answers") -> None:
        self._table_url = f"{url.rstrip('/')}/rest/v1/{table}"
        self._headers = {"apikey": api_key, "Authorization": f"Bearer {api_key}"}

    def save(self, shared: SharedAnswer) -> None:
        response = requests.post(
            self._table_url,
            json=dataclasses.asdict(shared),
            headers={
                **self._headers,
                "Content-Type": "application/json",
                "Prefer": "return=minimal",
            },
            timeout=5,
        )
        response.raise_for_status()

    def get(self, share_id: str) -> SharedAnswer | None:
        response = requests.get(
            self._table_url,
            headers=self._headers,
            params={"id": f"eq.{share_id}", "select": "*", "limit": 1},
            timeout=5,
        )
        response.raise_for_status()
        rows = response.json()
        if not rows:
            return None
        return _row_to_shared_answer(rows[0])


def _row_to_shared_answer(row: dict) -> SharedAnswer:
    return SharedAnswer(
        id=row["id"],
        question=row["question"],
        answer=row["answer"],
        sources=[Source(**s) for s in row["sources"]],
        out_of_scope=row["out_of_scope"],
    )
