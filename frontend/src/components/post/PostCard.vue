<script setup>
import { computed } from 'vue'
import { timeAgo, formatCount, truncate } from '../../utils/format'
import { extractImages } from '../../utils/markdown'
import AppIcon from '../common/AppIcon.vue'

const props = defineProps({
  post: {
    type: Object,
    required: true,
  },
})

const emit = defineEmits(['like', 'collect', 'share'])

// 从帖子内容中提取前 4 张图片（优先用后端预提取的 content_images）
const imageInfo = computed(() => {
  // 后端已在列表接口中预提取 content_images，包含 urls 和 total
  if (props.post.content_images) {
    return props.post.content_images
  }
  // 兜底：前端自行提取（详情页等场景传了完整 content）
  return extractImages(props.post.content || props.post.content_summary || '', 4)
})

const authorProfileUrl = computed(() => {
  const author = props.post.author
  if (author && typeof author === 'object' && author.id) {
    return `/users/${author.id}`
  }
  return ''
})

const authorName = computed(() => {
  return typeof props.post.author === 'object' ? props.post.author.nickname : props.post.author
})

const authorAvatar = computed(() => {
  if (typeof props.post.author === 'object') {
    return props.post.author.avatar_url || ''
  }
  return ''
})

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
      <!-- 作者头像 -->
      <router-link
        v-if="authorProfileUrl"
        :to="authorProfileUrl"
        class="post-card__author-link"
        @click.stop
      >
        <img
          v-if="authorAvatar"
          :src="authorAvatar"
          :alt="authorName"
          class="post-card__author-avatar"
          @error="$event.target.style.display = 'none'"
        >
        <span
          v-else
          class="post-card__author-avatar post-card__author-avatar--placeholder"
          :title="authorName"
        >
          {{ authorName?.charAt(0) || '?' }}
        </span>
      </router-link>
      <template v-else>
        <img
          v-if="authorAvatar"
          :src="authorAvatar"
          :alt="authorName"
          class="post-card__author-avatar"
          @error="$event.target.style.display = 'none'"
        >
        <span
          v-else
          class="post-card__author-avatar post-card__author-avatar--placeholder"
          :title="authorName"
        >
          {{ authorName?.charAt(0) || '?' }}
        </span>
      </template>

      <span v-if="post.category" class="post-card__category">
        {{ typeof post.category === 'object' ? post.category.name : post.category }}
      </span>
      <span v-if="post.is_elite" class="post-card__badge post-card__badge--elite">精</span>
      <span class="post-card__author">
        <router-link v-if="authorProfileUrl" :to="authorProfileUrl" class="post-card__author-name" @click.stop>{{ authorName }}</router-link>
        <template v-else>{{ authorName }}</template>
      </span>
      <span class="dot">·</span>
      <span class="post-card__time">{{ timeAgo(post.created_at) }}</span>
    </div>

    <!-- 分享来源提示 -->
    <div v-if="post.shared_by" class="post-card__shared-by">
      <AppIcon name="share" :size="12" />
      {{ post.shared_by === '__self__' ? '你分享了这篇帖子' : post.shared_by + ' 分享了这篇帖子' }}
    </div>

    <!-- 标题 -->
    <h3 class="post-card__title">
      <router-link :to="`/posts/${post.id}`">{{ post.title }}</router-link>
    </h3>

    <!-- 摘要 -->
    <p v-if="post.content_summary" class="post-card__summary">
      {{ truncate(post.content_summary, 120) }}
    </p>

    <!-- 图片预览网格 -->
    <div v-if="imageInfo.urls.length" class="post-card__images">
      <div class="post-card__images-grid">
        <div
          v-for="(url, idx) in imageInfo.urls"
          :key="idx"
          class="post-card__image-cell"
        >
          <img :src="url" :alt="'图片 ' + (idx + 1)" loading="lazy" />
        </div>
      </div>
      <span class="post-card__images-count">共 {{ imageInfo.total }} 张</span>
    </div>

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
      <button class="stat-btn" @click.stop="$router.push('/posts/' + post.id + '#comments')">
        <AppIcon name="comment" :size="14" /> {{ formatCount(post.comment_count || 0) }}
      </button>
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

.post-card__author-avatar {
  border-radius: 50%;
  flex-shrink: 0;
  height: 22px;
  object-fit: cover;
  width: 22px;
}

.post-card__author-avatar--placeholder {
  align-items: center;
  background: var(--color-border);
  color: var(--color-text-muted);
  display: inline-flex;
  font-size: 10px;
  font-weight: 700;
  justify-content: center;
}

.post-card__author-link {
  display: inline-flex;
  flex-shrink: 0;
}

.post-card__author-name {
  color: var(--color-text-secondary);
  font-weight: 500;
  text-decoration: none;
}

.post-card__author-name:hover {
  color: var(--color-primary);
  text-decoration: underline;
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

.post-card__shared-by {
  align-items: center;
  color: var(--color-primary);
  display: flex;
  font-size: 12px;
  gap: 4px;
  margin-bottom: 6px;
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

/* 图片预览网格 */
.post-card__images {
  margin-bottom: 10px;
  position: relative;
}

.post-card__images-grid {
  display: grid;
  gap: 4px;
  grid-template-columns: repeat(4, 1fr);
}

.post-card__image-cell {
  aspect-ratio: 1 / 1;
  border-radius: 6px;
  overflow: hidden;
}

.post-card__image-cell img {
  display: block;
  height: 100%;
  object-fit: cover;
  width: 100%;
}

.post-card__images-count {
  background: rgba(0, 0, 0, 0.55);
  border-radius: 4px;
  color: #fff;
  font-size: 11px;
  font-weight: 700;
  padding: 2px 8px;
  position: absolute;
  right: 4px;
  top: 4px;
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
