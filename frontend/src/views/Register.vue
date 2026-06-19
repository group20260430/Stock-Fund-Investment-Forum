<script setup>
import { ref, reactive } from 'vue'
import { useRouter } from 'vue-router'
import { useAuthStore } from '../stores/auth'
import { sendCode } from '../api/auth'

const router = useRouter()
const auth = useAuthStore()

const step = ref(1) // 1: 手机验证, 2: 设置密码, 3: 完善资料(可选)
const loading = ref(false)
const errorMsg = ref('')

const form = reactive({
  phone: '',
  code: '',
  password: '',
  confirmPassword: '',
  nickname: '',
  avatar_url: '',
  register_type: 'phone',
})

const codeSending = ref(false)
const codeCountdown = ref(0)
let countdownTimer = null
const codeRetries = ref(0)

async function requestCode() {
  if (!form.phone || codeCountdown.value > 0) return
  codeSending.value = true
  errorMsg.value = ''
  try {
    await sendCode(form.phone, 'register')
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

function nextStep() {
  errorMsg.value = ''

  if (step.value === 1) {
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
    // 模拟验证码校验（后端实际校验）
    step.value = 2
  } else if (step.value === 2) {
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
    if (!form.nickname || form.nickname.length < 2 || form.nickname.length > 20) {
      errorMsg.value = '昵称为2-20个字符'
      return
    }
    step.value = 3
  }
}

function skipStep3() {
  handleRegister()
}

async function handleRegister() {
  loading.value = true
  errorMsg.value = ''
  try {
    await auth.register({
      phone: form.phone,
      password: form.password,
      nickname: form.nickname,
      avatar_url: form.avatar_url,
      register_type: form.register_type,
    })
    router.push('/')
  } catch (err) {
    errorMsg.value = err.message || '注册失败，请稍后重试'
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
        <h1 class="auth-card__logo">创建您的账户</h1>
        <p class="auth-card__subtitle">加入投资讨论社区</p>
      </div>

      <!-- 步骤指示器 -->
      <div class="steps">
        <div :class="['step', { 'step--active': step >= 1, 'step--done': step > 1 }]">
          <span class="step__num">{{ step > 1 ? '✓' : '1' }}</span>
          <span class="step__label">手机验证</span>
        </div>
        <div class="step__line" :class="{ 'step__line--done': step > 1 }" />
        <div :class="['step', { 'step--active': step >= 2, 'step--done': step > 2 }]">
          <span class="step__num">{{ step > 2 ? '✓' : '2' }}</span>
          <span class="step__label">设置密码</span>
        </div>
        <div class="step__line" :class="{ 'step__line--done': step > 2 }" />
        <div :class="['step', { 'step--active': step >= 3 }]">
          <span class="step__num">3</span>
          <span class="step__label">完善资料</span>
        </div>
      </div>

      <!-- 错误提示 -->
      <div v-if="errorMsg" class="auth-error">{{ errorMsg }}</div>

      <!-- 第1步：手机验证 -->
      <form v-if="step === 1" class="auth-form" @submit.prevent="nextStep">
        <div class="form-field">
          <label>手机号</label>
          <input
            v-model="form.phone"
            type="tel"
            placeholder="请输入手机号"
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

        <button type="submit" class="submit-btn">下一步</button>
      </form>

      <!-- 第2步：设置密码和昵称 -->
      <form v-if="step === 2" class="auth-form" @submit.prevent="nextStep">
        <div class="form-field">
          <label>昵称</label>
          <input
            v-model="form.nickname"
            type="text"
            placeholder="2-20个字符"
            maxlength="20"
            class="form-input"
          >
        </div>

        <div class="form-field">
          <label>密码</label>
          <input
            v-model="form.password"
            type="password"
            placeholder="8-32位，含字母和数字"
            class="form-input"
            autocomplete="new-password"
          >
        </div>

        <div class="form-field">
          <label>确认密码</label>
          <input
            v-model="form.confirmPassword"
            type="password"
            placeholder="再次输入密码"
            class="form-input"
            autocomplete="new-password"
          >
        </div>

        <button type="submit" class="submit-btn">下一步</button>
      </form>

      <!-- 第3步：完善资料（可选） -->
      <div v-if="step === 3" class="auth-form">
        <p class="step3-hint">完善以下信息可获得更精准的内容推荐（可跳过）</p>

        <div class="form-field">
          <label>关注市场</label>
          <div class="checkbox-group">
            <label class="checkbox-item"><input type="checkbox" checked> A股</label>
            <label class="checkbox-item"><input type="checkbox"> 港股</label>
            <label class="checkbox-item"><input type="checkbox"> 美股</label>
            <label class="checkbox-item"><input type="checkbox"> 基金</label>
          </div>
        </div>

        <div class="form-field">
          <label>风险偏好</label>
          <div class="radio-group">
            <label class="radio-item"><input type="radio" name="risk"> 保守</label>
            <label class="radio-item"><input type="radio" name="risk" checked> 稳健</label>
            <label class="radio-item"><input type="radio" name="risk"> 激进</label>
          </div>
        </div>

        <button
          type="button"
          class="submit-btn"
          :disabled="loading"
          @click="handleRegister"
        >
          {{ loading ? '注册中...' : '完成注册' }}
        </button>
        <button type="button" class="skip-btn" @click="skipStep3">跳过</button>
      </div>

      <!-- 底部链接 -->
      <p class="auth-card__footer">
        {{ step > 1 ? '' : '已有账号？' }}
        <a v-if="step > 1" href="javascript:void(0)" @click="goBack">返回上一步</a>
        <router-link v-else to="/login">立即登录</router-link>
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
  text-align: center;
  white-space: nowrap;
}

.step--active .step__label {
  color: var(--color-primary);
  font-weight: 500;
}

.step__line {
  background: var(--color-border);
  height: 2px;
  margin: 0 8px;
  margin-bottom: 16px;
  width: 40px;
}

.step__line--done {
  background: var(--color-primary);
}

.auth-form {
  display: grid;
  gap: 18px;
}

.auth-error {
  background: var(--color-danger-light);
  border: 1px solid var(--color-danger-light);
  border-radius: 8px;
  color: var(--color-danger-hover);
  font-size: 14px;
  margin-bottom: 4px;
  padding: 10px 14px;
}

.form-field {
  display: grid;
  gap: 6px;
}

.form-field label {
  color: var(--color-text-body);
  font-size: 14px;
  font-weight: 500;
}

.form-input {
  border: 1px solid var(--color-border-input);
  border-radius: 8px;
  font: inherit;
  font-size: 15px;
  padding: 12px 14px;
  transition: border-color 0.15s, box-shadow 0.15s;
}

.form-input:focus {
  border-color: var(--color-primary);
  box-shadow: 0 0 0 3px var(--color-primary-ring);
  outline: none;
}

.code-row {
  display: flex;
  gap: 10px;
}

.code-input {
  flex: 1;
}

.code-btn {
  background: var(--color-bg-card);
  border: 1px solid var(--color-primary);
  border-radius: 8px;
  color: var(--color-primary);
  cursor: pointer;
  font: inherit;
  font-size: 13px;
  padding: 12px 14px;
  white-space: nowrap;
}

.code-btn:hover:not(:disabled) {
  background: var(--color-primary-light);
}

.code-btn:disabled {
  border-color: var(--color-border-input);
  color: var(--color-text-muted);
  cursor: not-allowed;
}

.submit-btn {
  background: var(--color-primary);
  border: 0;
  border-radius: 8px;
  color: var(--color-bg-card);
  cursor: pointer;
  font: inherit;
  font-size: 16px;
  font-weight: 600;
  margin-top: 4px;
  padding: 14px;
  transition: background 0.15s;
}

.submit-btn:hover:not(:disabled) {
  background: var(--color-primary-hover);
}

.submit-btn:disabled {
  opacity: 0.7;
  cursor: not-allowed;
}

.skip-btn {
  background: none;
  border: 0;
  color: var(--color-text-muted);
  cursor: pointer;
  font: inherit;
  font-size: 14px;
  padding: 8px;
}

.skip-btn:hover {
  color: var(--color-text-secondary);
}

.step3-hint {
  color: var(--color-text-secondary);
  font-size: 13px;
  margin: 0;
  text-align: center;
}

.checkbox-group,
.radio-group {
  display: flex;
  flex-wrap: wrap;
  gap: 12px;
}

.checkbox-item,
.radio-item {
  align-items: center;
  color: var(--color-text-body);
  cursor: pointer;
  display: flex;
  font-size: 14px;
  gap: 6px;
}

.checkbox-item input,
.radio-item input {
  accent-color: var(--color-primary);
}

.auth-card__footer {
  color: var(--color-text-secondary);
  font-size: 14px;
  margin: 24px 0 0;
  text-align: center;
}

.auth-card__footer a {
  color: var(--color-primary);
  text-decoration: none;
  font-weight: 500;
}

.auth-card__footer a:hover {
  text-decoration: underline;
}
</style>
