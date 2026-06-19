<script setup>
import { ref } from 'vue'
import AppIcon from '../common/AppIcon.vue'

const props = defineProps({
  post: { type: Object, required: true },
})

const emit = defineEmits(['close'])
const isPreview = ref(false)

function togglePreview() {
  isPreview.value = !isPreview.value
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
          <select class="editor__select">
            <option>综合讨论</option>
            <option>股票市场</option>
            <option>基金投资</option>
            <option>问答求助</option>
            <option>投资策略</option>
          </select>
        </div>

        <!-- 帖子类型 -->
        <div class="editor__field">
          <label>帖子类型</label>
          <div class="editor__type-tabs">
            <button class="type-tab type-tab--active">普通帖</button>
            <button class="type-tab">长文</button>
            <button class="type-tab">投票</button>
            <button class="type-tab">实时讨论</button>
          </div>
        </div>

        <!-- 标题 -->
        <div class="editor__field">
          <input
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
            class="editor__textarea"
            placeholder="在这里输入正文内容..."
            rows="12"
          />
        </div>

        <!-- 标签 -->
        <div class="editor__field">
          <label>标签</label>
          <input
            class="editor__input"
            type="text"
            placeholder="输入标签，回车添加"
          >
        </div>

        <!-- 附件区 -->
        <div class="editor__field">
          <label>附件</label>
          <div class="editor__attachments">
            <button class="editor__attach-btn"><AppIcon name="attachment" :size="14" /> 添加附件 (PDF/Excel, 最大10MB)</button>
          </div>
        </div>
      </div>

      <footer class="editor__footer">
        <button class="editor__btn editor__btn--secondary">存草稿</button>
        <div class="editor__footer-right">
          <button class="editor__btn editor__btn--secondary" @click="togglePreview">预览</button>
          <button class="editor__btn editor__btn--primary">发布</button>
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
</style>
