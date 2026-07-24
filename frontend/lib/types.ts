export type SourceType = 'constitucion' | 'sentencia'

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
}

export interface SharedQuery {
  question: string
  answer: string
  sources: Source[]
  out_of_scope: boolean
}
