/**
 * 编辑器文本操作工具
 */

/**
 * 获取 textarea 的选中文本及光标位置
 * @param {HTMLTextAreaElement} el
 * @returns {{ start: number, end: number, text: string }}
 */
export function getTextareaSelection(el) {
  return {
    start: el.selectionStart,
    end: el.selectionEnd,
    text: el.value.substring(el.selectionStart, el.selectionEnd),
  }
}

/**
 * 在 textarea 光标处插入文本，支持包裹选中文本
 * 同时更新 textarea 的 value 和光标位置
 *
 * @param {HTMLTextAreaElement} el - textarea DOM 元素
 * @param {string} before - 插入在选中文本前的内容
 * @param {string} [after] - 插入在选中文本后的内容（默认与 before 相同）
 * @param {string} [placeholder='文本'] - 未选中文本时的占位内容
 */
export function insertAtCursor(el, before, after, placeholder = '文本') {
  if (!el) return

  const { start, end, text } = getTextareaSelection(el)
  const hasSelection = start !== end

  after = after ?? before

  const inserted = hasSelection ? before + text + after : before + placeholder + after
  const cursorOffset = hasSelection
    ? before.length + text.length + after.length
    : before.length + placeholder.length

  // 用 InputEvent 触发 v-model 更新
  // 先直接修改原生 value，再 dispatch input 事件让 Vue 感知
  const nativeSetter = Object.getOwnPropertyDescriptor(
    window.HTMLTextAreaElement.prototype,
    'value',
  ).set
  nativeSetter.call(el, el.value.substring(0, start) + inserted + el.value.substring(end))

  el.dispatchEvent(new Event('input', { bubbles: true }))

  // 将光标放在插入内容之后
  const newPos = start + cursorOffset
  el.setSelectionRange(newPos, newPos)
  el.focus()
}

/**
 * 在行首插入前缀（用于列表等）
 * @param {HTMLTextAreaElement} el
 * @param {string} prefix - 行首前缀
 * @param {string} [placeholder='列表项'] - 占位文本
 */
export function insertAtLineStart(el, prefix, placeholder = '列表项') {
  if (!el) return

  const { start } = getTextareaSelection(el)
  const value = el.value

  // 找到当前行的起始位置
  const lineStart = value.lastIndexOf('\n', start - 1) + 1
  const indent = value.substring(lineStart, start).match(/^(\s*)/)?.[0] || ''

  const inserted = indent + prefix + ' ' + placeholder + '\n'

  const nativeSetter = Object.getOwnPropertyDescriptor(
    window.HTMLTextAreaElement.prototype,
    'value',
  ).set
  nativeSetter.call(
    el,
    value.substring(0, lineStart) + inserted + value.substring(start),
  )

  el.dispatchEvent(new Event('input', { bubbles: true }))

  // 光标放在占位文本中间，方便用户直接输入
  const newPos = lineStart + indent.length + prefix.length + 1
  el.setSelectionRange(newPos, newPos + placeholder.length)
  el.focus()
}
