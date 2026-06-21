<script setup>
import { ref, reactive, onMounted } from 'vue'
import { useToastStore } from '../../stores/toast'
import { createPost, updatePost, fetchCategories } from '../../api/posts'
import AppIcon from '../common/AppIcon.vue'

const props = defineProps({
  post: { type: Object, default: null },
})

const emit = defineEmits(['close', 'saved'])
const toast = useToastStore()

const isPreview = ref(false)
const submitting = ref(false)
const categories = ref([])
const tagInput = ref('')

const form = reactive({
  category_id: '',
  title: '',
  content: '',
  post_type: 'normal',
  tags: [],
  vote_options: [],
})

const voteOptionInputs = ref(['', ''])

onMounted(async () => {
  try {
    categories.value = await fetchCategories()
    if (categories.value.length) form.category_id = categories.value[0].id
  } catch { /* ignore */ }
  // 编辑模式：回填数据
  if (props.post) {
    form.category_id = props.post.category_id || props.post.category?.id || ''
    form.title = props.post.title || ''
    form.content = props.post.content || ''
    form.post_type = props.post.post_type || 'normal'
    form.tags = props.post.tags || []
    if (props.post.poll?.options) {
      voteOptionInputs.value = props.post.poll.options.map(o => o.text || o.label || '')
      form.vote_options = props.post.poll.options.map(o => ({ label: o.text || o.label || '' }))
    } else if (props.post.vote_options) {
      voteOptionInputs.value = props.post.vote_options.map(o => o.label || '')
      form.vote_options = props.post.vote_options.map(o => ({ label: o.label }))
    }
  }
})

function togglePreview() {
  isPreview.value = !isPreview.value
}

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
    emit('close')
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
        <h2>发布帖子</h2>
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

        <!-- 富文本工具栏 + 编辑区 -->
        <div class="editor__field">
          <div class="editor__toolbar">
            <button title="加粗"><b>B</b></button>
            <button title="斜体"><i>I</i></button>
            <button title="下划线"><u>U</u></button>
            <span class="toolbar-divider" />
            <button title="无序列表">≡</button>
            <button title="有序列表">1.</button>
            <span class="toolbar-divider" />
            <button title="链接"><AppIcon name="link" :size="16" /></button>
            <button title="图片"><AppIcon name="image" :size="16" /></button>
            <button title="附件"><AppIcon name="attachment" :size="16" /></button>
          </div>
          <textarea
            v-model="form.content"
            class="editor__textarea"
            placeholder="在这里输入正文内容..."
            rows="12"
          />
        </div>

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
          <div class="editor__attachments">
            <span class="editor__attach-hint">附件功能：目前支持填写文件 URL</span>
          </div>
        </div>
      </div>

      <footer class="editor__footer">
        <button class="editor__btn editor__btn--secondary" @click="emit('close')">取消</button>
        <div class="editor__footer-right">
          <button class="editor__btn editor__btn--secondary" @click="togglePreview">预览</button>
          <button class="editor__btn editor__btn--primary" :disabled="submitting" @click="handleSubmit">
            {{ submitting ? '发布中...' : (props.post?.id ? '保存修改' : '发布') }}
          </button>
        </div>
      </footer>

      <!-- 预览弹窗 -->
      <div v-if="isPreview" class="preview-overlay" @click.self="isPreview = false">
        <div class="preview">
          <h3>预览</h3>
          <p class="preview__placeholder">预览内容将在支持 Markdown 后渲染</p>
          <button class="editor__btn editor__btn--secondary" @click="isPreview = false">关闭</button>
        </div>
      </div>
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
  max-height: 90vh;
  max-width: 800px;
  overflow-y: auto;
  width: 92vw;
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

.editor__textarea {
  resize: vertical;
  min-height: 240px;
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

.editor__toolbar {
  align-items: center;
  background: var(--color-bg-hover);
  border: 1px solid var(--color-border);
  border-radius: 8px 8px 0 0;
  display: flex;
  gap: 4px;
  padding: 8px 12px;
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
  height: 32px;
  justify-content: center;
  min-width: 32px;
  padding: 0 6px;
}

.editor__toolbar button:hover {
  background: var(--color-border);
}

.toolbar-divider {
  background: var(--color-border-input);
  height: 20px;
  margin: 0 4px;
  width: 1px;
}

.editor__attachments {
  align-items: center;
  display: flex;
  gap: 12px;
}

.editor__attach-btn {
  background: var(--color-bg-card);
  border: 1px dashed var(--color-border-input);
  border-radius: 8px;
  color: var(--color-text-secondary);
  cursor: pointer;
  font: inherit;
  font-size: 13px;
  padding: 12px 20px;
}

.editor__attach-btn:hover {
  border-color: var(--color-primary);
  color: var(--color-primary);
}

.editor__footer {
  border-top: 1px solid var(--color-border);
  display: flex;
  justify-content: space-between;
  padding: 16px 24px;
}

.editor__footer-right {
  display: flex;
  gap: 8px;
}

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

.editor__btn--primary:hover {
  background: var(--color-primary-hover);
}

.editor__btn--secondary {
  background: var(--color-bg-card);
  border: 1px solid var(--color-border-input);
  color: var(--color-text-body);
}

.editor__btn--secondary:hover {
  background: var(--color-bg-hover);
}

/* 预览 */
.preview-overlay {
  align-items: center;
  background: var(--color-bg-overlay);
  display: flex;
  inset: 0;
  justify-content: center;
  position: fixed;
  z-index: 70;
}

.preview {
  background: var(--color-bg-card);
  border-radius: 10px;
  max-width: 600px;
  padding: 32px;
  text-align: center;
  width: 90vw;
}

.preview h3 {
  margin: 0 0 16px;
}

.preview__placeholder {
  color: var(--color-text-muted);
  margin-bottom: 20px;
}

.editor__vote-option { display: flex; gap: 8px; align-items: center; }
.editor__vote-remove { background: none; border: 0; color: var(--color-danger); cursor: pointer; font-size: 20px; padding: 4px; }
.editor__add-vote { background: none; border: 1px dashed var(--color-border-input); border-radius: 6px; color: var(--color-primary); cursor: pointer; font: inherit; font-size: 13px; padding: 8px; width: 100%; }
.editor__add-vote:hover { background: var(--color-primary-light); }
.editor__tags { display: flex; flex-wrap: wrap; gap: 6px; margin-bottom: 6px; }
.editor__tag { background: var(--color-primary-light); border-radius: 4px; color: var(--color-primary); font-size: 12px; padding: 4px 8px; display: inline-flex; align-items: center; gap: 4px; }
.editor__tag-remove { background: none; border: 0; color: var(--color-primary); cursor: pointer; font-size: 14px; padding: 0; line-height: 1; }
.editor__attach-hint { color: var(--color-text-muted); font-size: 13px; }
</style>
