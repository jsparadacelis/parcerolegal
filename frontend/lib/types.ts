// Debe reflejar los SOURCE_TYPE_* del backend (backend/app/domain/entities.py).
// Al agregar un corpus nuevo, añadirlo aquí y en SOURCE_META (SourceCard.tsx).
export type SourceType =
  | 'constitucion'
  | 'sentencia'
  | 'codigo_penal'
  | 'codigo_sustantivo_trabajo'

export interface Source {
  chunk_id: string
  source_type: SourceType
  title: string
  url: string
}

export interface QueryResponse {
  answer: string
  sources: Source[]
  out_of_scope: boolean
  processing_time_ms: number
  share_token: string
}

export interface SharedQuery {
  question: string
  answer: string
  sources: Source[]
  out_of_scope: boolean
}
