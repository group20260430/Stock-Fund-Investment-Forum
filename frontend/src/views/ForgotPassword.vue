<script setup>
import { ref, reactive } from 'vue'
import { useRouter } from 'vue-router'
import { useToastStore } from '../stores/toast'
import { sendCode, verifyCode, resetPassword } from '../api/auth'

const router = useRouter()
const toast = useToastStore()

const step = ref(1) // 1: 验证身份, 2: 重置密码, 3: 完成
const loading = ref(false)
const errorMsg = ref('')

const form = reactive({
  phone: '',
  code: '',
  password: '',
  confirmPassword: '',
})

const codeSending = ref(false)
const codeCountdown = ref(0)
let countdownTimer = null

async function requestCode() {
  if (!form.phone || codeCountdown.value > 0) return
  codeSending.value = true
  errorMsg.value = ''
  try {
    const res = await sendCode(form.phone, 'reset_password')
    if (res?.dev_code) {
      toast.info(`验证码：${res.dev_code}（开发模式）`, 10000)
    }
    codeCountdown.value = 60
    countdownTimer = setInterval(() => {
      codeCountdown.value--
      if (codeCountdown.value <= 0) {
        clearInterval(countdownTimer)
        countdownTimer = null
      }
    }, 1000)
  } catch (err) {
    errorMsg.value = err.message || '发送验证码失败'
  } finally {
    codeSending.value = false
  }
}

async function verifyIdentity() {
  errorMsg.value = ''

  if (!form.phone) {
    errorMsg.value = '请输入手机号'
    return
  }
  if (!/^1\d{10}$/.test(form.phone)) {
    errorMsg.value = '手机号格式不正确'
    return
  }
  if (!form.code) {
    errorMsg.value = '请输入验证码'
    return
  }

  loading.value = true
  try {
    await verifyCode(form.phone, form.code, 'reset_password')
    step.value = 2
  } catch (err) {
    errorMsg.value = err.message || '验证码错误或已过期'
  } finally {
    loading.value = false
  }
}

async function handleReset() {
  errorMsg.value = ''

  if (!form.password || form.password.length < 8) {
    errorMsg.value = '密码至少8位'
    return
  }
  if (!/[a-zA-Z]/.test(form.password) || !/\d/.test(form.password)) {
    errorMsg.value = '密码需包含字母和数字'
    return
  }
  if (form.password !== form.confirmPassword) {
    errorMsg.value = '两次输入的密码不一致'
    return
  }

  loading.value = true
  try {
    await resetPassword(form.phone, form.code, form.password)
    step.value = 3
  } catch (err) {
    errorMsg.value = err.message || '重置密码失败，请稍后重试'
  } finally {
    loading.value = false
  }
}

function goBack() {
  if (step.value > 1) {
    step.value--
    errorMsg.value = ''
  } else {
    router.push('/login')
  }
}
</script>

<template>
  <div class="auth-page">
    <div class="auth-card">
      <!-- Logo -->
      <div class="auth-card__header">
        <h1 class="auth-card__logo">重置密码</h1>
        <p class="auth-card__subtitle">验证身份后即可设置新密码</p>
      </div>

      <!-- 步骤指示器 -->
      <div class="steps">
        <div :class="['step', { 'step--active': step >= 1, 'step--done': step > 1 }]">
          <span class="step__num">{{ step > 1 ? '✓' : '1' }}</span>
          <span class="step__label">验证身份</span>
        </div>
        <div class="step__line" :class="{ 'step__line--done': step > 1 }" />
        <div :class="['step', { 'step--active': step >= 2, 'step--done': step > 2 }]">
          <span class="step__num">{{ step > 2 ? '✓' : '2' }}</span>
          <span class="step__label">设置新密码</span>
        </div>
        <div class="step__line" :class="{ 'step__line--done': step > 2 }" />
        <div :class="['step', { 'step--active': step >= 3 }]">
          <span class="step__num">3</span>
          <span class="step__label">完成</span>
        </div>
      </div>

      <!-- 错误提示 -->
      <div v-if="errorMsg" class="auth-error">{{ errorMsg }}</div>

      <!-- 第1步：验证身份 -->
      <form v-if="step === 1" class="auth-form" @submit.prevent="verifyIdentity">
        <div class="form-field">
          <label>手机号</label>
          <input
            v-model="form.phone"
            type="tel"
            placeholder="请输入注册时使用的手机号"
            maxlength="11"
            class="form-input"
            autocomplete="tel"
          >
        </div>

        <div class="form-field">
          <label>验证码</label>
          <div class="code-row">
            <input
              v-model="form.code"
              type="text"
              placeholder="输入验证码"
              maxlength="6"
              class="form-input code-input"
            >
            <button
              type="button"
              class="code-btn"
              :disabled="codeCountdown > 0 || codeSending"
              @click="requestCode"
            >
              {{ codeCountdown > 0 ? `${codeCountdown}s` : codeSending ? '发送中...' : '获取验证码' }}
            </button>
          </div>
        </div>

        <button type="submit" class="submit-btn" :disabled="loading">
          {{ loading ? '验证中...' : '下一步' }}
        </button>
      </form>

      <!-- 第2步：设置新密码 -->
      <form v-if="step === 2" class="auth-form" @submit.prevent="handleReset">
        <div class="form-field">
          <label>新密码</label>
          <input
            v-model="form.password"
            type="password"
            placeholder="8-32位，含字母和数字"
            class="form-input"
            autocomplete="new-password"
          >
        </div>

        <div class="form-field">
          <label>确认新密码</label>
          <input
            v-model="form.confirmPassword"
            type="password"
            placeholder="再次输入新密码"
            class="form-input"
            autocomplete="new-password"
          >
        </div>

        <button type="submit" class="submit-btn" :disabled="loading">
          {{ loading ? '重置中...' : '确认重置' }}
        </button>
      </form>

      <!-- 第3步：完成 -->
      <div v-if="step === 3" class="auth-form">
        <div class="success-icon">✓</div>
        <h2 class="success-title">密码重置成功</h2>
        <p class="success-desc">请使用新密码登录您的账号</p>
        <button type="button" class="submit-btn" @click="router.push('/login')">
          去登录
        </button>
      </div>

      <!-- 底部链接 -->
      <p class="auth-card__footer">
        <a href="javascript:void(0)" @click="goBack">返回</a>
        <span class="auth-card__sep">|</span>
        <router-link to="/login">返回登录</router-link>
      </p>
    </div>
  </div>
</template>

<style scoped>
.auth-page {
  align-items: center;
  background: var(--color-bg-page);
  display: flex;
  justify-content: center;
  min-height: 100vh;
  padding: 24px;
}

.auth-card {
  background: var(--color-bg-card);
  border: 1px solid var(--color-border);
  border-radius: 12px;
  box-shadow: 0 4px 24px rgba(15, 23, 42, 0.08);
  max-width: 440px;
  padding: 40px;
  width: 100%;
}

.auth-card__header {
  margin-bottom: 28px;
  text-align: center;
}

.auth-card__logo {
  color: var(--color-text-primary);
  font-size: 22px;
  margin: 0 0 6px;
}

.auth-card__subtitle {
  color: var(--color-text-muted);
  font-size: 14px;
  margin: 0;
}

/* 步骤指示器 */
.steps {
  align-items: center;
  display: flex;
  gap: 0;
  justify-content: center;
  margin-bottom: 28px;
}

.step {
  align-items: center;
  display: flex;
  flex-direction: column;
  gap: 4px;
}

.step__num {
  align-items: center;
  background: var(--color-border);
  border-radius: 50%;
  color: var(--color-text-muted);
  display: flex;
  font-size: 12px;
  font-weight: 700;
  height: 24px;
  justify-content: center;
  transition: all 0.2s;
  width: 24px;
}

.step--active .step__num {
  background: var(--color-primary);
  color: var(--color-bg-card);
}

.step--done .step__num {
  background: var(--color-primary);
  color: var(--color-bg-card);
}

.step__label {
  color: var(--color-text-muted);
  font-size: 11px;
}

.step--active .step__label,
.step--done .step__label {
  color: var(--color-primary);
  font-weight: 600;
}

.step__line {
  background: var(--color-border);
  height: 2px;
  margin: 0 8px;
  margin-top: -10px;
  width: 40px;
}

.step__line--done {
  background: var(--color-primary);
}

/* 表单 */
.auth-form {
  display: flex;
  flex-direction: column;
  gap: 16px;
}

.form-field {
  display: flex;
  flex-direction: column;
  gap: 6px;
}

.form-field label {
  color: var(--color-text-secondary);
  font-size: 13px;
  font-weight: 600;
}

.form-input {
  background: var(--color-bg-input, #f8fafc);
  border: 1px solid var(--color-border);
  border-radius: 8px;
  color: var(--color-text-primary);
  font-size: 14px;
  outline: none;
  padding: 10px 14px;
  transition: border-color 0.2s;
}

.form-input:focus {
  border-color: var(--color-primary);
  box-shadow: 0 0 0 3px rgba(37, 99, 235, 0.1);
}

.code-row {
  display: flex;
  gap: 10px;
}

.code-input {
  flex: 1;
}

.code-btn {
  background: var(--color-bg-input, #f8fafc);
  border: 1px solid var(--color-border);
  border-radius: 8px;
  color: var(--color-primary);
  cursor: pointer;
  flex-shrink: 0;
  font-size: 13px;
  font-weight: 600;
  padding: 10px 16px;
  transition: all 0.2s;
  white-space: nowrap;
}

.code-btn:hover:not(:disabled) {
  background: var(--color-primary);
  color: #fff;
}

.code-btn:disabled {
  color: var(--color-text-muted);
  cursor: not-allowed;
}

.submit-btn {
  background: var(--color-primary);
  border: none;
  border-radius: 8px;
  color: #fff;
  cursor: pointer;
  font-size: 15px;
  font-weight: 600;
  margin-top: 8px;
  padding: 12px;
  transition: opacity 0.2s;
}

.submit-btn:hover:not(:disabled) {
  opacity: 0.9;
}

.submit-btn:disabled {
  cursor: not-allowed;
  opacity: 0.6;
}

.auth-error {
  background: #fef2f2;
  border: 1px solid #fecaca;
  border-radius: 8px;
  color: #dc2626;
  font-size: 13px;
  margin-bottom: 8px;
  padding: 10px 14px;
}

.auth-card__footer {
  color: var(--color-text-muted);
  font-size: 13px;
  margin-top: 24px;
  text-align: center;
}

.auth-card__footer a {
  color: var(--color-primary);
  text-decoration: none;
}

.auth-card__sep {
  margin: 0 8px;
}

/* 成功页 */
.success-icon {
  align-items: center;
  background: #16a34a;
  border-radius: 50%;
  color: #fff;
  display: flex;
  font-size: 32px;
  font-weight: 700;
  height: 64px;
  justify-content: center;
  margin: 20px auto 16px;
  width: 64px;
}

.success-title {
  color: var(--color-text-primary);
  font-size: 20px;
  margin: 0;
  text-align: center;
}

.success-desc {
  color: var(--color-text-muted);
  font-size: 14px;
  margin: 8px 0 0;
  text-align: center;
}
</style>
