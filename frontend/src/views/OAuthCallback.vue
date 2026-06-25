<script setup>
import { onMounted, ref } from 'vue'
import { useRouter } from 'vue-router'
import { useAuthStore } from '../stores/auth'
import { setToken } from '../utils/auth'

const router = useRouter()
const auth = useAuthStore()
const message = ref('正在完成 QQ 登录...')

onMounted(async () => {
  const params = new URLSearchParams(window.location.hash.replace(/^#/, ''))
  const token = params.get('token')
  const redirect = params.get('redirect') || '/'

  if (!token) {
    message.value = 'QQ 登录失败，请返回登录页重试'
    setTimeout(() => router.replace({ name: 'login' }), 1200)
    return
  }

  setToken(token)
  auth.token = token
  await auth.fetchUser()
  router.replace(redirect.startsWith('/') ? redirect : '/')
})
</script>

<template>
  <div class="oauth-callback">
    <div class="oauth-callback__card">
      <h1>{{ message }}</h1>
      <p>请稍候，正在为你跳转。</p>
    </div>
  </div>
</template>

<style scoped>
.oauth-callback {
  align-items: center;
  background: var(--color-bg-page);
  display: flex;
  justify-content: center;
  min-height: 100vh;
  padding: 24px;
}

.oauth-callback__card {
  background: var(--color-bg-card);
  border: 1px solid var(--color-border);
  border-radius: 12px;
  box-shadow: 0 4px 24px rgba(15, 23, 42, 0.08);
  max-width: 420px;
  padding: 32px;
  text-align: center;
  width: 100%;
}

.oauth-callback__card h1 {
  color: var(--color-text-primary);
  font-size: 20px;
  margin: 0 0 10px;
}

.oauth-callback__card p {
  color: var(--color-text-secondary);
  margin: 0;
}
</style>
