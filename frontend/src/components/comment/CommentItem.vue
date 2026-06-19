<script setup>
import { ref } from 'vue'
import { timeAgo, formatCount } from '../../utils/format'
import { useAuthStore } from '../../stores/auth'
import AppIcon from '../common/AppIcon.vue'

const props = defineProps({
  comment: { type: Object, required: true },
  depth: { type: Number, default: 0 },
})

const emit = defineEmits(['reply', 'like'])
const auth = useAuthStore()

const showReplies = ref(false)
const showReplyBox = ref(false)
const replyContent = ref('')
const maxReplyDepth = 2 // 最多嵌套层级

function handleLike() {
  emit('like', props.comment.id)
}

function handleReply() {
  if (replyContent.value.trim()) {
    emit('reply', {
      parentId: props.comment.id,
      replyToId: props.comment.author?.id,
      replyToName: typeof props.comment.author === 'object'
        ? props.comment.author.nickname
        : props.comment.author,
      content: replyContent.value.trim(),
    })
    replyContent.value = ''
    showReplyBox.value = false
  }
}

function toggleReplies() {
  showReplies.value = !showReplies.value
}

const authorName = typeof props.comment.author === 'object'
  ? props.comment.author.nickname
  : props.comment.author

const authorAvatar = typeof props.comment.author === 'object'
  ? props.comment.author.avatar_url
  : null

const replyToName = props.comment.reply_to && (typeof props.comment.reply_to === 'object'
  ? props.comment.reply_to.nickname
  : props.comment.reply_to)
</script>

<template>
  <div :class="['comment-item', { 'comment-item--nested': depth > 0 }]">
    <!-- 主体 -->
    <div class="comment-item__body">
      <img
        :src="authorAvatar || ''"
        :alt="authorName"
        class="comment-item__avatar"
        @error="$event.target.src = 'data:image/svg+xml,%3Csvg xmlns=%22http://www.w3.org/2000/svg%22 viewBox=%220 0 40 40%22%3E%3Ccircle fill=%22%23d1d5db%22 cx=%2220%22 cy=%2220%22 r=%2220%22/%3E%3C/svg%3E'"
      >
      <div class="comment-item__content">
        <div class="comment-item__header">
          <strong>{{ authorName }}</strong>
          <span
            v-if="comment.author?.auth_level === 'professional'"
            class="auth-badge auth-badge--pro"
            title="专业认证"
          >V</span>
          <span
            v-else-if="comment.author?.auth_level === 'verified'"
            class="auth-badge auth-badge--verified"
            title="实名认证"
          >V</span>
          <span class="comment-item__time">{{ timeAgo(comment.created_at) }}</span>
        </div>

        <p class="comment-item__text">
          <span v-if="replyToName" class="reply-to">@{{ replyToName }}</span>
          {{ comment.content }}
        </p>

        <div class="comment-item__actions">
          <button
            :class="['action-btn', { 'action-btn--active': comment.is_liked }]"
            @click="handleLike"
          >
            <AppIcon :name="comment.is_liked ? 'like' : 'like'" :solid="comment.is_liked" :size="12" /> {{ formatCount(comment.like_count || 0) }}
          </button>
          <button
            v-if="auth.isLoggedIn && depth < maxReplyDepth"
            class="action-btn"
            @click="showReplyBox = !showReplyBox"
          >
            <AppIcon name="reply" :size="12" /> 回复
          </button>
        </div>

        <!-- 回复框 -->
        <div v-if="showReplyBox" class="reply-box">
          <textarea
            v-model="replyContent"
            :placeholder="`回复 @${authorName}...`"
            rows="3"
            class="reply-box__textarea"
          />
          <div class="reply-box__actions">
            <button class="reply-box__submit" @click="handleReply">回复</button>
            <button class="reply-box__cancel" @click="showReplyBox = false">取消</button>
          </div>
        </div>
      </div>
    </div>

    <!-- 楼中楼回复 -->
    <div v-if="comment.replies && comment.replies.length" class="comment-item__replies">
      <template v-if="showReplies">
        <CommentItem
          v-for="reply in comment.replies"
          :key="reply.id"
          :comment="reply"
          :depth="depth + 1"
          @reply="emit('reply', $event)"
          @like="emit('like', $event)"
        />
      </template>
      <button v-if="!showReplies" class="expand-btn" @click="toggleReplies">
        ── 展开 {{ comment.reply_count || comment.replies.length }} 条回复 ──
      </button>
      <button v-else class="expand-btn" @click="toggleReplies">
        ── 收起回复 ──
      </button>
    </div>
  </div>
</template>

<style scoped>
.comment-item {
  padding: 16px 0;
}

.comment-item + .comment-item {
  border-top: 1px solid var(--color-border-light);
}

.comment-item--nested {
  margin-left: 40px;
  padding-left: 16px;
  border-left: 2px solid var(--color-border);
}

.comment-item__body {
  display: flex;
  gap: 12px;
}

.comment-item__avatar {
  border-radius: 50%;
  flex-shrink: 0;
  height: 36px;
  object-fit: cover;
  width: 36px;
}

.comment-item__content {
  flex: 1;
  min-width: 0;
}

.comment-item__header {
  align-items: center;
  display: flex;
  flex-wrap: wrap;
  gap: 6px;
  margin-bottom: 4px;
}

.comment-item__header strong {
  font-size: 14px;
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

.comment-item__time {
  color: var(--color-text-muted);
  font-size: 12px;
}

.comment-item__text {
  color: var(--color-text-body);
  font-size: 14px;
  line-height: 1.7;
  margin: 0;
  word-break: break-word;
}

.reply-to {
  color: var(--color-info);
  margin-right: 4px;
}

.comment-item__actions {
  display: flex;
  gap: 12px;
  margin-top: 8px;
}

.action-btn {
  align-items: center;
  background: none;
  border: 0;
  border-radius: 4px;
  color: var(--color-text-muted);
  cursor: pointer;
  display: inline-flex;
  font: inherit;
  font-size: 12px;
  gap: 4px;
  padding: 2px 6px;
}

.action-btn:hover {
  color: var(--color-primary);
}

.action-btn--active {
  color: var(--color-primary);
}

.reply-box {
  margin-top: 10px;
}

.reply-box__textarea {
  border: 1px solid var(--color-border-input);
  border-radius: 8px;
  font: inherit;
  font-size: 13px;
  padding: 10px 12px;
  resize: vertical;
  width: 100%;
}

.reply-box__textarea:focus {
  border-color: var(--color-primary);
  box-shadow: 0 0 0 3px var(--color-primary-ring);
  outline: none;
}

.reply-box__actions {
  display: flex;
  gap: 8px;
  justify-content: flex-end;
  margin-top: 8px;
}

.reply-box__submit {
  background: var(--color-primary);
  border: 0;
  border-radius: 6px;
  color: var(--color-bg-card);
  cursor: pointer;
  font: inherit;
  font-size: 12px;
  padding: 6px 14px;
}

.reply-box__cancel {
  background: var(--color-bg-card);
  border: 1px solid var(--color-border-input);
  border-radius: 6px;
  color: var(--color-text-secondary);
  cursor: pointer;
  font: inherit;
  font-size: 12px;
  padding: 6px 14px;
}

.comment-item__replies {
  margin-top: 8px;
}

.expand-btn {
  background: none;
  border: 0;
  color: var(--color-primary);
  cursor: pointer;
  font: inherit;
  font-size: 13px;
  margin-top: 8px;
  padding: 4px 0;
}

.expand-btn:hover {
  text-decoration: underline;
}
</style>
