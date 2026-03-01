export type SourceType = 'constitución' | 'sentencia'

export interface Source {
  title: string
  type: SourceType
  excerpt: string
  similarity: number
}

export interface QueryResponse {
  answer: string
  sources: Source[]
  processing_time_ms?: number
}
