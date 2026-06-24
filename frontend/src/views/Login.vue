<script setup>
import { ref, reactive, onUnmounted } from 'vue'
import { useRouter, useRoute } from 'vue-router'
import { useAuthStore } from '../stores/auth'
import { getQQLoginUrl, sendCode as sendCodeApi, sendEmailCode, resetPassword } from '../api/auth'

const router = useRouter()
const route = useRoute()
const auth = useAuthStore()

// 登录模式：password | code | reset
const mode = ref('password')
const loading = ref(false)
const errorMsg = ref('')
const successMsg = ref('')

const form = reactive({
  phone: '',
  password: '',
  code: '',
  remember: false,
})

const resetForm = reactive({
  account: '',
  code: '',
  newPassword: '',
  confirmPassword: '',
})

const codeSending = ref(false)
const codeCountdown = ref(0)
let countdownTimer = null

function switchMode(m) {
  mode.value = m
  errorMsg.value = ''
  successMsg.value = ''
  if (m === 'reset' && form.phone && !resetForm.account) {
    resetForm.account = form.phone
  }
}

async function sendCode() {
  const account = mode.value === 'reset' ? resetForm.account : form.phone
  if (!account || codeCountdown.value > 0) return
  codeSending.value = true
  errorMsg.value = ''
  successMsg.value = ''
  try {
    const isEmail = /^[^\s@]+@[^\s@]+\.[^\s@]+$/.test(account)
    const codeType = mode.value === 'reset' ? 'reset_password' : 'login'
    if (isEmail) {
      await sendEmailCode(account, codeType)
    } else {
      await sendCodeApi(account, codeType)
    }
    successMsg.value = '验证码已发送，请在 5 分钟内完成操作'
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

async function handleLogin() {
  if (mode.value === 'reset') {
    await handleResetPassword()
    return
  }
  errorMsg.value = ''
  successMsg.value = ''

  // 基础校验
  if (!form.phone) {
    errorMsg.value = '请输入手机号或邮箱'
    return
  }
  if (mode.value === 'password' && !form.password) {
    errorMsg.value = '请输入密码'
    return
  }
  if (mode.value === 'code' && !form.code) {
    errorMsg.value = '请输入验证码'
    return
  }

  loading.value = true
  try {
    const credentials = {
      phone: form.phone,
      login_type: mode.value,
    }
    if (mode.value === 'password') {
      credentials.password = form.password
    } else {
      credentials.code = form.code
    }
    await auth.login(credentials)
    // 登录成功后跳转
    const redirect = route.query.redirect || '/'
    router.push(redirect)
  } catch (err) {
    errorMsg.value = err.message || '登录失败，请稍后重试'
  } finally {
    loading.value = false
  }
}

async function handleResetPassword() {
  errorMsg.value = ''
  successMsg.value = ''
  if (!resetForm.account) {
    errorMsg.value = '请输入手机号或邮箱'
    return
  }
  if (!resetForm.code) {
    errorMsg.value = '请输入验证码'
    return
  }
  if (!resetForm.newPassword) {
    errorMsg.value = '请输入新密码'
    return
  }
  if (resetForm.newPassword !== resetForm.confirmPassword) {
    errorMsg.value = '两次输入的新密码不一致'
    return
  }

  loading.value = true
  try {
    await resetPassword(resetForm.account, resetForm.code, resetForm.newPassword)
    form.phone = resetForm.account
    form.password = ''
    resetForm.code = ''
    resetForm.newPassword = ''
    resetForm.confirmPassword = ''
    switchMode('password')
    successMsg.value = '密码已重置，请使用新密码登录'
  } catch (err) {
    errorMsg.value = err.message || '重置密码失败'
  } finally {
    loading.value = false
  }
}

function handleQQLogin() {
  errorMsg.value = ''
  successMsg.value = ''
  const redirect = typeof route.query.redirect === 'string' ? route.query.redirect : '/'
  window.location.href = getQQLoginUrl(redirect)
}

onUnmounted(() => {
  if (countdownTimer) clearInterval(countdownTimer)
})
</script>

<template>
  <div class="auth-page">
    <div class="auth-card">
      <!-- Logo -->
      <div class="auth-card__header">
        <h1 class="auth-card__logo" @click="router.push('/')">
          股票基金投资论坛
        </h1>
        <p class="auth-card__subtitle">Stock &amp; Fund Forum</p>
      </div>

      <!-- 登录模式切换 -->
      <div class="auth-card__tabs">
        <button
          :class="['auth-tab', { 'auth-tab--active': mode === 'password' }]"
          @click="switchMode('password')"
        >
          密码登录
        </button>
        <button
          :class="['auth-tab', { 'auth-tab--active': mode === 'code' }]"
          @click="switchMode('code')"
        >
          验证码登录
        </button>
      </div>
      <p v-if="mode === 'reset'" class="reset-tip">
        通过手机号或邮箱验证码重置登录密码
      </p>

      <!-- 表单 -->
      <form class="auth-form" @submit.prevent="handleLogin">
        <!-- 错误提示 -->
        <div v-if="errorMsg" class="auth-error">{{ errorMsg }}</div>
        <div v-if="successMsg" class="auth-success">{{ successMsg }}</div>

        <template v-if="mode !== 'reset'">
          <!-- 手机号 -->
          <div class="form-field">
            <label>手机号 / 邮箱</label>
            <input
              v-model="form.phone"
              type="text"
              placeholder="请输入手机号或邮箱"
              autocomplete="username"
              class="form-input"
            >
          </div>
        </template>

        <!-- 密码模式 -->
        <template v-if="mode === 'password'">
          <div class="form-field">
            <label>密码</label>
            <input
              v-model="form.password"
              type="password"
              placeholder="请输入密码"
              autocomplete="current-password"
              class="form-input"
            >
          </div>

          <div class="form-footer">
            <label class="remember-me">
              <input v-model="form.remember" type="checkbox">
              记住登录状态
            </label>
            <button type="button" class="forgot-link" @click="switchMode('reset')">
              忘记密码？
            </button>
          </div>
        </template>

        <!-- 验证码模式 -->
        <template v-else-if="mode === 'code'">
          <div class="form-field">
            <label>验证码</label>
            <div class="code-row">
              <input
                v-model="form.code"
                type="text"
                placeholder="请输入验证码"
                maxlength="6"
                class="form-input code-input"
              >
              <button
                type="button"
                class="code-btn"
                :disabled="codeCountdown > 0 || codeSending"
                @click="sendCode"
              >
                {{ codeCountdown > 0 ? `${codeCountdown}s` : codeSending ? '发送中...' : '获取验证码' }}
              </button>
            </div>
          </div>
        </template>

        <!-- 忘记密码模式 -->
        <template v-else>
          <div class="form-field">
            <label>手机号 / 邮箱</label>
            <input
              v-model="resetForm.account"
              type="text"
              placeholder="请输入已注册的手机号或邮箱"
              autocomplete="username"
              class="form-input"
            >
          </div>

          <div class="form-field">
            <label>验证码</label>
            <div class="code-row">
              <input
                v-model="resetForm.code"
                type="text"
                placeholder="请输入验证码"
                maxlength="6"
                class="form-input code-input"
              >
              <button
                type="button"
                class="code-btn"
                :disabled="codeCountdown > 0 || codeSending"
                @click="sendCode"
              >
                {{ codeCountdown > 0 ? `${codeCountdown}s` : codeSending ? '发送中...' : '获取验证码' }}
              </button>
            </div>
          </div>

          <div class="form-field">
            <label>新密码</label>
            <input
              v-model="resetForm.newPassword"
              type="password"
              placeholder="8~32位，需包含字母和数字"
              autocomplete="new-password"
              class="form-input"
            >
          </div>

          <div class="form-field">
            <label>确认新密码</label>
            <input
              v-model="resetForm.confirmPassword"
              type="password"
              placeholder="请再次输入新密码"
              autocomplete="new-password"
              class="form-input"
            >
          </div>
        </template>

        <!-- 提交按钮 -->
        <button
          type="submit"
          class="submit-btn"
          :disabled="loading"
        >
          {{ loading ? (mode === 'reset' ? '提交中...' : '登录中...') : (mode === 'reset' ? '重置密码' : '登录') }}
        </button>
      </form>

      <div v-if="mode !== 'reset'" class="oauth-login">
        <div class="oauth-login__divider"><span>或</span></div>
        <button type="button" class="qq-login-btn" @click="handleQQLogin">
          使用 QQ 登录
        </button>
      </div>

      <!-- 底部链接 -->
      <p v-if="mode !== 'reset'" class="auth-card__footer">
        还没有账号？
        <router-link to="/register">立即注册</router-link>
      </p>
      <p v-else class="auth-card__footer">
        想起来了？
        <button type="button" class="footer-link" @click="switchMode('password')">返回登录</button>
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
  max-width: 420px;
  padding: 40px;
  width: 100%;
}

.auth-card__header {
  margin-bottom: 28px;
  text-align: center;
}

.auth-card__logo {
  color: var(--color-primary);
  cursor: pointer;
  font-size: 24px;
  margin: 0 0 8px;
}

.auth-card__subtitle {
  color: var(--color-text-muted);
  font-size: 13px;
  margin: 0;
}

.auth-card__tabs {
  display: flex;
  gap: 0;
  margin-bottom: 28px;
}

.reset-tip {
  color: var(--color-text-secondary);
  font-size: 14px;
  margin: -12px 0 20px;
  text-align: center;
}

.auth-tab {
  background: none;
  border: 0;
  border-bottom: 2px solid var(--color-border);
  color: var(--color-text-muted);
  cursor: pointer;
  flex: 1;
  font: inherit;
  font-size: 15px;
  font-weight: 500;
  padding: 10px 0;
  transition: color 0.15s, border-color 0.15s;
}

.auth-tab:hover {
  color: var(--color-text-body);
}

.auth-tab--active {
  border-bottom-color: var(--color-primary);
  color: var(--color-primary);
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
  padding: 10px 14px;
}

.auth-success {
  background: var(--color-success-light);
  border: 1px solid var(--color-success-light);
  border-radius: 8px;
  color: var(--color-success);
  font-size: 14px;
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

.form-footer {
  align-items: center;
  display: flex;
  justify-content: space-between;
}

.remember-me {
  align-items: center;
  color: var(--color-text-secondary);
  cursor: pointer;
  display: flex;
  font-size: 13px;
  gap: 6px;
}

.remember-me input {
  accent-color: var(--color-primary);
}

.forgot-link {
  background: none;
  border: 0;
  color: var(--color-primary);
  cursor: pointer;
  font: inherit;
  font-size: 13px;
  padding: 0;
  text-decoration: none;
}

.forgot-link:hover {
  text-decoration: underline;
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

.oauth-login {
  margin-top: 20px;
}

.oauth-login__divider {
  align-items: center;
  color: var(--color-text-muted);
  display: flex;
  font-size: 12px;
  gap: 12px;
  margin-bottom: 14px;
}

.oauth-login__divider::before,
.oauth-login__divider::after {
  background: var(--color-border);
  content: "";
  flex: 1;
  height: 1px;
}

.qq-login-btn {
  background: #12b7f5;
  border: 0;
  border-radius: 8px;
  color: #fff;
  cursor: pointer;
  font: inherit;
  font-size: 15px;
  font-weight: 600;
  padding: 12px 14px;
  width: 100%;
}

.qq-login-btn:hover {
  background: #0aa4df;
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

.footer-link {
  background: none;
  border: 0;
  color: var(--color-primary);
  cursor: pointer;
  font: inherit;
  font-weight: 500;
  padding: 0;
}

.auth-card__footer a:hover,
.footer-link:hover {
  text-decoration: underline;
}
</style>
