import React from 'react'

interface ReactMarkdownProps {
  children: string
  components?: Record<string, any>
}

export default function ReactMarkdown({ children, components }: ReactMarkdownProps) {
  // Simple mock that renders markdown as HTML for testing
  const processMarkdown = (text: string) => {
    let processed = text

    // Bold: **text** -> <strong>text</strong>
    processed = processed.replace(/\*\*(.*?)\*\*/g, '<strong>$1</strong>')

    // Italic: *text* -> <em>text</em>
    processed = processed.replace(/\*(.*?)\*/g, '<em>$1</em>')

    return processed
  }

  const html = processMarkdown(children)

  return <div dangerouslySetInnerHTML={{ __html: html }} />
}
