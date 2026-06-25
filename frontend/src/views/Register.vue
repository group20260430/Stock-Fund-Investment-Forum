<script setup>
import { ref, reactive } from 'vue'
import { useRouter } from 'vue-router'
import { useAuthStore } from '../stores/auth'
import { useToastStore } from '../stores/toast'
import { sendCode, verifyCode } from '../api/auth'
import { getQQLoginUrl, getWeChatLoginUrl, getWeiboLoginUrl } from '../api/auth'

const router = useRouter()
const auth = useAuthStore()
const toast = useToastStore()

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
    const res = await sendCode(form.phone, 'register')
    // 开发模式：后端返回验证码，显示在 Toast 上
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

async function nextStep() {
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
    // 向后端验证验证码
    loading.value = true
    try {
      await verifyCode(form.phone, form.code, 'register')
      step.value = 2
    } catch (err) {
      errorMsg.value = err.message || '验证码错误或已过期'
    } finally {
      loading.value = false
    }
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

function handleOAuthRegister(provider) {
  const redirect = '/'
  const urls = {
    qq: getQQLoginUrl(redirect),
    wechat: getWeChatLoginUrl(redirect),
    weibo: getWeiboLoginUrl(redirect),
  }
  window.location.href = urls[provider]
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

        <button type="submit" class="submit-btn" :disabled="loading">
          {{ loading ? '验证中...' : '下一步' }}
        </button>
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

      <!-- 第三方登录 -->
      <div v-if="step === 1" class="oauth-login">
        <div class="oauth-login__divider"><span>或</span></div>
        <div class="oauth-buttons">
          <button type="button" class="oauth-btn oauth-btn--qq" @click="handleOAuthRegister('qq')">
            <AppIcon name="qq" :size="18" /> QQ 注册
          </button>
          <button type="button" class="oauth-btn oauth-btn--wechat" @click="handleOAuthRegister('wechat')">
            <AppIcon name="wechat" :size="18" /> 微信注册
          </button>
          <button type="button" class="oauth-btn oauth-btn--weibo" @click="handleOAuthRegister('weibo')">
            <AppIcon name="weibo" :size="18" /> 微博注册
          </button>
        </div>
      </div>

      <!-- 底部链接 -->
      <p class="auth-card__footer">
        {{ step > 1 ? '' : '已有账号？' }}
        <a v-if="step > 1" href="javascript:void(0)" @click="goBack">返回上一步</a>
        <router-link v-else to="/login">立即登录</router-link>
        <span v-if="step === 1" class="auth-card__sep">|</span>
        <router-link v-if="step === 1" to="/register/email" class="auth-card__switch">
          使用邮箱注册
        </router-link>
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

.oauth-login {
  margin: 24px 0 0;
}

.oauth-login__divider {
  align-items: center;
  color: var(--color-text-muted);
  display: flex;
  font-size: 13px;
  gap: 12px;
  margin-bottom: 16px;
}

.oauth-login__divider::before,
.oauth-login__divider::after {
  border-top: 1px solid var(--color-border);
  content: '';
  flex: 1;
}

.oauth-buttons {
  display: flex;
  flex-direction: column;
  gap: 10px;
  margin-bottom: 8px;
}

.oauth-btn {
  border-radius: 8px;
  border: 1px solid var(--color-border);
  cursor: pointer;
  font: inherit;
  font-size: 14px;
  font-weight: 600;
  padding: 10px 14px;
  transition: background 0.2s;
  width: 100%;
}

.oauth-btn:hover {
  opacity: 0.85;
}

.oauth-btn--qq { background: #12b7f5; color: #fff; border-color: #12b7f5; }
.oauth-btn--wechat { background: #07c160; color: #fff; border-color: #07c160; }
.oauth-btn--weibo { background: #e6162d; color: #fff; border-color: #e6162d; }

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

.auth-card__sep {
  color: var(--color-border);
  margin: 0 8px;
}

.auth-card__switch {
  color: var(--color-text-secondary);
  font-size: 13px;
}
</style>
