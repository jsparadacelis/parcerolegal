'use client'

import { useState } from 'react'
import { Share2, Check, AlertCircle } from 'lucide-react'

interface ShareButtonProps {
  /** share_token que ya vino en la respuesta de /api/query — compartir no
   * hace ninguna llamada de red, solo arma el link y lo copia. */
  shareToken: string
}

export function ShareButton({ shareToken }: ShareButtonProps) {
  const [status, setStatus] = useState<'idle' | 'copied' | 'error'>('idle')

  const handleShare = async () => {
    try {
      await navigator.clipboard.writeText(`${location.origin}/s/${shareToken}`)
      setStatus('copied')
    } catch {
      setStatus('error')
    } finally {
      setTimeout(() => setStatus('idle'), 2000)
    }
  }

  return (
    <div className="relative">
      <button
        onClick={handleShare}
        className="flex items-center gap-1.5 rounded-lg px-2.5 py-[7px] text-[13px] font-medium text-primary hover:bg-surface-2 transition-colors"
      >
        <Share2 className="w-[15px] h-[15px]" />
        Compartir
      </button>
      {status !== 'idle' && (
        <div className="absolute -top-10 left-1/2 -translate-x-1/2 flex items-center gap-1.5 bg-ink text-white text-xs font-semibold px-3 py-[7px] rounded-lg whitespace-nowrap shadow-lg">
          {status === 'copied' ? (
            <>
              <Check className="w-[13px] h-[13px] text-emerald-400" />
              Link copiado
            </>
          ) : (
            <>
              <AlertCircle className="w-[13px] h-[13px] text-red-400" />
              No se pudo compartir
            </>
          )}
          <span className="absolute -bottom-1 left-1/2 -translate-x-1/2 w-2 h-2 bg-ink rotate-45" />
        </div>
      )}
    </div>
  )
}
