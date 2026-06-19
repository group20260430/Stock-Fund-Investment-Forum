<script setup>
defineProps({
  user: { type: Object, required: true },
  showFollowBtn: { type: Boolean, default: true },
})

defineEmits(['follow'])
</script>

<template>
  <div class="user-card">
    <img
      :src="user.avatar_url || ''"
      :alt="user.nickname"
      class="user-card__avatar"
      @error="$event.target.src = 'data:image/svg+xml,%3Csvg xmlns=%22http://www.w3.org/2000/svg%22 viewBox=%220 0 48 48%22%3E%3Ccircle fill=%22%23d1d5db%22 cx=%2224%22 cy=%2224%22 r=%2224%22/%3E%3C/svg%3E'"
    >
    <div class="user-card__info">
      <div class="user-card__name-row">
        <strong>{{ user.nickname }}</strong>
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
      <p v-if="user.bio" class="user-card__bio">{{ user.bio }}</p>
      <div class="user-card__stats">
        <span>帖子 {{ user.achievements?.posts_count || user.posts_count || 0 }}</span>
        <span>粉丝 {{ user.followers_count || 0 }}</span>
      </div>
    </div>
    <button
      v-if="showFollowBtn"
      :class="['user-card__follow-btn', { 'user-card__follow-btn--active': user.is_followed }]"
      @click.stop="$emit('follow', user.id)"
    >
      {{ user.is_followed ? '已关注' : '+ 关注' }}
    </button>
  </div>
</template>

<style scoped>
.user-card {
  align-items: center;
  background: var(--color-bg-card);
  border: 1px solid var(--color-border);
  border-radius: 8px;
  cursor: pointer;
  display: flex;
  gap: 12px;
  padding: 16px;
  transition: box-shadow 0.15s;
}

.user-card:hover {
  box-shadow: 0 2px 8px rgba(15, 23, 42, 0.06);
}

.user-card__avatar {
  border-radius: 50%;
  flex-shrink: 0;
  height: 44px;
  object-fit: cover;
  width: 44px;
}

.user-card__info {
  flex: 1;
  min-width: 0;
}

.user-card__name-row {
  align-items: center;
  display: flex;
  gap: 6px;
  margin-bottom: 2px;
}

.user-card__name-row strong {
  font-size: 15px;
}

.auth-badge {
  border-radius: 50%;
  display: inline-flex;
  align-items: center;
  justify-content: center;
  font-size: 10px;
  font-weight: 700;
  height: 16px;
  width: 16px;
}

.auth-badge--pro {
  background: var(--color-info);
  color: var(--color-bg-card);
}

.auth-badge--verified {
  background: var(--color-warning);
  color: var(--color-bg-card);
}

.user-card__bio {
  color: var(--color-text-secondary);
  font-size: 13px;
  margin: 2px 0;
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
}

.user-card__stats {
  color: var(--color-text-muted);
  display: flex;
  font-size: 12px;
  gap: 12px;
}

.user-card__follow-btn {
  background: var(--color-primary);
  border: 0;
  border-radius: 6px;
  color: var(--color-bg-card);
  cursor: pointer;
  flex-shrink: 0;
  font: inherit;
  font-size: 13px;
  padding: 6px 14px;
  white-space: nowrap;
}

.user-card__follow-btn--active {
  background: var(--color-bg-card);
  border: 1px solid var(--color-border-input);
  color: var(--color-text-secondary);
}

.user-card__follow-btn:hover:not(.user-card__follow-btn--active) {
  background: var(--color-primary-hover);
}
</style>
