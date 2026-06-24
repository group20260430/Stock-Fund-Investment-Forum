<script setup>
import { ref } from 'vue'
import { useRouter } from 'vue-router'
import { useAuthStore } from '../stores/auth'
import { useToastStore } from '../stores/toast'
import { submitCertification } from '../api/auth'
import AppIcon from '../components/common/AppIcon.vue'

const router = useRouter()
const auth = useAuthStore()
const toast = useToastStore()

const form = ref({
  real_name: '',
  id_number: '',
  id_card_front: '',
  id_card_back: '',
})
const submitting = ref(false)
const frontPreview = ref('')
const backPreview = ref('')
const uploadingFront = ref(false)
const uploadingBack = ref(false)

function handleImageUpload(side) {
  const input = document.createElement('input')
  input.type = 'file'
  input.accept = 'image/*'
  input.onchange = async (e) => {
    const file = e.target.files?.[0]
    if (!file) return
    if (file.size > 5 * 1024 * 1024) { toast.warning('图片大小不能超过 5MB'); return }
    if (!file.type.startsWith('image/')) { toast.warning('请选择图片文件'); return }
    if (side === 'front') uploadingFront.value = true; else uploadingBack.value = true
    try {
      const base64 = await fileToBase64(file)
      if (side === 'front') {
        form.value.id_card_front = base64
        frontPreview.value = URL.createObjectURL(file)
      } else {
        form.value.id_card_back = base64
        backPreview.value = URL.createObjectURL(file)
      }
    } catch { toast.error('图片读取失败') }
    finally { if (side === 'front') uploadingFront.value = false; else uploadingBack.value = false }
  }
  input.click()
}

function fileToBase64(file) {
  return new Promise((resolve, reject) => {
    const reader = new FileReader()
    reader.onload = () => resolve(reader.result)
    reader.onerror = reject
    reader.readAsDataURL(file)
  })
}

function removeImage(side) {
  if (side === 'front') { form.value.id_card_front = ''; frontPreview.value = '' }
  else { form.value.id_card_back = ''; backPreview.value = '' }
}

async function handleSubmit() {
  if (!form.value.real_name.trim()) { toast.warning('请输入真实姓名'); return }
  if (!/^\d{17}[\dXx]$/.test(form.value.id_number)) { toast.warning('请输入正确的18位身份证号码'); return }
  if (!form.value.id_card_front) { toast.warning('请上传身份证正面照片'); return }
  if (!form.value.id_card_back) { toast.warning('请上传身份证反面照片'); return }
  submitting.value = true
  try {
    await submitCertification({
      real_name: form.value.real_name.trim(),
      id_number: form.value.id_number.trim(),
      id_card_front: form.value.id_card_front,
      id_card_back: form.value.id_card_back,
    })
    toast.success('认证申请已提交，请等待审核')
    router.push('/me/settings')
  } catch (err) {
    toast.error(err.message || '提交失败')
  } finally { submitting.value = false }
}
</script>

<template>
    <header class="toolbar">
      <button class="back-btn" @click="router.back()">&larr; 返回设置</button>
      <h1>实名认证</h1>
      <p>完成实名认证后可获得认证标识</p>
    </header>

    <div class="cert-body">
      <div class="cert-card">
        <h2>基本信息</h2>
        <div class="form-field">
          <label>真实姓名</label>
          <input v-model="form.real_name" type="text" class="form-input" placeholder="请输入真实姓名" maxlength="30" />
        </div>
        <div class="form-field">
          <label>身份证号码</label>
          <input v-model="form.id_number" type="text" class="form-input" placeholder="请输入18位身份证号码" maxlength="18" />
        </div>
      </div>

      <div class="cert-card">
        <h2>上传身份证</h2>
        <p class="form-hint">请上传清晰的身份证正反面照片，仅用于实名认证，不会对外公开</p>
        <div class="upload-grid">
          <div class="upload-box">
            <label>身份证正面（人像面）</label>
            <div class="upload-area" :class="{ 'upload-area--has-image': frontPreview }" @click="!frontPreview && handleImageUpload('front')">
              <img v-if="frontPreview" :src="frontPreview" class="upload-preview" alt="身份证正面" />
              <div v-else class="upload-placeholder">
                <AppIcon name="image" :size="32" />
                <span>{{ uploadingFront ? '读取中...' : '点击上传正面照片' }}</span>
              </div>
            </div>
            <button v-if="frontPreview" class="upload-remove" @click="removeImage('front')">移除</button>
          </div>
          <div class="upload-box">
            <label>身份证反面（国徽面）</label>
            <div class="upload-area" :class="{ 'upload-area--has-image': backPreview }" @click="!backPreview && handleImageUpload('back')">
              <img v-if="backPreview" :src="backPreview" class="upload-preview" alt="身份证反面" />
              <div v-else class="upload-placeholder">
                <AppIcon name="image" :size="32" />
                <span>{{ uploadingBack ? '读取中...' : '点击上传反面照片' }}</span>
              </div>
            </div>
            <button v-if="backPreview" class="upload-remove" @click="removeImage('back')">移除</button>
          </div>
        </div>
      </div>

      <button class="submit-btn" :disabled="submitting" @click="handleSubmit">
        {{ submitting ? '提交中...' : '提交认证申请' }}
      </button>
    </div>
</template>

<style scoped>
.toolbar { margin-bottom: 24px; }
.toolbar h1 { font-size: 28px; margin: 8px 0 8px; }
.toolbar p { color: var(--color-text-secondary); margin: 0; }
.back-btn { background: none; border: 0; color: var(--color-text-secondary); cursor: pointer; font: inherit; font-size: 14px; padding: 4px 0; }
.back-btn:hover { color: var(--color-primary); }
.cert-body { max-width: 600px; }
.cert-card {
  background: var(--color-bg-card);
  border: 1px solid var(--color-border);
  border-radius: 10px;
  margin-bottom: 20px;
  padding: 24px;
}
.cert-card h2 { font-size: 18px; margin: 0 0 16px; }
.form-field { display: grid; gap: 6px; margin-bottom: 16px; }
.form-field label { color: var(--color-text-body); font-size: 14px; font-weight: 500; }
.form-input {
  border: 1px solid var(--color-border-input);
  border-radius: 8px;
  font: inherit;
  font-size: 15px;
  padding: 10px 14px;
  transition: border-color 0.15s;
  width: 100%;
  box-sizing: border-box;
}
.form-input:focus { border-color: var(--color-primary); outline: none; box-shadow: 0 0 0 3px var(--color-primary-ring); }
.form-hint { color: var(--color-text-muted); font-size: 13px; margin: 0 0 16px; }
.upload-grid { display: grid; grid-template-columns: 1fr 1fr; gap: 16px; }
.upload-box { display: grid; gap: 8px; }
.upload-box label { color: var(--color-text-body); font-size: 14px; font-weight: 500; }
.upload-area { border: 2px dashed var(--color-border-input); border-radius: 10px; cursor: pointer; min-height: 160px; overflow: hidden; position: relative; transition: border-color 0.15s; }
.upload-area:hover { border-color: var(--color-primary); }
.upload-area--has-image { border-style: solid; border-color: var(--color-border); cursor: default; }
.upload-placeholder { align-items: center; color: var(--color-text-muted); display: flex; flex-direction: column; gap: 8px; height: 160px; justify-content: center; }
.upload-placeholder span { font-size: 13px; }
.upload-preview { display: block; max-height: 220px; object-fit: contain; width: 100%; }
.upload-remove { background: none; border: 0; color: var(--color-danger); cursor: pointer; font: inherit; font-size: 13px; padding: 4px 0; text-align: center; }
.upload-remove:hover { text-decoration: underline; }
.submit-btn { background: var(--color-primary); border: 0; border-radius: 8px; color: #fff; cursor: pointer; font: inherit; font-size: 15px; padding: 12px 24px; width: 100%; max-width: 600px; }
.submit-btn:hover { background: var(--color-primary-hover); }
.submit-btn:disabled { opacity: 0.6; cursor: not-allowed; }
@media (max-width: 500px) { .upload-grid { grid-template-columns: 1fr; } }
</style>
