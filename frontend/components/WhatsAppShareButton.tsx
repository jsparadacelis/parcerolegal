'use client'

import { MessageCircle } from 'lucide-react'

const SHARE_TEXT = 'Mira esta respuesta de parcerolegal sobre la ley colombiana:'

/** Arma el link de wa.me con el texto y el link `/s/{token}` ya codificados. */
export function buildWhatsAppUrl(origin: string, shareToken: string): string {
  const text = `${SHARE_TEXT} ${origin}/s/${shareToken}`
  return `https://wa.me/?text=${encodeURIComponent(text)}`
}

interface WhatsAppShareButtonProps {
  /** share_token de la respuesta; sin token no hay nada que compartir. */
  shareToken: string
}

export function WhatsAppShareButton({ shareToken }: WhatsAppShareButtonProps) {
  if (!shareToken) return null

  return (
    <a
      href={buildWhatsAppUrl(location.origin, shareToken)}
      target="_blank"
      rel="noopener noreferrer"
      aria-label="Compartir por WhatsApp (se abre en una pestaña nueva)"
      className="flex items-center gap-1.5 rounded-lg px-2.5 py-[7px] text-[13px] font-medium text-primary hover:bg-surface-2 transition-colors focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-primary focus-visible:ring-offset-2"
    >
      <MessageCircle className="w-[15px] h-[15px]" aria-hidden="true" />
      WhatsApp
    </a>
  )
}
