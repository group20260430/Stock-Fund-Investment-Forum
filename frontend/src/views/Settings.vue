<script setup>
import { ref, reactive, onMounted } from 'vue'
import { useRouter } from 'vue-router'
import { useAuthStore } from '../stores/auth'
import { useToastStore } from '../stores/toast'
import { fetchPrivacySettings, updatePrivacySettings } from '../api/auth'

const router = useRouter()
const auth = useAuthStore()
const toast = useToastStore()
const saving = ref(false)
const saved = ref(false)
const privacySaving = ref(false)

const form = reactive({
  nickname: auth.user?.nickname || '',
  bio: auth.user?.bio || '',
  phone: auth.user?.phone || '',
  email: auth.user?.email || '',
})

const privacy = reactive({
  profile_visibility: 'public',
  message_permission: 'everyone',
  show_investment_info: true,
  show_follow_lists: true,
  show_activity_status: true,
})

onMounted(loadPrivacy)

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

async function loadPrivacy() {
  try {
    Object.assign(privacy, await fetchPrivacySettings())
  } catch (err) {
    toast.error(err.message || '隐私设置加载失败')
  }
}

async function handlePrivacySave() {
  privacySaving.value = true
  try {
    Object.assign(privacy, await updatePrivacySettings(privacy))
    toast.success('隐私设置已保存')
  } catch (err) {
    toast.error(err.message || '保存失败')
  } finally {
    privacySaving.value = false
  }
}
</script>

<template>
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

    <div class="settings-card">
      <h2>隐私设置</h2>
      <div class="form-field">
        <label>资料可见性</label>
        <select v-model="privacy.profile_visibility" class="form-input">
          <option value="public">所有人可见</option>
          <option value="followers_only">仅粉丝可见</option>
          <option value="private">仅自己可见</option>
        </select>
      </div>
      <div class="form-field">
        <label>谁可以给我发私信</label>
        <select v-model="privacy.message_permission" class="form-input">
          <option value="everyone">所有人</option>
          <option value="followers_only">仅粉丝</option>
          <option value="none">不接收私信</option>
        </select>
      </div>
      <label class="switch-row">
        <span>
          <strong>展示投资信息</strong>
          <small>公开风险偏好、投资标签等信息</small>
        </span>
        <input v-model="privacy.show_investment_info" type="checkbox">
      </label>
      <label class="switch-row">
        <span>
          <strong>展示关注/粉丝列表</strong>
          <small>允许别人查看你的关注和粉丝</small>
        </span>
        <input v-model="privacy.show_follow_lists" type="checkbox">
      </label>
      <label class="switch-row">
        <span>
          <strong>展示活跃状态</strong>
          <small>公开成就、影响力等活动信息</small>
        </span>
        <input v-model="privacy.show_activity_status" type="checkbox">
      </label>
      <button class="save-btn" :disabled="privacySaving" @click="handlePrivacySave">
        {{ privacySaving ? '保存中...' : '保存隐私设置' }}
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

.switch-row {
  align-items: center;
  border-top: 1px solid var(--color-border-light);
  cursor: pointer;
  display: flex;
  gap: 16px;
  justify-content: space-between;
  padding: 14px 0;
}

.switch-row strong {
  color: var(--color-text-body);
  display: block;
  font-size: 14px;
}

.switch-row small {
  color: var(--color-text-muted);
  display: block;
  font-size: 12px;
  margin-top: 4px;
}

.switch-row input {
  height: 18px;
  width: 18px;
}

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
