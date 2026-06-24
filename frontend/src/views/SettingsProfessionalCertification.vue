<script setup>
import { ref } from 'vue'
import { useRouter } from 'vue-router'
import { useAuthStore } from '../stores/auth'
import { useToastStore } from '../stores/toast'
import AppIcon from '../components/common/AppIcon.vue'

const router = useRouter()
const auth = useAuthStore()
const toast = useToastStore()

const API_BASE = import.meta.env.VITE_API_BASE_URL || 'http://localhost:8000/api'

const docs = ref([])
const description = ref('')
const submitting = ref(false)
const uploading = ref(false)

// 可选的资质类型
const docTypeOptions = [
  '证券从业资格证',
  '基金从业资格证',
  '期货从业资格证',
  '投资顾问资格证书',
  'CPA注册会计师',
  'CFA特许金融分析师',
  'FRM金融风险管理师',
  '学历/学位证书',
  '其他从业资格证明',
]

async function addDoc() {
  const input = document.createElement('input')
  input.type = 'file'
  input.accept = '.pdf,.jpg,.jpeg,.png,.doc,.docx'
  input.onchange = async (e) => {
    const file = e.target.files?.[0]
    if (!file) return
    if (file.size > 10 * 1024 * 1024) { toast.warning('文件大小不能超过 10MB'); return }
    uploading.value = true
    try {
      const formData = new FormData()
      formData.append('file', file)
      const token = localStorage.getItem('token')
      const response = await fetch(`${API_BASE}/uploads`, {
        method: 'POST',
        headers: token ? { Authorization: `Bearer ${token}` } : {},
        body: formData,
      })
      if (!response.ok) throw new Error('上传失败')
      const result = await response.json()
      // 选择文件类型名称
      const name = file.name.replace(/\.[^.]+$/, '')
      docs.value.push({ name, url: result.data.file_url, file_name: file.name })
    } catch (err) {
      toast.error(err.message || '文件上传失败')
    } finally {
      uploading.value = false
    }
  }
  input.click()
}

function removeDoc(index) {
  docs.value.splice(index, 1)
}

function setDocName(index, name) {
  docs.value[index].name = name
}

async function handleSubmit() {
  if (docs.value.length === 0) {
    toast.warning('请至少上传一份资质证明文件')
    return
  }
  submitting.value = true
  try {
    const token = localStorage.getItem('token')
    const response = await fetch(`${API_BASE}/auth/professional-certification`, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
        ...(token ? { Authorization: `Bearer ${token}` } : {}),
      },
      body: JSON.stringify({
        qualification_docs: docs.value.map(d => ({ name: d.name, url: d.url })),
        description: description.value.trim() || null,
      }),
    })
    const result = await response.json()
    if (!response.ok) throw new Error(result.message || '提交失败')
    toast.success('专业认证申请已提交，请等待审核')
    router.push('/me/settings')
  } catch (err) {
    toast.error(err.message || '提交失败')
  } finally {
    submitting.value = false
  }
}
</script>

<template>
    <header class="toolbar">
      <button class="back-btn" @click="router.back()">&larr; 返回设置</button>
      <h1>专业认证</h1>
      <p>上传从业资格、学历证明等材料，审核通过后获得 <strong>加V标识</strong></p>
    </header>

    <div class="cert-body">
      <!-- 说明 -->
      <div class="info-card">
        <div class="info-card__icon">💼</div>
        <div class="info-card__text">
          <strong>什么是专业认证？</strong>
          <p>专业认证面向金融从业者、持牌分析师、基金经理等专业人士。<br>
          通过认证后，您的账号将获得 <strong class="pro-badge">专业认证 V</strong> 标识，提升您的发言可信度。</p>
        </div>
      </div>

      <!-- 上传资质证明 -->
      <div class="cert-card">
        <h2>资质证明文件</h2>
        <p class="form-hint">支持 PDF、JPG、PNG、DOC 等格式，单文件最大 10MB</p>

        <div v-if="docs.length" class="doc-list">
          <div v-for="(doc, idx) in docs" :key="idx" class="doc-item">
            <div class="doc-item__icon">
              <AppIcon name="attachment" :size="18" />
            </div>
            <div class="doc-item__info">
              <select
                :value="doc.name"
                class="doc-item__select"
                @change="setDocName(idx, $event.target.value)"
              >
                <option v-for="opt in docTypeOptions" :key="opt" :value="opt">{{ opt }}</option>
                <option value="__custom__">自定义...</option>
              </select>
              <input
                v-if="!docTypeOptions.includes(doc.name)"
                :value="doc.name"
                class="doc-item__custom-input"
                placeholder="输入文件名称"
                @change="setDocName(idx, $event.target.value)"
              />
              <span class="doc-item__file-name">{{ doc.file_name }}</span>
            </div>
            <button class="doc-item__remove" @click="removeDoc(idx)">&times;</button>
          </div>
        </div>

        <button class="upload-btn" :disabled="uploading" @click="addDoc">
          <AppIcon name="upload" :size="16" />
          {{ uploading ? '上传中...' : '上传证明文件' }}
        </button>
      </div>

      <!-- 申请说明 -->
      <div class="cert-card">
        <h2>申请说明（可选）</h2>
        <textarea
          v-model="description"
          class="form-textarea"
          placeholder="请简述您的从业经历或相关资质说明..."
          rows="4"
          maxlength="500"
        />
        <span class="char-count">{{ description.length }}/500</span>
      </div>

      <button class="submit-btn" :disabled="submitting || docs.length === 0" @click="handleSubmit">
        {{ submitting ? '提交中...' : '提交专业认证申请' }}
      </button>
    </div>
</template>

<style scoped>
.toolbar { margin-bottom: 24px; }
.toolbar h1 { font-size: 28px; margin: 8px 0 8px; }
.toolbar p { color: var(--color-text-secondary); margin: 0; }
.toolbar p strong { color: var(--color-primary); }
.back-btn { background: none; border: 0; color: var(--color-text-secondary); cursor: pointer; font: inherit; font-size: 14px; padding: 4px 0; }
.back-btn:hover { color: var(--color-primary); }
.cert-body { max-width: 600px; }

.info-card {
  align-items: flex-start;
  background: var(--color-primary-light);
  border: 1px solid var(--color-primary-ring);
  border-radius: 10px;
  display: flex;
  gap: 14px;
  margin-bottom: 20px;
  padding: 18px;
}
.info-card__icon { font-size: 28px; flex-shrink: 0; }
.info-card__text { font-size: 14px; line-height: 1.6; }
.info-card__text strong { display: block; margin-bottom: 4px; }
.info-card__text p { margin: 0; color: var(--color-text-secondary); }
.pro-badge {
  background: var(--color-primary);
  border-radius: 4px;
  color: #fff;
  font-size: 12px;
  padding: 2px 6px;
}

.cert-card {
  background: var(--color-bg-card);
  border: 1px solid var(--color-border);
  border-radius: 10px;
  margin-bottom: 20px;
  padding: 24px;
}
.cert-card h2 { font-size: 18px; margin: 0 0 12px; }
.form-hint { color: var(--color-text-muted); font-size: 13px; margin: 0 0 16px; }

.doc-list { display: grid; gap: 8px; margin-bottom: 12px; }
.doc-item {
  align-items: center;
  background: var(--color-bg-hover);
  border-radius: 8px;
  display: flex;
  gap: 10px;
  padding: 12px 14px;
}
.doc-item__icon { color: var(--color-primary); flex-shrink: 0; }
.doc-item__info { flex: 1; min-width: 0; display: grid; gap: 4px; }
.doc-item__select {
  border: 1px solid var(--color-border-input);
  border-radius: 6px;
  font: inherit;
  font-size: 13px;
  padding: 6px 8px;
  width: 100%;
}
.doc-item__custom-input {
  border: 0;
  border-bottom: 1px solid var(--color-border-input);
  font: inherit;
  font-size: 13px;
  padding: 4px 0;
  width: 100%;
  background: transparent;
}
.doc-item__custom-input:focus { outline: none; border-color: var(--color-primary); }
.doc-item__file-name { color: var(--color-text-muted); font-size: 12px; overflow: hidden; text-overflow: ellipsis; white-space: nowrap; }
.doc-item__remove { background: none; border: 0; color: var(--color-danger); cursor: pointer; font-size: 20px; padding: 4px; flex-shrink: 0; }

.upload-btn {
  align-items: center;
  background: var(--color-bg-card);
  border: 1px dashed var(--color-border-input);
  border-radius: 8px;
  color: var(--color-text-secondary);
  cursor: pointer;
  display: inline-flex;
  font: inherit;
  font-size: 13px;
  gap: 6px;
  padding: 10px 18px;
  transition: all 0.15s;
}
.upload-btn:hover:not(:disabled) { border-color: var(--color-primary); color: var(--color-primary); }
.upload-btn:disabled { opacity: 0.6; cursor: not-allowed; }

.form-textarea {
  border: 1px solid var(--color-border-input);
  border-radius: 8px;
  font: inherit;
  font-size: 14px;
  padding: 10px 14px;
  resize: vertical;
  width: 100%;
  box-sizing: border-box;
}
.form-textarea:focus { border-color: var(--color-primary); outline: none; box-shadow: 0 0 0 3px var(--color-primary-ring); }
.char-count { color: var(--color-text-muted); font-size: 12px; display: block; text-align: right; margin-top: 4px; }

.submit-btn { background: var(--color-primary); border: 0; border-radius: 8px; color: #fff; cursor: pointer; font: inherit; font-size: 15px; padding: 12px 24px; width: 100%; max-width: 600px; }
.submit-btn:hover { background: var(--color-primary-hover); }
.submit-btn:disabled { opacity: 0.6; cursor: not-allowed; }
</style>
