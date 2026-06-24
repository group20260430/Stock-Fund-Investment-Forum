/** 格式化相对时间（如 "3小时前"） */
export function timeAgo(dateStr) {
  if (!dateStr) return ''
  const now = Date.now()
  const date = parseBackendTime(dateStr)
  if (Number.isNaN(date)) return ''
  const diff = now - date

  const seconds = Math.floor(diff / 1000)
  if (seconds < 60) return '刚刚'

  const minutes = Math.floor(seconds / 60)
  if (minutes < 60) return `${minutes}分钟前`

  const hours = Math.floor(minutes / 60)
  if (hours < 24) return `${hours}小时前`

  const days = Math.floor(hours / 24)
  if (days < 30) return `${days}天前`

  const months = Math.floor(days / 30)
  if (months < 12) return `${months}个月前`

  return `${Math.floor(months / 12)}年前`
}

function parseBackendTime(value) {
  if (value instanceof Date) return value.getTime()
  if (typeof value !== 'string') return new Date(value).getTime()

  const normalized = value.trim()
  const hasTimezone = /(?:Z|[+-]\d{2}:?\d{2})$/i.test(normalized)
  const looksLikeDateTime = /^\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}/.test(normalized)

  // FastAPI + SQLite returns UTC timestamps without timezone suffix.
  // Tell the browser they are UTC so "刚发布" doesn't become "8小时前".
  return new Date(!hasTimezone && looksLikeDateTime ? `${normalized}Z` : normalized).getTime()
}

/** 格式化数字（超过1万显示为 x.x万） */
export function formatCount(num) {
  if (num >= 10000) {
    return (num / 10000).toFixed(1) + '万'
  }
  return String(num)
}

/** 截断文字 */
export function truncate(str, maxLen = 100) {
  if (!str) return ''
  return str.length > maxLen ? str.slice(0, maxLen) + '...' : str
}
