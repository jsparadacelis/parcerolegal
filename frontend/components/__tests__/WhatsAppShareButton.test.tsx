import { render, screen } from '@testing-library/react'
import { WhatsAppShareButton, buildWhatsAppUrl } from '../WhatsAppShareButton'

describe('buildWhatsAppUrl', () => {
  it('builds a wa.me link with the encoded text and share link', () => {
    const url = buildWhatsAppUrl('https://parcerolegal.co', 'abc123')

    expect(url.startsWith('https://wa.me/?text=')).toBe(true)
    const text = decodeURIComponent(url.slice('https://wa.me/?text='.length))
    expect(text).toMatch(/parcerolegal/i)
    expect(text.endsWith('https://parcerolegal.co/s/abc123')).toBe(true)
  })

  it('percent-encodes the whole text so spaces and the link survive', () => {
    const url = buildWhatsAppUrl('https://parcerolegal.co', 'a b&c')

    expect(url).not.toContain(' ')
    expect(url).toContain(encodeURIComponent('https://parcerolegal.co/s/a b&c'))
  })
})

describe('WhatsAppShareButton', () => {
  it('renders a link to WhatsApp built from the share token', () => {
    render(<WhatsAppShareButton shareToken="abc123" />)

    const link = screen.getByRole('link', { name: /compartir por whatsapp/i })
    expect(link).toHaveAttribute('href', buildWhatsAppUrl(location.origin, 'abc123'))
  })

  it('opens in a new tab without leaking the opener', () => {
    render(<WhatsAppShareButton shareToken="abc123" />)

    const link = screen.getByRole('link', { name: /compartir por whatsapp/i })
    expect(link).toHaveAttribute('target', '_blank')
    expect(link).toHaveAttribute('rel', 'noopener noreferrer')
  })

  it('renders nothing without a share token', () => {
    const { container } = render(<WhatsAppShareButton shareToken="" />)

    expect(container).toBeEmptyDOMElement()
    expect(screen.queryByRole('link')).not.toBeInTheDocument()
  })
})
