import { metadata } from '../layout'

const CORPUS = [
  /constituci[oó]n/i,
  /corte constitucional/i,
  /c[oó]digo penal/i,
  /c[oó]digo sustantivo del trabajo/i,
  /c[oó]digo civil/i,
]

const descriptions = Object.entries({
  description: metadata.description,
  'openGraph.description': metadata.openGraph?.description,
  'twitter.description': metadata.twitter?.description,
})

describe('metadata del sitio', () => {
  it.each(descriptions)('%s menciona todo el corpus real', (_, text) => {
    for (const pattern of CORPUS) {
      expect(text).toMatch(pattern)
    }
  })

  it.each(descriptions)('%s cabe en 160 caracteres', (_, text) => {
    expect((text as string).length).toBeLessThanOrEqual(160)
  })
})
