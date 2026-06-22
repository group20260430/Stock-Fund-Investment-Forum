/**
 * Markdown 渲染工具 — marked + DOMPurify
 */
import { marked } from 'marked'
import DOMPurify from 'dompurify'

// 配置 marked
marked.setOptions({
  gfm: true,          // GitHub Flavored Markdown（表格、任务列表等）
  breaks: true,       // 换行符转 <br>
})

// 自定义渲染：链接在新窗口打开
const defaultRenderer = new marked.Renderer()
defaultRenderer.link = function ({ href, title, text }) {
  const titleAttr = title ? ` title="${title}"` : ''
  return `<a href="${href}"${titleAttr} target="_blank" rel="noopener noreferrer">${text}</a>`
}
marked.use({ renderer: defaultRenderer })

/**
 * 将 Markdown 字符串渲染为安全的 HTML
 * @param {string} raw - 原始 Markdown 文本
 * @returns {string} 安全清洗后的 HTML
 */
export function renderMarkdown(raw) {
  if (!raw) return ''
  const html = marked.parse(raw)
  return DOMPurify.sanitize(html)
}

/**
 * 从 Markdown / HTML 内容中提取前 N 张图片的 URL
 * @param {string} content - 原始内容（Markdown 或 HTML）
 * @param {number} [limit=4] - 最多提取几张
 * @returns {{ urls: string[], total: number }} 图片 URL 数组和总数
 */
export function extractImages(content, limit = 4) {
  if (!content) return { urls: [], total: 0 }

  // 先渲染为 HTML，方便统一用 DOM 解析
  const html = renderMarkdown(content)
  if (!html) return { urls: [], total: 0 }

  // 用 DOMParser 解析 HTML 并提取 img 标签
  const parser = new DOMParser()
  const doc = parser.parseFromString(html, 'text/html')
  const imgs = doc.querySelectorAll('img')
  const allUrls = Array.from(imgs).map(img => img.getAttribute('src')).filter(Boolean)

  return {
    urls: allUrls.slice(0, limit),
    total: allUrls.length,
  }
}
