export function formatDate(value) {
  if (!value) return '—'
  const date = new Date(value)
  if (Number.isNaN(date.getTime())) return String(value)
  return date.toLocaleString('ru-RU', {
    year: 'numeric',
    month: 'short',
    day: 'numeric',
    hour: '2-digit',
    minute: '2-digit',
  })
}

export function extractNewsPreview(content) {
  if (!content) return ''
  if (typeof content === 'string') return content
  if (typeof content.lead === 'string') return content.lead
  if (typeof content.text === 'string') return content.text
  if (typeof content.body === 'string') return content.body
  if (Array.isArray(content.sections) && content.sections.length > 0) {
    const first = content.sections[0]
    return first.body || first.heading || JSON.stringify(content)
  }
  return JSON.stringify(content)
}
