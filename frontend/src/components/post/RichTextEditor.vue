<script setup>
import { ref, onMounted, onBeforeUnmount, watch } from 'vue'
import { useEditor, EditorContent } from '@tiptap/vue-3'
import StarterKit from '@tiptap/starter-kit'
import Image from '@tiptap/extension-image'
import Link from '@tiptap/extension-link'
import Table from '@tiptap/extension-table'
import TableRow from '@tiptap/extension-table-row'
import TableCell from '@tiptap/extension-table-cell'
import TableHeader from '@tiptap/extension-table-header'
import Placeholder from '@tiptap/extension-placeholder'
import Underline from '@tiptap/extension-underline'
import AppIcon from '../common/AppIcon.vue'

const props = defineProps({
  modelValue: { type: String, default: '' },
  placeholder: { type: String, default: '输入内容...' },
})
const emit = defineEmits(['update:modelValue'])

const editor = useEditor({
  content: props.modelValue,
  extensions: [
    StarterKit.configure({
      heading: { levels: [1, 2, 3] },
    }),
    Underline,
    Link.configure({ openOnClick: false }),
    Image.configure({ inline: true }),
    Table.configure({ resizable: true }),
    TableRow, TableCell, TableHeader,
    Placeholder.configure({ placeholder: props.placeholder }),
  ],
  onUpdate: () => {
    emit('update:modelValue', editor.value?.getHTML() || '')
  },
})

watch(() => props.modelValue, (val) => {
  if (editor.value && val !== editor.value.getHTML()) {
    editor.value.commands.setContent(val, false)
  }
})

onBeforeUnmount(() => {
  editor.value?.destroy()
})

function setLink() {
  const url = window.prompt('输入链接地址：')
  if (url) {
    editor.value?.chain().focus().setLink({ href: url }).run()
  }
}

function addImage() {
  const url = window.prompt('输入图片URL：')
  if (url) {
    editor.value?.chain().focus().setImage({ src: url }).run()
  }
}

function addTable() {
  editor.value?.chain().focus().insertTable({ rows: 3, cols: 3, withHeaderRow: true }).run()
}

defineExpose({ editor })
</script>

<template>
  <div class="rich-editor" @click="editor?.commands?.focus()">
    <!-- 工具栏 -->
    <div class="rich-editor__toolbar">
      <button type="button" class="toolbar-btn" :class="{ active: editor?.isActive('bold') }" @click="editor?.chain().focus().toggleBold().run()" title="加粗">
        <strong>B</strong>
      </button>
      <button type="button" class="toolbar-btn" :class="{ active: editor?.isActive('italic') }" @click="editor?.chain().focus().toggleItalic().run()" title="斜体">
        <em>I</em>
      </button>
      <button type="button" class="toolbar-btn" :class="{ active: editor?.isActive('underline') }" @click="editor?.chain().focus().toggleUnderline().run()" title="下划线">
        <u>U</u>
      </button>
      <span class="toolbar-divider" />

      <button type="button" class="toolbar-btn" :class="{ active: editor?.isActive('heading', { level: 1 }) }" @click="editor?.chain().focus().toggleHeading({ level: 1 }).run()" title="标题1">H1</button>
      <button type="button" class="toolbar-btn" :class="{ active: editor?.isActive('heading', { level: 2 }) }" @click="editor?.chain().focus().toggleHeading({ level: 2 }).run()" title="标题2">H2</button>
      <button type="button" class="toolbar-btn" :class="{ active: editor?.isActive('heading', { level: 3 }) }" @click="editor?.chain().focus().toggleHeading({ level: 3 }).run()" title="标题3">H3</button>
      <span class="toolbar-divider" />

      <button type="button" class="toolbar-btn" :class="{ active: editor?.isActive('bulletList') }" @click="editor?.chain().focus().toggleBulletList().run()" title="无序列表">•列表</button>
      <button type="button" class="toolbar-btn" :class="{ active: editor?.isActive('orderedList') }" @click="editor?.chain().focus().toggleOrderedList().run()" title="有序列表">1.列表</button>
      <button type="button" class="toolbar-btn" :class="{ active: editor?.isActive('blockquote') }" @click="editor?.chain().focus().toggleBlockquote().run()" title="引用">"</button>
      <span class="toolbar-divider" />

      <button type="button" class="toolbar-btn" @click="setLink" :class="{ active: editor?.isActive('link') }" title="插入链接">🔗</button>
      <button type="button" class="toolbar-btn" @click="addImage" title="插入图片">🖼</button>
      <button type="button" class="toolbar-btn" @click="addTable" title="插入表格">⊞</button>
    </div>

    <!-- 编辑器区域 -->
    <EditorContent :editor="editor" class="rich-editor__content" />
  </div>
</template>

<style scoped>
.rich-editor {
  border: 1px solid var(--color-border-input, #d1d5db);
  border-radius: var(--radius-lg, 8px);
  overflow: hidden;
  background: var(--color-bg-card, #fff);
}

.rich-editor__toolbar {
  display: flex;
  flex-wrap: wrap;
  gap: 2px;
  padding: 6px 8px;
  border-bottom: 1px solid var(--color-border-input, #d1d5db);
  background: var(--color-bg-subtle, #f9fafb);
}

.toolbar-btn {
  display: inline-flex;
  align-items: center;
  justify-content: center;
  min-width: 30px;
  height: 30px;
  padding: 0 6px;
  border: 1px solid transparent;
  border-radius: 4px;
  background: transparent;
  color: var(--color-text-secondary, #374151);
  font-size: 13px;
  cursor: pointer;
  transition: all 0.15s;
}

.toolbar-btn:hover {
  background: var(--color-bg-card, #e5e7eb);
  border-color: var(--color-border-input, #d1d5db);
}

.toolbar-btn.active {
  background: var(--color-primary, #3b82f6);
  color: #fff;
  border-color: var(--color-primary, #3b82f6);
}

.toolbar-divider {
  width: 1px;
  height: 22px;
  margin: 4px;
  background: var(--color-border-input, #d1d5db);
}

.rich-editor__content {
  padding: 12px 16px;
  min-height: 300px;
  cursor: text;
}

.rich-editor__content :deep(.ProseMirror) {
  outline: none;
  min-height: 300px;
  line-height: 1.7;
}

.rich-editor__content :deep(.ProseMirror p) {
  margin: 0 0 8px;
}

.rich-editor__content :deep(.ProseMirror h1) {
  font-size: 1.5em;
  font-weight: 700;
  margin: 16px 0 8px;
}

.rich-editor__content :deep(.ProseMirror h2) {
  font-size: 1.25em;
  font-weight: 600;
  margin: 14px 0 6px;
}

.rich-editor__content :deep(.ProseMirror h3) {
  font-size: 1.1em;
  font-weight: 600;
  margin: 12px 0 4px;
}

.rich-editor__content :deep(.ProseMirror ul),
.rich-editor__content :deep(.ProseMirror ol) {
  padding-left: 24px;
  margin: 8px 0;
}

.rich-editor__content :deep(.ProseMirror blockquote) {
  border-left: 3px solid var(--color-primary, #3b82f6);
  padding-left: 12px;
  color: var(--color-text-muted, #6b7280);
  margin: 8px 0;
}

.rich-editor__content :deep(.ProseMirror img) {
  max-width: 100%;
  height: auto;
  border-radius: 6px;
  margin: 8px 0;
}

.rich-editor__content :deep(.ProseMirror table) {
  width: 100%;
  border-collapse: collapse;
  margin: 12px 0;
  overflow: hidden;
}

.rich-editor__content :deep(.ProseMirror th),
.rich-editor__content :deep(.ProseMirror td) {
  border: 1px solid var(--color-border-input, #d1d5db);
  padding: 8px 12px;
  text-align: left;
  min-width: 60px;
}

.rich-editor__content :deep(.ProseMirror th) {
  background: var(--color-bg-subtle, #f3f4f6);
  font-weight: 600;
}

.rich-editor__content :deep(.ProseMirror p.is-editor-empty:first-child::before) {
  content: attr(data-placeholder);
  color: var(--color-text-muted, #9ca3af);
  pointer-events: none;
  float: left;
  height: 0;
}

.rich-editor__content :deep(.ProseMirror a) {
  color: var(--color-primary, #3b82f6);
  text-decoration: underline;
  cursor: pointer;
}

.rich-editor__content :deep(.ProseMirror code) {
  background: #f3f4f6;
  border-radius: 3px;
  padding: 2px 4px;
  font-size: 0.9em;
}
</style>
