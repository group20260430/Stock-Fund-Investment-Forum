<script setup>
import { timeAgo } from '../../utils/format'
import AppIcon from '../common/AppIcon.vue'


defineProps({
  post: { type: Object, required: true },
})
</script>

<template>
  <!-- 帖子正文 -->
  <article class="post-detail">
    <!-- 标题区 -->
    <header class="post-detail__header">
      <div class="post-detail__badges">
        <span v-if="post.category" class="post-detail__category">
          {{ typeof post.category === 'object' ? post.category.name : post.category }}
        </span>
        <span v-if="post.is_elite" class="post-detail__badge post-detail__badge--elite">精华</span>
      </div>
      <h1 class="post-detail__title">{{ post.title }}</h1>
      <div class="post-detail__meta">
        <img
          :src="(typeof post.author === 'object' ? post.author.avatar_url : '') || ''"
          :alt="typeof post.author === 'object' ? post.author.nickname : ''"
          class="post-detail__avatar"
          @error="$event.target.style.display = 'none'"
        >
        <div>
          <strong class="post-detail__author">
            {{ typeof post.author === 'object' ? post.author.nickname : post.author }}
          </strong>
          <span
            v-if="post.author && post.author.auth_level === 'professional'"
            class="auth-badge auth-badge--pro"
            title="专业认证"
          >V</span>
          <span
            v-else-if="post.author && post.author.auth_level === 'verified'"
            class="auth-badge auth-badge--verified"
            title="实名认证"
          >V</span>
        </div>
        <span class="post-detail__dot">·</span>
        <span class="post-detail__time">{{ timeAgo(post.created_at) }}</span>
        <span class="post-detail__dot">·</span>
        <span class="post-detail__views">{{ post.view_count || 0 }} 次阅读</span>
      </div>
    </header>

    <!-- 正文内容 -->
    <div class="post-detail__content" v-html="post.content" />

    <!-- 附件区 -->
    <div v-if="post.attachments && post.attachments.length" class="post-detail__attachments">
      <h4>附件</h4>
      <div v-for="att in post.attachments" :key="att.file_name" class="attachment-item">
        <span class="attachment-item__icon"><AppIcon name="attachment" :size="18" /></span>
        <span class="attachment-item__name">{{ att.file_name }}</span>
        <span class="attachment-item__size">{{ ((att.file_size || 0) / 1024 / 1024).toFixed(1) }}MB</span>
        <a v-if="att.file_url" :href="att.file_url" class="attachment-item__download" download>下载</a>
      </div>
    </div>

    <!-- 标签 -->
    <div v-if="post.tags && post.tags.length" class="post-detail__tags">
      <span v-for="tag in post.tags" :key="tag" class="post-detail__tag">{{ tag }}</span>
    </div>

    <!-- 互动统计 -->
    <div class="post-detail__stats">
      <span>👍 {{ post.like_count || 0 }}</span>
      <span>💬 {{ post.comment_count || 0 }}</span>
      <span>⭐ {{ post.collect_count || 0 }}</span>
      <span>↗ {{ post.share_count || 0 }}</span>
    </div>
  </article>
</template>

<style scoped>
.post-detail {
  background: var(--color-bg-card);
  border: 1px solid var(--color-border);
  border-radius: 10px;
  margin-bottom: 24px;
  padding: 32px;
}

.post-detail__header {
  margin-bottom: 24px;
}

.post-detail__badges {
  display: flex;
  gap: 8px;
  margin-bottom: 12px;
}

.post-detail__category {
  background: var(--color-primary-light);
  border-radius: 4px;
  color: var(--color-primary);
  font-size: 13px;
  font-weight: 500;
  padding: 3px 10px;
}

.post-detail__badge--elite {
  background: var(--color-warning-light);
  border-radius: 4px;
  color: var(--color-warning);
  font-size: 13px;
  font-weight: 600;
  padding: 3px 10px;
}

.post-detail__title {
  font-size: 28px;
  font-weight: 700;
  line-height: 1.4;
  margin: 0 0 16px;
}

.post-detail__meta {
  align-items: center;
  color: var(--color-text-secondary);
  display: flex;
  flex-wrap: wrap;
  font-size: 14px;
  gap: 6px;
}

.post-detail__avatar {
  border-radius: 50%;
  height: 32px;
  object-fit: cover;
  width: 32px;
}

.post-detail__author {
  color: var(--color-text-body);
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
  vertical-align: middle;
}

.auth-badge--pro {
  background: var(--color-info);
  color: var(--color-bg-card);
}

.auth-badge--verified {
  background: var(--color-warning);
  color: var(--color-bg-card);
}

.post-detail__dot {
  color: var(--color-border-input);
}

.post-detail__content {
  color: var(--color-text-body);
  font-size: 16px;
  line-height: 1.9;
  margin-bottom: 24px;
  word-break: break-word;
}

.post-detail__attachments {
  background: var(--color-bg-hover);
  border-radius: 8px;
  margin-bottom: 16px;
  padding: 16px;
}

.post-detail__attachments h4 {
  color: var(--color-text-body);
  font-size: 14px;
  margin: 0 0 12px;
}

.attachment-item {
  align-items: center;
  display: flex;
  font-size: 13px;
  gap: 8px;
  padding: 6px 0;
}

.attachment-item__icon {
  font-size: 18px;
}

.attachment-item__name {
  color: var(--color-text-body);
  flex: 1;
}

.attachment-item__size {
  color: var(--color-text-muted);
}

.attachment-item__download {
  color: var(--color-primary);
  text-decoration: none;
}

.attachment-item__download:hover {
  text-decoration: underline;
}

.post-detail__tags {
  display: flex;
  flex-wrap: wrap;
  gap: 6px;
  margin-bottom: 16px;
}

.post-detail__tag {
  background: var(--color-border-light);
  border-radius: 4px;
  color: var(--color-text-secondary);
  font-size: 12px;
  padding: 3px 10px;
}

.post-detail__stats {
  border-top: 1px solid var(--color-border);
  color: var(--color-text-secondary);
  display: flex;
  font-size: 14px;
  gap: 24px;
  padding-top: 16px;
}

@media (max-width: 780px) {
  .post-detail {
    padding: 20px;
  }

  .post-detail__title {
    font-size: 22px;
  }
}
</style>
