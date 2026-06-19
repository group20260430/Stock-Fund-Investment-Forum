<script setup>
import { timeAgo, formatCount, truncate } from '../../utils/format'
import AppIcon from '../common/AppIcon.vue'

const props = defineProps({
  post: {
    type: Object,
    required: true,
  },
})

const emit = defineEmits(['like', 'collect', 'share'])

function handleLike() {
  emit('like', props.post.id)
}

function handleCollect() {
  emit('collect', props.post.id)
}

function handleShare() {
  emit('share', props.post.id)
}
</script>

<template>
  <article class="post-card">
    <!-- 元信息行 -->
    <div class="post-card__meta">
      <span v-if="post.category" class="post-card__category">
        {{ typeof post.category === 'object' ? post.category.name : post.category }}
      </span>
      <span v-if="post.is_elite" class="post-card__badge post-card__badge--elite">精</span>
      <span class="post-card__author">
        {{ typeof post.author === 'object' ? post.author.nickname : post.author }}
      </span>
      <span class="dot">·</span>
      <span class="post-card__time">{{ timeAgo(post.created_at) }}</span>
    </div>

    <!-- 标题 -->
    <h3 class="post-card__title">
      <router-link :to="`/posts/${post.id}`">{{ post.title }}</router-link>
    </h3>

    <!-- 摘要 -->
    <p v-if="post.content_summary" class="post-card__summary">
      {{ truncate(post.content_summary, 120) }}
    </p>

    <!-- 标签 -->
    <div v-if="post.tags && post.tags.length" class="post-card__tags">
      <span v-for="tag in post.tags.slice(0, 3)" :key="tag" class="post-card__tag">{{ tag }}</span>
    </div>

    <!-- 统计 -->
    <div class="post-card__stats">
      <button
        :class="['stat-btn', { 'stat-btn--active': post.is_liked }]"
        @click.stop="handleLike"
      >
        <AppIcon :name="post.is_liked ? 'like' : 'like'" :solid="post.is_liked" :size="14" /> {{ formatCount(post.like_count || 0) }}
      </button>
      <span class="stat-item">
        <AppIcon name="comment" :size="14" /> {{ formatCount(post.comment_count || 0) }}
      </span>
      <button
        :class="['stat-btn', { 'stat-btn--active': post.is_collected }]"
        @click.stop="handleCollect"
      >
        <AppIcon :name="post.is_collected ? 'collect' : 'collect'" :solid="post.is_collected" :size="14" /> {{ formatCount(post.collect_count || 0) }}
      </button>
      <button class="stat-btn" @click.stop="handleShare">
        <AppIcon name="share" :size="14" /> {{ formatCount(post.share_count || 0) }}
      </button>
    </div>
  </article>
</template>

<style scoped>
.post-card {
  background: var(--color-bg-card);
  border: 1px solid var(--color-border);
  border-radius: 10px;
  box-shadow: 0 1px 2px rgba(15, 23, 42, 0.06);
  cursor: pointer;
  padding: 20px;
  transition: box-shadow 0.15s, transform 0.15s;
}

.post-card:hover {
  box-shadow: 0 4px 12px rgba(15, 23, 42, 0.08);
  transform: translateY(-1px);
}

.post-card__meta {
  align-items: center;
  color: var(--color-text-secondary);
  display: flex;
  flex-wrap: wrap;
  font-size: 13px;
  gap: 6px;
  margin-bottom: 8px;
}

.post-card__category {
  background: var(--color-primary-light);
  border-radius: 4px;
  color: var(--color-primary);
  font-weight: 500;
  padding: 2px 8px;
}

.post-card__badge {
  border-radius: 3px;
  font-size: 11px;
  font-weight: 700;
  padding: 2px 6px;
}

.post-card__badge--elite {
  background: var(--color-warning-light);
  color: var(--color-warning);
}

.dot {
  color: var(--color-border-input);
}

.post-card__title {
  font-size: 18px;
  font-weight: 600;
  line-height: 1.5;
  margin: 0 0 8px;
}

.post-card__title a {
  color: var(--color-text-primary);
  text-decoration: none;
}

.post-card__title a:hover {
  color: var(--color-primary);
}

.post-card__summary {
  color: var(--color-text-body);
  font-size: 14px;
  line-height: 1.7;
  margin: 0 0 10px;
}

.post-card__tags {
  display: flex;
  flex-wrap: wrap;
  gap: 6px;
  margin-bottom: 10px;
}

.post-card__tag {
  background: var(--color-border-light);
  border-radius: 4px;
  color: var(--color-text-secondary);
  font-size: 12px;
  padding: 2px 8px;
}

.post-card__stats {
  align-items: center;
  border-top: 1px solid var(--color-border-light);
  color: var(--color-text-secondary);
  display: flex;
  flex-wrap: wrap;
  font-size: 13px;
  gap: 16px;
  padding-top: 12px;
}

.stat-item {
  display: inline-flex;
  align-items: center;
  gap: 4px;
}

.stat-btn {
  align-items: center;
  background: none;
  border: 0;
  border-radius: 6px;
  color: var(--color-text-secondary);
  cursor: pointer;
  display: inline-flex;
  font: inherit;
  font-size: 13px;
  gap: 4px;
  padding: 4px 8px;
  transition: background 0.15s, color 0.15s;
}

.stat-btn:hover {
  background: var(--color-border-light);
  color: var(--color-primary);
}

.stat-btn--active {
  color: var(--color-primary);
}
</style>
