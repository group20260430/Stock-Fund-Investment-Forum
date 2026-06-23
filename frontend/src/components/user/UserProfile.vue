<script setup>
import { ref } from 'vue'
import { useAuthStore } from '../../stores/auth'
import { useToastStore } from '../../stores/toast'
import AppIcon from '../common/AppIcon.vue'

const props = defineProps({
  user: { type: Object, required: true },
  isOwn: { type: Boolean, default: false },
})

const emit = defineEmits(['follow', 'message', 'edit', 'avatarUpdated'])
const auth = useAuthStore()
const toast = useToastStore()

const uploadingAvatar = ref(false)
const avatarInputRef = ref(null)

function triggerAvatarUpload() {
  avatarInputRef.value?.click()
}

async function handleAvatarSelected(e) {
  const files = e.target.files
  if (!files || !files.length) return
  const file = files[0]

  if (!file.type.startsWith('image/')) {
    toast.warning('请选择图片文件')
    e.target.value = ''
    return
  }
  if (file.size > 5 * 1024 * 1024) {
    toast.warning('头像图片不能超过 5MB')
    e.target.value = ''
    return
  }

  uploadingAvatar.value = true
  try {
    const formData = new FormData()
    formData.append('file', file)

    const token = localStorage.getItem('token')
    const API_BASE = import.meta.env.VITE_API_BASE_URL || 'http://localhost:8000/api'
    const response = await fetch(`${API_BASE}/uploads`, {
      method: 'POST',
      headers: token ? { Authorization: `Bearer ${token}` } : {},
      body: formData,
    })

    if (!response.ok) {
      const err = await response.json().catch(() => ({}))
      throw new Error(err.message || `上传失败 (${response.status})`)
    }

    const result = await response.json()
    const avatarUrl = result.data.file_url

    await auth.updateProfile({ avatar_url: avatarUrl })
    toast.success('头像已更新')
    emit('avatarUpdated', avatarUrl)
  } catch (err) {
    toast.error(err.message || '头像上传失败')
  } finally {
    uploadingAvatar.value = false
    e.target.value = ''
  }
}
</script>

<template>
  <div class="profile-header">
    <div class="profile-header__banner">
      <div class="profile-header__banner-placeholder" />
    </div>

    <div class="profile-header__info">
      <div class="profile-header__avatar-wrap" :class="{ 'profile-header__avatar-wrap--uploading': uploadingAvatar }">
        <img
          :src="user.avatar_url || ''"
          :alt="user.nickname"
          class="profile-header__avatar"
          @error="$event.target.src = 'data:image/svg+xml,%3Csvg xmlns=%22http://www.w3.org/2000/svg%22 viewBox=%220 0 80 80%22%3E%3Ccircle fill=%22%23d1d5db%22 cx=%2240%22 cy=%2240%22 r=%2240%22/%3E%3C/svg%3E'"
        >
        <!-- 自己的主页：可点击上传头像 -->
        <button
          v-if="isOwn"
          class="profile-header__avatar-overlay"
          :disabled="uploadingAvatar"
          @click="triggerAvatarUpload"
          :title="uploadingAvatar ? '上传中...' : '更换头像'"
        >
          <AppIcon name="image" :size="16" />
        </button>
        <input
          v-if="isOwn"
          ref="avatarInputRef"
          type="file"
          accept="image/*"
          style="display: none"
          @change="handleAvatarSelected"
        >
      </div>
      <div class="profile-header__details">
        <div class="profile-header__name-row">
          <h1>{{ user.nickname }}</h1>
          <span v-if="user.is_starred" class="star-badge" title="星标用户">⭐</span>
          <span class="level-badge">Lv.{{ user.level || 1 }}</span>
          <span
            v-if="user.auth_level === 'professional'"
            class="auth-badge auth-badge--pro"
            title="专业认证"
          >V</span>
          <span
            v-else-if="user.auth_level === 'verified'"
            class="auth-badge auth-badge--verified"
            title="实名认证"
          >V</span>
        </div>
        <div class="profile-header__points">{{ user.points || 0 }} 积分</div>
        <p v-if="user.bio" class="profile-header__bio">{{ user.bio }}</p>
        <div class="profile-header__stats">
          <router-link :to="'/users/' + user.id + '/follow?tab=following'">
            <strong>{{ user.achievements?.posts_count || 0 }}</strong> 帖子
          </router-link>
          <router-link :to="'/users/' + user.id + '/follow?tab=followers'">
            <strong>{{ user.followers_count || 0 }}</strong> 粉丝
          </router-link>
          <router-link :to="'/users/' + user.id + '/follow?tab=following'">
            <strong>{{ user.following_count || 0 }}</strong> 关注
          </router-link>
          <span>
            <strong>{{ user.achievements?.influence_score || 0 }}</strong> 影响力
          </span>
        </div>
        <div v-if="user.achievements?.badges && user.achievements.badges.length" class="profile-header__badges">
          <span v-for="badge in user.achievements.badges" :key="badge" class="badge-item">
            <AppIcon name="badge" :size="14" /> {{ badge }}
          </span>
        </div>
      </div>

      <div class="profile-header__actions">
        <template v-if="isOwn">
          <button class="action-btn action-btn--secondary" @click="emit('edit')">编辑资料</button>
        </template>
        <template v-else>
          <button
            :class="['action-btn', { 'action-btn--active': user.is_followed }]"
            @click="emit('follow', user.id)"
          >{{ user.is_followed ? "已关注" : "+ 关注" }}</button>
          <button
            :class="['action-btn action-btn--secondary', { 'star-btn--active': user.is_starred }]"
            :title="user.is_starred ? '取消星标' : '设为星标'"
            @click="emit('star', user.id)"
          >{{ user.is_starred ? "⭐ 已星标" : "☆ 星标" }}</button>
          <button class="action-btn action-btn--secondary" @click="emit('message', user.id)">
            <AppIcon name="message" :size="14" /> 私信
          </button>
        </template>
      </div>
    </div>
  </div>
</template>

<style scoped>
.profile-header {
  background: var(--color-bg-card);
  border: 1px solid var(--color-border);
  border-radius: 10px;
  margin-bottom: 24px;
  overflow: hidden;
}

.profile-header__banner {
  background: linear-gradient(135deg, var(--color-primary) 0%, var(--color-primary-500) 50%, var(--color-primary-400) 100%);
  height: 120px;
}

.profile-header__info {
  display: flex;
  gap: 20px;
  padding: 0 24px 24px;
  position: relative;
}

.profile-header__avatar {
  background: var(--color-bg-card);
  border: 4px solid var(--color-bg-card);
  border-radius: 50%;
  box-shadow: 0 2px 8px var(--color-bg-overlay);
  display: block;
  height: 80px;
  object-fit: cover;
  width: 80px;
}

.profile-header__avatar-wrap {
  flex-shrink: 0;
  height: 80px;
  margin-top: -40px;
  position: relative;
  width: 80px;
}

.profile-header__avatar-wrap--uploading .profile-header__avatar {
  opacity: 0.5;
}

.profile-header__avatar-overlay {
  align-items: center;
  background: rgba(0, 0, 0, 0.4);
  border: 0;
  border-radius: 50%;
  color: #fff;
  cursor: pointer;
  display: flex;
  inset: 4px;
  justify-content: center;
  opacity: 0;
  position: absolute;
  transition: opacity 0.2s;
}

.profile-header__avatar-wrap:hover .profile-header__avatar-overlay {
  opacity: 1;
}

.profile-header__avatar-overlay:disabled {
  cursor: not-allowed;
  opacity: 1;
}

.profile-header__details {
  flex: 1;
  min-width: 0;
  padding-top: 8px;
}

.profile-header__name-row {
  align-items: center;
  display: flex;
  gap: 8px;
  margin-bottom: 4px;
}

.profile-header__name-row h1 { font-size: 22px; margin: 0; }

.star-badge { font-size: 16px; }

.level-badge {
  background: var(--color-primary-light);
  border-radius: var(--radius-pill);
  color: var(--color-primary);
  font-size: 12px;
  font-weight: 700;
  padding: 3px 8px;
}

.profile-header__points {
  color: var(--color-text-muted);
  font-size: 13px;
  margin-bottom: 6px;
}

.auth-badge {
  border-radius: 50%;
  display: inline-flex;
  align-items: center;
  justify-content: center;
  font-size: 12px;
  font-weight: 700;
  height: 20px;
  width: 20px;
}

.auth-badge--pro { background: var(--color-info); color: var(--color-bg-card); }
.auth-badge--verified { background: var(--color-warning); color: var(--color-bg-card); }

.profile-header__bio {
  color: var(--color-text-secondary);
  font-size: 14px;
  margin: 4px 0 12px;
}

.profile-header__stats {
  color: var(--color-text-secondary);
  display: flex;
  font-size: 14px;
  gap: 20px;
}

.profile-header__stats a,
.profile-header__stats span { color: inherit; text-decoration: none; }

.profile-header__stats strong { color: var(--color-text-primary); }

.profile-header__badges {
  display: flex;
  flex-wrap: wrap;
  gap: 8px;
  margin-top: 12px;
}

.badge-item {
  background: var(--color-warning-light);
  border-radius: 4px;
  color: var(--color-warning);
  font-size: 12px;
  padding: 3px 8px;
}

.profile-header__actions {
  display: flex;
  flex-shrink: 0;
  gap: 8px;
  padding-top: 12px;
}

.action-btn {
  background: var(--color-primary);
  border: 0;
  border-radius: 6px;
  color: var(--color-bg-card);
  cursor: pointer;
  font: inherit;
  font-size: 14px;
  padding: 8px 18px;
  white-space: nowrap;
}

.action-btn:hover { background: var(--color-primary-hover); }

.action-btn--active {
  background: var(--color-bg-card);
  border: 1px solid var(--color-border-input);
  color: var(--color-text-secondary);
}

.action-btn--secondary {
  background: var(--color-bg-card);
  border: 1px solid var(--color-border-input);
  color: var(--color-text-body);
}

.action-btn--secondary:hover { background: var(--color-bg-hover); }

.star-btn--active {
  background: var(--color-warning-light);
  border-color: var(--color-warning);
  color: var(--color-warning);
}

@media (max-width: 780px) {
  .profile-header__info {
    flex-direction: column;
    align-items: center;
    text-align: center;
  }

  .profile-header__avatar-wrap {
    margin-top: -40px;
    height: 64px;
    width: 64px;
  }

  .profile-header__avatar {
    height: 64px;
    width: 64px;
  }

  .profile-header__name-row {
    justify-content: center;
  }

  .profile-header__stats {
    justify-content: center;
  }

  .profile-header__badges {
    justify-content: center;
  }

  .profile-header__actions {
    justify-content: center;
  }
=======
  .profile-header__info { flex-direction: column; align-items: center; text-align: center; }
  .profile-header__avatar { margin-top: -40px; height: 64px; width: 64px; }
  .profile-header__name-row { justify-content: center; }
  .profile-header__stats { justify-content: center; }
  .profile-header__badges { justify-content: center; }
  .profile-header__actions { justify-content: center; }
}
</style>
