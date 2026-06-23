<script setup>
import { ref, reactive, computed, onMounted } from 'vue'
import { useToastStore } from '../../stores/toast'
import { createPost, updatePost, fetchCategories } from '../../api/posts'
import { renderMarkdown } from '../../utils/markdown'
import { insertAtCursor, insertAtLineStart } from '../../utils/editor'
import AppIcon from '../common/AppIcon.vue'
import RichTextEditor from './RichTextEditor.vue'

const props = defineProps({
  post: { type: Object, default: null },
})

const emit = defineEmits(['close', 'saved'])
const toast = useToastStore()

const submitting = ref(false)
const categories = ref([])
const tagInput = ref('')
const textareaRef = ref(null)
const fileInputRef = ref(null)
const imageInputRef = ref(null)
const uploading = ref(false)
const uploadingImage = ref(false)

const form = reactive({
  category_id: '',
  title: '',
  content: '',
  post_type: 'normal',
  tags: [],
  vote_options: [],
  attachments: [],
})

const voteOptionInputs = ref(['', ''])

const previewHtml = computed(() => renderMarkdown(form.content))
const richTextMode = computed(() => form.post_type === 'long_article')

onMounted(async () => {
  try {
    categories.value = await fetchCategories()
    if (categories.value.length) form.category_id = categories.value[0].id
  } catch { /* ignore */ }
  if (props.post) {
    form.category_id = props.post.category_id || props.post.category?.id || ''
    form.title = props.post.title || ''
    form.content = props.post.content || ''
    form.post_type = props.post.post_type || 'normal'
    form.tags = props.post.tags || []
    form.attachments = (props.post.attachments || []).map(a => ({
      file_name: a.file_name,
      file_url: a.file_url,
      file_size: a.file_size || 0,
      file_type: a.file_type || '',
    }))
    if (props.post.poll?.options) {
      voteOptionInputs.value = props.post.poll.options.map(o => o.text || o.label || '')
      form.vote_options = props.post.poll.options.map(o => ({ label: o.text || o.label || '' }))
    } else if (props.post.vote_options) {
      voteOptionInputs.value = props.post.vote_options.map(o => o.label || '')
      form.vote_options = props.post.vote_options.map(o => ({ label: o.label }))
    }
  }
})

// ========== 通用上传 ==========
async function uploadSingleFile(file) {
  const formData = new FormData()
  formData.append('file', file)

  const token = localStorage.getItem('token')
  const API_BASE = import.meta.env.VITE_API_BASE_URL || 'http://localhost:8000/api'
  const response = await fetch(`${API_BASE}/uploads`, {
    method: 'POST',
    headers: token ? { Authorization: `Bearer ${token}` } : {},
    body: formData,
  })

  if (!response.ok) {
    const err = await response.json().catch(() => ({}))
    throw new Error(err.message || `上传失败 (${response.status})`)
  }

  const result = await response.json()
  return result.data
}

// ========== 工具栏操作 ==========
const textarea = () => textareaRef.value

function insertBold()      { insertAtCursor(textarea(), '**', '**', '加粗文本') }
function insertItalic()    { insertAtCursor(textarea(), '*', '*', '斜体文本') }
function insertUnderline() { insertAtCursor(textarea(), '<u>', '</u>', '下划线文本') }
function insertUl()        { insertAtLineStart(textarea(), '-', '列表项') }
function insertOl()        { insertAtLineStart(textarea(), '1.', '列表项') }

function insertLink() {
  const url = prompt('请输入链接 URL：', 'https://')
  if (url) insertAtCursor(textarea(), '[', `](${url})`, '链接文本')
}

// ========== 图片上传并插入 ==========
function triggerImageInput() {
  imageInputRef.value?.click()
}

async function handleImageSelected(e) {
  const files = e.target.files
  if (!files || !files.length) return

  const file = files[0]

  // 校验
  if (!file.type.startsWith('image/')) {
    toast.warning('请选择图片文件')
    e.target.value = ''
    return
  }
  if (file.size > 10 * 1024 * 1024) {
    toast.warning('图片大小超过 10MB 限制')
    e.target.value = ''
    return
  }

  uploadingImage.value = true
  try {
    const data = await uploadSingleFile(file)
    // 用文件名作为 alt 描述（去掉扩展名）
    const alt = file.name.replace(/\.[^.]+$/, '')
    insertAtCursor(textarea(), '![', `](${data.file_url})`, alt)
  } catch (err) {
    toast.error(err.message || '图片上传失败')
  } finally {
    uploadingImage.value = false
    e.target.value = ''
  }
}

// ========== 附件上传 ==========
function triggerFileInput() {
  fileInputRef.value?.click()
}

async function handleFileSelected(e) {
  const files = e.target.files
  if (!files || !files.length) return

  uploading.value = true
  for (const file of files) {
    if (file.size > 10 * 1024 * 1024) {
      toast.warning(`文件 ${file.name} 超过 10MB 限制`)
      continue
    }
    try {
      const data = await uploadSingleFile(file)
      form.attachments.push({
        file_name: data.file_name,
        file_url: data.file_url,
        file_size: data.file_size,
        file_type: data.file_type,
      })
    } catch (err) {
      toast.error(err.message || '文件上传失败')
    }
  }
  uploading.value = false
  e.target.value = ''
}

function removeAttachment(idx) {
  form.attachments.splice(idx, 1)
}

function formatFileSize(bytes) {
  if (!bytes) return '0 B'
  if (bytes < 1024) return bytes + ' B'
  if (bytes < 1024 * 1024) return (bytes / 1024).toFixed(1) + ' KB'
  return (bytes / 1024 / 1024).toFixed(1) + ' MB'
}

// ========== 其他 ==========
function selectType(type) {
  form.post_type = type
}

function addTag(e) {
  const val = e.target.value.trim()
  if (val && !form.tags.includes(val)) {
    form.tags.push(val)
  }
  tagInput.value = ''
}

function removeTag(idx) {
  form.tags.splice(idx, 1)
}

function addVoteOption() {
  voteOptionInputs.value.push('')
}

function removeVoteOption(idx) {
  if (voteOptionInputs.value.length <= 2) return
  voteOptionInputs.value.splice(idx, 1)
}

async function handleSubmit() {
  if (!form.title.trim()) { toast.warning('请输入标题'); return }
  if (!form.content.trim()) { toast.warning('请输入内容'); return }
  if (!form.category_id) { toast.warning('请选择板块'); return }

  const data = {
    category_id: Number(form.category_id),
    title: form.title.trim(),
    content: form.content.trim(),
    post_type: form.post_type,
    tags: form.tags,
    attachments: form.attachments.map(a => ({
      file_name: a.file_name,
      file_url: a.file_url,
      file_size: a.file_size,
      file_type: a.file_type,
    })),
  }

  if (form.post_type === 'poll') {
    const options = voteOptionInputs.value.filter(v => v.trim()).map(v => ({ label: v.trim() }))
    if (options.length < 2) { toast.warning('投票帖至少需要2个选项'); return }
    data.vote_options = options
  }

  submitting.value = true
  try {
    if (props.post?.id) {
      await updatePost(props.post.id, data)
      toast.success('帖子已更新')
    } else {
      await createPost(data)
      toast.success('发布成功')
    }
    emit('saved')
  } catch (err) {
    toast.error(err.message || '发布失败')
  } finally {
    submitting.value = false
  }
}
</script>

<template>
  <div class="editor-overlay" @click.self="emit('close')">
    <div class="editor">
      <header class="editor__header">
        <h2>{{ props.post?.id ? '编辑帖子' : '发布帖子' }}</h2>
        <button class="editor__close" @click="emit('close')"><AppIcon name="close" :size="18" /></button>
      </header>

      <div class="editor__body">
        <!-- 板块选择 -->
        <div class="editor__field">
          <label>选择板块</label>
          <select v-model="form.category_id" class="editor__select">
            <option v-for="c in categories" :key="c.id" :value="c.id">{{ c.name }}</option>
          </select>
        </div>

        <!-- 帖子类型 -->
        <div class="editor__field">
          <label>帖子类型</label>
          <div class="editor__type-tabs">
            <button :class="['type-tab', { 'type-tab--active': form.post_type === 'normal' }]" @click="selectType('normal')">普通帖</button>
            <button :class="['type-tab', { 'type-tab--active': form.post_type === 'long_article' }]" @click="selectType('long_article')">长文</button>
            <button :class="['type-tab', { 'type-tab--active': form.post_type === 'poll' }]" @click="selectType('poll')">投票</button>
          </div>
        </div>

        <!-- 标题 -->
        <div class="editor__field">
          <input
            v-model="form.title"
            class="editor__input"
            type="text"
            placeholder="请输入帖子标题 (1-120字)"
            maxlength="120"
          >
        </div>

        <!-- 编辑 + 预览 左右分栏 -->
        <div class="editor__field">
          <label>正文
            <span v-if="richTextMode" class="editor__label-hint">（富文本编辑器，支持表格、图片、图表）</span>
            <span v-else class="editor__label-hint">（支持 Markdown 语法）</span>
          </label>

          <div class="editor__panes">
            <!-- 左侧：编辑 -->
            <div class="editor__pane editor__pane--edit">
              <template v-if="richTextMode">
                <RichTextEditor v-model="form.content" placeholder="输入长文分析内容..." />
              </template>
              <template v-else>
                <div class="editor__toolbar">
                  <button title="加粗" @click="insertBold"><b>B</b></button>
                  <button title="斜体" @click="insertItalic"><i>I</i></button>
                  <button title="下划线" @click="insertUnderline"><u>U</u></button>
                  <span class="toolbar-divider" />
                  <button title="无序列表" @click="insertUl"><AppIcon name="list-bullet" :size="16" /></button>
                  <button title="有序列表" @click="insertOl"><AppIcon name="list-ordered" :size="16" /></button>
                  <span class="toolbar-divider" />
                  <button title="插入链接" @click="insertLink"><AppIcon name="link" :size="16" /></button>
                  <button title="上传图片并插入" :disabled="uploadingImage" @click="triggerImageInput">
                    <AppIcon name="image" :size="16" />
                    <span v-if="uploadingImage" class="spin-icon">⟳</span>
                  </button>
                  <button title="上传附件" :disabled="uploading" @click="triggerFileInput">
                    <AppIcon name="attachment" :size="16" />
                    <span v-if="uploading" class="spin-icon">⟳</span>
                  </button>
                </div>
                <textarea
                  ref="textareaRef"
                  v-model="form.content"
                  class="editor__textarea"
                  placeholder="输入 Markdown 正文内容..."
                  rows="16"
                />
              </template>
            </div>

            <!-- 右侧：预览（仅 Markdown 模式） -->
            <div v-if="!richTextMode" class="editor__pane editor__pane--preview">
              <div class="editor__preview-header">预览</div>
              <div class="editor__preview-body">
                <div v-if="form.title" class="editor__preview-title">{{ form.title }}</div>
                <div v-if="previewHtml" class="editor__preview-content" v-html="previewHtml" />
                <div v-else class="editor__preview-empty">
                  <AppIcon name="image" :size="36" />
                  <p>实时预览</p>
                  <span>在左侧输入内容后，此处将实时渲染 Markdown 效果</span>
                </div>
              </div>
            </div>
          </div>
        </div>

        <!-- 隐藏：图片上传 input -->
        <input
          ref="imageInputRef"
          type="file"
          accept="image/*"
          style="display: none"
          @change="handleImageSelected"
        >

        <!-- 隐藏：附件上传 input -->
        <input
          ref="fileInputRef"
          type="file"
          multiple
          style="display: none"
          @change="handleFileSelected"
        >

        <!-- 投票选项 -->
        <div v-if="form.post_type === 'poll'" class="editor__field">
          <label>投票选项（至少2项）</label>
          <div v-for="(opt, idx) in voteOptionInputs" :key="idx" class="editor__vote-option">
            <input v-model="voteOptionInputs[idx]" class="editor__input" :placeholder="'选项 ' + (idx + 1)" maxlength="200" />
            <button v-if="voteOptionInputs.length > 2" class="editor__vote-remove" @click="removeVoteOption(idx)">&times;</button>
          </div>
          <button class="editor__add-vote" @click="addVoteOption">+ 添加选项</button>
        </div>

        <!-- 标签 -->
        <div class="editor__field">
          <label>标签</label>
          <div class="editor__tags">
            <span v-for="(tag, idx) in form.tags" :key="idx" class="editor__tag">
              {{ tag }} <button class="editor__tag-remove" @click="removeTag(idx)">&times;</button>
            </span>
          </div>
          <input
            v-model="tagInput"
            class="editor__input"
            type="text"
            placeholder="输入标签，回车添加"
            @keyup.enter="addTag"
          >
        </div>

        <!-- 附件区 -->
        <div class="editor__field">
          <label>附件</label>
          <div v-if="form.attachments.length" class="editor__attachments">
            <div v-for="(att, idx) in form.attachments" :key="idx" class="attachment-chip">
              <span class="attachment-chip__icon"><AppIcon name="attachment" :size="14" /></span>
              <span class="attachment-chip__name" :title="att.file_name">{{ att.file_name }}</span>
              <span class="attachment-chip__size">{{ formatFileSize(att.file_size) }}</span>
              <button class="attachment-chip__remove" @click="removeAttachment(idx)">&times;</button>
            </div>
          </div>
          <button class="editor__attach-btn" :disabled="uploading" @click="triggerFileInput">
            <AppIcon name="attachment" :size="14" />
            {{ uploading ? ' 上传中...' : ' 选择文件' }}
          </button>
          <span class="editor__attach-hint">支持图片、PDF、文档等，单文件最大 10MB</span>
        </div>
      </div>

      <footer class="editor__footer">
        <button class="editor__btn editor__btn--secondary" @click="emit('close')">取消</button>
        <div class="editor__footer-right">
          <button class="editor__btn editor__btn--primary" :disabled="submitting" @click="handleSubmit">
            {{ submitting ? '发布中...' : (props.post?.id ? '保存修改' : '发布') }}
          </button>
        </div>
      </footer>
    </div>
  </div>
</template>

<style scoped>
.editor-overlay {
  align-items: center;
  background: var(--color-bg-overlay);
  display: flex;
  inset: 0;
  justify-content: center;
  position: fixed;
  z-index: 60;
}

.editor {
  background: var(--color-bg-card);
  border-radius: 12px;
  box-shadow: 0 20px 60px rgba(0, 0, 0, 0.15);
  display: flex;
  flex-direction: column;
  max-height: 92vh;
  max-width: 1200px;
  overflow-y: auto;
  width: 96vw;
}

.editor__header {
  align-items: center;
  border-bottom: 1px solid var(--color-border);
  display: flex;
  justify-content: space-between;
  padding: 20px 24px;
}

.editor__header h2 {
  font-size: 20px;
  margin: 0;
}

.editor__close {
  background: none;
  border: 0;
  border-radius: 6px;
  color: var(--color-text-muted);
  cursor: pointer;
  font-size: 18px;
  padding: 6px 10px;
}

.editor__close:hover {
  background: var(--color-bg-hover);
  color: var(--color-text-body);
}

.editor__body {
  display: grid;
  gap: 20px;
  padding: 24px;
}

.editor__field {
  display: grid;
  gap: 8px;
}

.editor__field label {
  color: var(--color-text-body);
  font-size: 14px;
  font-weight: 500;
}

.editor__label-hint {
  color: var(--color-text-muted);
  font-size: 12px;
  font-weight: 400;
}

.editor__input,
.editor__select,
.editor__textarea {
  border: 1px solid var(--color-border-input);
  border-radius: 8px;
  font: inherit;
  font-size: 14px;
  padding: 10px 12px;
  transition: border-color 0.15s, box-shadow 0.15s;
}

.editor__input:focus,
.editor__select:focus,
.editor__textarea:focus {
  border-color: var(--color-primary);
  box-shadow: 0 0 0 3px var(--color-primary-ring);
  outline: none;
}

.editor__type-tabs {
  display: flex;
  gap: 6px;
}

.type-tab {
  background: var(--color-bg-hover);
  border: 0;
  border-radius: 6px;
  color: var(--color-text-secondary);
  cursor: pointer;
  font: inherit;
  font-size: 13px;
  padding: 8px 14px;
}

.type-tab:hover {
  background: var(--color-border);
}

.type-tab--active {
  background: var(--color-primary);
  color: var(--color-bg-card);
}

/* ===== 编辑 + 预览 左右分栏 ===== */
.editor__panes {
  border: 1px solid var(--color-border);
  border-radius: 8px;
  display: flex;
  gap: 0;
  min-height: 420px;
  overflow: hidden;
}

.editor__pane {
  display: flex;
  flex-direction: column;
  flex: 1;
  min-width: 0;
}

.editor__pane--edit {
  border-right: 1px solid var(--color-border);
}

.editor__textarea {
  background: var(--color-bg-card);
  border: 0;
  border-radius: 0;
  flex: 1;
  font-family: 'SF Mono', 'Cascadia Code', 'Consolas', monospace;
  font-size: 14px;
  line-height: 1.7;
  min-height: 0;
  padding: 14px 16px;
  resize: none;
}

.editor__textarea:focus {
  box-shadow: none;
}

.editor__toolbar {
  align-items: center;
  background: var(--color-bg-hover);
  border-bottom: 1px solid var(--color-border);
  display: flex;
  gap: 4px;
  padding: 6px 10px;
  flex-shrink: 0;
}

.editor__toolbar button {
  align-items: center;
  background: none;
  border: 0;
  border-radius: 4px;
  color: var(--color-text-body);
  cursor: pointer;
  display: flex;
  font: inherit;
  font-size: 14px;
  gap: 4px;
  height: 32px;
  justify-content: center;
  min-width: 32px;
  padding: 0 6px;
  transition: background 0.15s;
}

.editor__toolbar button:hover:not(:disabled) {
  background: var(--color-border);
}

.editor__toolbar button:disabled {
  opacity: 0.5;
  cursor: not-allowed;
}

.toolbar-divider {
  background: var(--color-border-input);
  height: 20px;
  margin: 0 4px;
  width: 1px;
}

.spin-icon {
  animation: spin 0.8s linear infinite;
  display: inline-block;
  font-size: 12px;
  line-height: 1;
}

@keyframes spin {
  from { transform: rotate(0deg); }
  to { transform: rotate(360deg); }
}

/* ===== 预览面板 ===== */
.editor__preview-header {
  align-items: center;
  background: var(--color-bg-hover);
  border-bottom: 1px solid var(--color-border);
  color: var(--color-text-secondary);
  display: flex;
  flex-shrink: 0;
  font-size: 12px;
  font-weight: 500;
  height: 30px;
  padding: 0 14px;
  text-transform: uppercase;
  letter-spacing: 0.05em;
}

.editor__preview-body {
  flex: 1;
  overflow-y: auto;
  padding: 16px 18px;
}

.editor__preview-title {
  border-bottom: 1px solid var(--color-border);
  font-size: 20px;
  font-weight: 700;
  margin-bottom: 14px;
  padding-bottom: 12px;
}

.editor__preview-content {
  color: var(--color-text-body);
  font-size: 15px;
  line-height: 1.8;
  word-break: break-word;
}

.editor__preview-content :deep(h1),
.editor__preview-content :deep(h2),
.editor__preview-content :deep(h3) {
  margin: 1em 0 0.5em;
}

.editor__preview-content :deep(p) { margin: 0.6em 0; }

.editor__preview-content :deep(ul),
.editor__preview-content :deep(ol) {
  padding-left: 1.5em;
}

.editor__preview-content :deep(li) { margin: 0.3em 0; }

.editor__preview-content :deep(blockquote) {
  border-left: 3px solid var(--color-primary);
  color: var(--color-text-secondary);
  margin: 0.8em 0;
  padding: 0.4em 1em;
}

.editor__preview-content :deep(code) {
  background: var(--color-bg-hover);
  border-radius: 4px;
  font-family: 'SF Mono', 'Cascadia Code', 'Consolas', monospace;
  font-size: 0.9em;
  padding: 2px 6px;
}

.editor__preview-content :deep(pre) {
  background: var(--color-bg-hover);
  border-radius: 6px;
  overflow-x: auto;
  padding: 14px;
}

.editor__preview-content :deep(pre code) {
  background: none;
  padding: 0;
}

.editor__preview-content :deep(table) {
  border-collapse: collapse;
  width: 100%;
}

.editor__preview-content :deep(th),
.editor__preview-content :deep(td) {
  border: 1px solid var(--color-border);
  padding: 6px 10px;
  text-align: left;
}

.editor__preview-content :deep(th) {
  background: var(--color-bg-hover);
  font-weight: 600;
}

.editor__preview-content :deep(a) { color: var(--color-primary); }

.editor__preview-content :deep(img) {
  max-width: 100%;
  border-radius: 6px;
}

.editor__preview-empty {
  align-items: center;
  color: var(--color-text-muted);
  display: flex;
  flex-direction: column;
  gap: 8px;
  justify-content: center;
  min-height: 320px;
  text-align: center;
}

.editor__preview-empty p {
  font-size: 16px;
  margin: 0;
}

.editor__preview-empty span {
  font-size: 13px;
  max-width: 200px;
}

/* ===== 附件 ===== */
.editor__attachments {
  display: flex;
  flex-direction: column;
  gap: 6px;
}

.attachment-chip {
  align-items: center;
  background: var(--color-bg-hover);
  border-radius: 6px;
  display: flex;
  font-size: 13px;
  gap: 8px;
  padding: 8px 12px;
}

.attachment-chip__icon { color: var(--color-text-muted); flex-shrink: 0; }
.attachment-chip__name { color: var(--color-text-body); flex: 1; overflow: hidden; text-overflow: ellipsis; white-space: nowrap; }
.attachment-chip__size { color: var(--color-text-muted); flex-shrink: 0; }
.attachment-chip__remove { background: none; border: 0; color: var(--color-danger); cursor: pointer; flex-shrink: 0; font-size: 18px; padding: 0 2px; }

.editor__attach-btn {
  align-items: center;
  background: var(--color-bg-card);
  border: 1px dashed var(--color-border-input);
  border-radius: 8px;
  color: var(--color-text-secondary);
  cursor: pointer;
  display: inline-flex;
  font: inherit;
  font-size: 13px;
  gap: 4px;
  padding: 10px 18px;
  width: fit-content;
}

.editor__attach-btn:hover:not(:disabled) {
  border-color: var(--color-primary);
  color: var(--color-primary);
}

.editor__attach-btn:disabled { opacity: 0.6; cursor: not-allowed; }
.editor__attach-hint { color: var(--color-text-muted); font-size: 12px; }

.editor__footer {
  border-top: 1px solid var(--color-border);
  display: flex;
  justify-content: space-between;
  padding: 16px 24px;
}

.editor__footer-right { display: flex; gap: 8px; }

.editor__btn {
  border: 0;
  border-radius: 8px;
  cursor: pointer;
  font: inherit;
  font-size: 14px;
  font-weight: 500;
  padding: 10px 20px;
}

.editor__btn--primary {
  background: var(--color-primary);
  color: var(--color-bg-card);
}

.editor__btn--primary:hover:not(:disabled) { background: var(--color-primary-hover); }
.editor__btn--primary:disabled { opacity: 0.6; cursor: not-allowed; }

.editor__btn--secondary {
  background: var(--color-bg-card);
  border: 1px solid var(--color-border-input);
  color: var(--color-text-body);
}

.editor__btn--secondary:hover { background: var(--color-bg-hover); }

.editor__vote-option { display: flex; gap: 8px; align-items: center; }
.editor__vote-remove { background: none; border: 0; color: var(--color-danger); cursor: pointer; font-size: 20px; padding: 4px; }
.editor__add-vote { background: none; border: 1px dashed var(--color-border-input); border-radius: 6px; color: var(--color-primary); cursor: pointer; font: inherit; font-size: 13px; padding: 8px; width: 100%; }
.editor__add-vote:hover { background: var(--color-primary-light); }
.editor__tags { display: flex; flex-wrap: wrap; gap: 6px; margin-bottom: 6px; }
.editor__tag { background: var(--color-primary-light); border-radius: 4px; color: var(--color-primary); font-size: 12px; padding: 4px 8px; display: inline-flex; align-items: center; gap: 4px; }
.editor__tag-remove { background: none; border: 0; color: var(--color-primary); cursor: pointer; font-size: 14px; padding: 0; line-height: 1; }

/* 移动端回退为上下堆叠 */
@media (max-width: 780px) {
  .editor { max-width: 100vw; width: 100vw; max-height: 100vh; border-radius: 0; }
  .editor__panes { flex-direction: column; min-height: auto; }
  .editor__pane--edit { border-right: 0; border-bottom: 1px solid var(--color-border); }
  .editor__pane--preview { min-height: 260px; }
}
</style>
