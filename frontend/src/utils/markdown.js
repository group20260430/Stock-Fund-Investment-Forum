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
