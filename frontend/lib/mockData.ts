import type { QueryResponse } from './types'

export const EXAMPLE_QUERY = '¿Puedo grabar una llamada sin permiso de la otra persona?'

export const MOCK_RESPONSE: QueryResponse = {
  answer: `Según el **Artículo 15** de la Constitución Política de Colombia, todas las personas tienen derecho a su intimidad personal y familiar, y a su buen nombre. Solo mediante orden judicial se pueden interceptar comunicaciones privadas.

La jurisprudencia establecida en la **Sentencia T-881/2002** de la Corte Constitucional aclaró que grabar una conversación privada sin el consentimiento de todas las partes vulnera el derecho a la intimidad y está prohibido.

**Conclusión**: No está permitido grabar llamadas sin el consentimiento explícito de todas las personas involucradas, salvo que exista una orden judicial que lo autorice.`,
  sources: [
    {
      title: 'Constitución Política de Colombia - Artículo 15',
      type: 'constitución',
      excerpt:
        'Todas las personas tienen derecho a su intimidad personal y familiar y a su buen nombre, y el Estado debe respetarlos y hacerlos respetar. De igual modo, tienen derecho a conocer, actualizar y rectificar las informaciones que se hayan recogido sobre ellas en bancos de datos y en archivos de entidades públicas y privadas.',
      similarity: 0.89,
    },
    {
      title: 'Sentencia T-881/2002 - Corte Constitucional',
      type: 'sentencia',
      excerpt:
        'La grabación de conversaciones privadas sin el consentimiento de los interlocutores constituye una vulneración del derecho fundamental a la intimidad consagrado en el artículo 15 de la Constitución Política.',
      similarity: 0.85,
    },
    {
      title: 'Constitución Política de Colombia - Artículo 74',
      type: 'constitución',
      excerpt:
        'Todas las personas tienen derecho a acceder a los documentos públicos salvo los casos que establezca la ley. El secreto profesional es inviolable.',
      similarity: 0.72,
    },
  ],
  processing_time_ms: 1423,
}

export function simulateQuery(_query: string): Promise<QueryResponse> {
  return new Promise((resolve) => {
    setTimeout(() => {
      resolve(MOCK_RESPONSE)
    }, 1500)
  })
}
