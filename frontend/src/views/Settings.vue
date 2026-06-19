<script setup>
import { ref, reactive } from 'vue'
import { useRouter } from 'vue-router'
import { useAuthStore } from '../stores/auth'
import AppLayout from '../components/layout/AppLayout.vue'

const router = useRouter()
const auth = useAuthStore()
const saving = ref(false)
const saved = ref(false)

const form = reactive({
  nickname: auth.user?.nickname || '',
  bio: auth.user?.bio || '',
  phone: auth.user?.phone || '',
  email: auth.user?.email || '',
})

async function handleSave() {
  saving.value = true
  try {
    await auth.updateProfile(form)
    saved.value = true
    setTimeout(() => { saved.value = false }, 2000)
  } catch (err) {
    console.error('保存失败:', err.message)
  } finally {
    saving.value = false
  }
}
</script>

<template>
  <AppLayout>
    <header class="toolbar">
      <div>
        <h1>个人设置</h1>
        <p>管理您的个人资料和偏好</p>
      </div>
    </header>

    <div class="settings-card">
      <h2>个人资料</h2>
      <div class="form-field">
        <label>昵称</label>
        <input v-model="form.nickname" type="text" class="form-input" maxlength="20">
      </div>
      <div class="form-field">
        <label>个人简介</label>
        <textarea v-model="form.bio" class="form-input" rows="3" maxlength="500" placeholder="介绍一下自己..." />
      </div>
      <div class="form-field">
        <label>手机号</label>
        <input v-model="form.phone" type="text" class="form-input" disabled>
        <span class="form-hint">手机号暂不支持修改</span>
      </div>
      <button class="save-btn" :disabled="saving" @click="handleSave">
        {{ saved ? '✓ 已保存' : saving ? '保存中...' : '保存修改' }}
      </button>
    </div>

    <!-- 认证入口 -->
    <div class="settings-card">
      <h2>身份认证</h2>
      <p class="settings-card__desc">完成实名认证后可获得认证标识和专业用户权限</p>
      <button class="cert-btn" @click="$router.push('/me/settings/certification')">
        去认证
      </button>
    </div>

    <!-- 风险评估 -->
    <div class="settings-card">
      <h2>投资者风险评估</h2>
      <p class="settings-card__desc">完成风险评估问卷以获得个性化的内容推荐</p>
      <button class="cert-btn cert-btn--secondary" @click="$router.push('/me/settings/assessment')">
        进行评估
      </button>
    </div>
  </AppLayout>
</template>

<style scoped>
.toolbar { margin-bottom: 24px; }
.toolbar h1 { font-size: 28px; margin: 0 0 8px; }
.toolbar p { color: var(--color-text-secondary); margin: 0; }

.settings-card {
  background: var(--color-bg-card);
  border: 1px solid var(--color-border);
  border-radius: 10px;
  margin-bottom: 20px;
  padding: 24px;
}

.settings-card h2 { font-size: 18px; margin: 0 0 16px; }
.settings-card__desc { color: var(--color-text-secondary); font-size: 14px; margin: 0 0 12px; }

.form-field { display: grid; gap: 6px; margin-bottom: 16px; }
.form-field label { color: var(--color-text-body); font-size: 14px; font-weight: 500; }

.form-input {
  border: 1px solid var(--color-border-input);
  border-radius: 8px;
  font: inherit;
  font-size: 14px;
  padding: 10px 12px;
  width: 100%;
}

.form-input:focus {
  border-color: var(--color-primary);
  box-shadow: 0 0 0 3px var(--color-primary-ring);
  outline: none;
}

.form-hint { color: var(--color-text-muted); font-size: 12px; }

.save-btn {
  background: var(--color-primary);
  border: 0;
  border-radius: 8px;
  color: var(--color-bg-card);
  cursor: pointer;
  font: inherit;
  font-size: 14px;
  padding: 10px 24px;
}

.save-btn:hover { background: var(--color-primary-hover); }

.cert-btn {
  background: var(--color-primary);
  border: 0;
  border-radius: 6px;
  color: var(--color-bg-card);
  cursor: pointer;
  font: inherit;
  font-size: 14px;
  padding: 8px 20px;
}

.cert-btn--secondary {
  background: var(--color-bg-card);
  border: 1px solid var(--color-primary);
  color: var(--color-primary);
}

.cert-btn--secondary:hover { background: var(--color-primary-light); }
</style>
