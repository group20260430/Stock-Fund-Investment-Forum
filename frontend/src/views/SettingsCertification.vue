<script setup>
import { ref } from 'vue'
import { useRouter } from 'vue-router'
import { useAuthStore } from '../stores/auth'
import { useToastStore } from '../stores/toast'
import { submitCertification } from '../api/auth'
import AppLayout from '../components/layout/AppLayout.vue'

const router = useRouter()
const auth = useAuthStore()
const toast = useToastStore()

const form = ref({
  real_name: '',
  id_number: '',
})
const submitting = ref(false)

async function handleSubmit() {
  if (!form.value.real_name.trim() || !form.value.id_number.trim()) {
    toast.warning('请填写完整信息')
    return
  }
  if (!/^\d{17}[\dXx]$/.test(form.value.id_number)) {
    toast.warning('请输入正确的身份证号码')
    return
  }
  submitting.value = true
  try {
    await submitCertification(form.value)
    toast.success('认证申请已提交，请等待审核')
    router.push('/me/settings')
  } catch (err) {
    toast.error(err.message || '提交失败')
  } finally {
    submitting.value = false
  }
}
</script>

<template>
  <AppLayout>
    <header class="toolbar">
      <button class="back-btn" @click="router.back()">&larr; 返回设置</button>
      <h1>实名认证</h1>
      <p>完成实名认证后可获得认证标识</p>
    </header>

    <div class="cert-card">
      <div class="form-field">
        <label>真实姓名</label>
        <input v-model="form.real_name" type="text" class="form-input" placeholder="请输入真实姓名" maxlength="30" />
      </div>
      <div class="form-field">
        <label>身份证号码</label>
        <input v-model="form.id_number" type="text" class="form-input" placeholder="请输入18位身份证号码" maxlength="18" />
      </div>
      <p class="form-hint">您的信息仅用于实名认证，不会对外公开</p>
      <button class="submit-btn" :disabled="submitting" @click="handleSubmit">
        {{ submitting ? '提交中...' : '提交认证申请' }}
      </button>
    </div>
  </AppLayout>
</template>

<style scoped>
.toolbar { margin-bottom: 24px; }
.toolbar h1 { font-size: 28px; margin: 8px 0 8px; }
.toolbar p { color: var(--color-text-secondary); margin: 0; }
.back-btn { background: none; border: 0; color: var(--color-text-secondary); cursor: pointer; font: inherit; font-size: 14px; padding: 4px 0; }
.back-btn:hover { color: var(--color-primary); }
.cert-card {
  background: var(--color-bg-card);
  border: 1px solid var(--color-border);
  border-radius: 10px;
  max-width: 480px;
  padding: 24px;
}
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
.submit-btn {
  background: var(--color-primary);
  border: 0;
  border-radius: 8px;
  color: #fff;
  cursor: pointer;
  font: inherit;
  font-size: 15px;
  padding: 12px 24px;
  width: 100%;
}
.submit-btn:hover { background: var(--color-primary-hover); }
.submit-btn:disabled { opacity: 0.6; cursor: not-allowed; }
</style>
