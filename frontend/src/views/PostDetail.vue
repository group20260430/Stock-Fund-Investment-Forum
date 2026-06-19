<script setup>
import { ref, onMounted } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { useAuthStore } from '../stores/auth'
import { usePostsStore } from '../stores/posts'
import { fetchComments, createComment } from '../api/comments'
import AppLayout from '../components/layout/AppLayout.vue'
import PostDetailComponent from '../components/post/PostDetail.vue'
import CommentList from '../components/comment/CommentList.vue'
import Loading from '../components/common/Loading.vue'
import ErrorState from '../components/common/ErrorState.vue'
import Pagination from '../components/common/Pagination.vue'

const route = useRoute()
const router = useRouter()
const auth = useAuthStore()
const postsStore = usePostsStore()

const comments = ref([])
const commentsPage = ref(1)
const commentsTotal = ref(0)
const commentsLoading = ref(false)
const commentText = ref('')
const submittingComment = ref(false)

onMounted(async () => {
  const id = route.params.id
  await postsStore.loadPostDetail(id)
  if (postsStore.currentPost) {
    await loadComments()
  }
})

async function loadComments(page = 1) {
  commentsLoading.value = true
  try {
    const data = await fetchComments(route.params.id, { page, size: 20 })
    comments.value = data.items || []
    commentsTotal.value = data.total || 0
    commentsPage.value = page
  } catch (err) {
    console.error('加载评论失败:', err.message)
  } finally {
    commentsLoading.value = false
  }
}

async function handleSubmitComment() {
  if (!commentText.value.trim() || submittingComment.value) return
  submittingComment.value = true
  try {
    await createComment(route.params.id, { content: commentText.value.trim() })
    commentText.value = ''
    await loadComments(1)
    // 更新帖子评论数
    if (postsStore.currentPost) {
      postsStore.currentPost.comment_count = (postsStore.currentPost.comment_count || 0) + 1
    }
  } catch (err) {
    console.error('评论失败:', err.message)
  } finally {
    submittingComment.value = false
  }
}

async function handleReply(data) {
  if (submittingComment.value) return
  submittingComment.value = true
  try {
    await createComment(route.params.id, {
      content: data.content,
      parent_id: data.parentId,
      reply_to_id: data.replyToId,
    })
    await loadComments(commentsPage.value)
  } catch (err) {
    console.error('回复失败:', err.message)
  } finally {
    submittingComment.value = false
  }
}

async function handleLikePost() {
  if (!auth.isLoggedIn) return
  await postsStore.togglePostLike(route.params.id)
}

async function handleCollectPost() {
  if (!auth.isLoggedIn) return
  await postsStore.togglePostCollect(route.params.id)
}

async function handleCommentLike(commentId) {
  if (!auth.isLoggedIn) return
  try {
    const { likeComment } = await import('../api/comments')
    await likeComment(commentId)
    // 简化：重载评论
    await loadComments(commentsPage.value)
  } catch (err) {
    console.error('点赞评论失败:', err.message)
  }
}

function handleCommentsPageChange(page) {
  loadComments(page)
  // 滚动到评论区
  document.querySelector('.comments-section')?.scrollIntoView({ behavior: 'smooth' })
}

const post = postsStore.currentPost
</script>

<template>
  <AppLayout>
    <!-- 加载态 -->
    <Loading v-if="postsStore.loading && !post" variant="skeleton" :rows="1" />

    <!-- 错误态 -->
    <ErrorState
      v-else-if="postsStore.error && !post"
      :message="postsStore.error"
      @retry="postsStore.loadPostDetail(route.params.id)"
    />

    <!-- 帖子不存在 -->
    <ErrorState
      v-else-if="!post"
      message="帖子不存在或已被删除"
    />

    <!-- 帖子内容 -->
    <template v-else>
      <!-- 返回按钮 -->
      <button class="back-btn" @click="router.back()">&larr; 返回</button>

      <PostDetailComponent :post="post" />

      <!-- 互动操作栏 -->
      <div class="action-bar">
        <button
          :class="['action-btn', { 'action-btn--active': post.is_liked }]"
          @click="handleLikePost"
        >
          👍 {{ post.like_count || 0 }}
        </button>
        <button
          :class="['action-btn', { 'action-btn--active': post.is_collected }]"
          @click="handleCollectPost"
        >
          ⭐ {{ post.collect_count || 0 }}
        </button>
        <button class="action-btn">
          ↗ {{ post.share_count || 0 }}
        </button>
        <button class="action-btn" @click="router.push(`/posts/${post.id}#comments`)">
          💬 {{ post.comment_count || 0 }}
        </button>
      </div>

      <!-- 评论区 -->
      <section id="comments" class="comments-section">
        <h3>{{ commentsTotal }} 条评论</h3>

        <!-- 发表评论 -->
        <div v-if="auth.isLoggedIn" class="comment-form">
          <textarea
            v-model="commentText"
            placeholder="发表评论..."
            rows="3"
            class="comment-form__textarea"
            maxlength="2000"
          />
          <div class="comment-form__footer">
            <span class="comment-form__hint">{{ commentText.length }}/2000</span>
            <button
              class="comment-form__submit"
              :disabled="!commentText.trim() || submittingComment"
              @click="handleSubmitComment"
            >
              {{ submittingComment ? '提交中...' : '发表评论' }}
            </button>
          </div>
        </div>
        <div v-else class="comment-login-hint">
          <router-link :to="`/login?redirect=/posts/${route.params.id}`">登录</router-link>
          后即可参与评论
        </div>

        <!-- 评论列表 -->
        <CommentList
          :comments="comments"
          :loading="commentsLoading"
          @reply="handleReply"
          @like="handleCommentLike"
        />

        <Pagination
          v-if="commentsTotal > 20"
          :current="commentsPage"
          :total="commentsTotal"
          :size="20"
          @update:current="handleCommentsPageChange"
        />
      </section>
    </template>
  </AppLayout>
</template>

<style scoped>
.back-btn {
  background: none;
  border: 0;
  color: var(--color-text-secondary);
  cursor: pointer;
  font: inherit;
  font-size: 14px;
  margin-bottom: 16px;
  padding: 4px 0;
}

.back-btn:hover {
  color: var(--color-primary);
}

/* 操作栏 */
.action-bar {
  background: var(--color-bg-card);
  border: 1px solid var(--color-border);
  border-radius: 10px;
  display: flex;
  gap: 8px;
  margin-bottom: 32px;
  padding: 12px 20px;
}

.action-btn {
  align-items: center;
  background: none;
  border: 0;
  border-radius: 8px;
  color: var(--color-text-secondary);
  cursor: pointer;
  display: inline-flex;
  font: inherit;
  font-size: 15px;
  gap: 6px;
  padding: 8px 16px;
  transition: background 0.15s, color 0.15s;
}

.action-btn:hover {
  background: var(--color-border-light);
  color: var(--color-primary);
}

.action-btn--active {
  color: var(--color-primary);
}

/* 评论区 */
.comments-section {
  background: var(--color-bg-card);
  border: 1px solid var(--color-border);
  border-radius: 10px;
  padding: 24px;
}

.comments-section h3 {
  font-size: 18px;
  margin: 0 0 20px;
}

.comment-form {
  margin-bottom: 24px;
}

.comment-form__textarea {
  border: 1px solid var(--color-border-input);
  border-radius: 8px;
  font: inherit;
  font-size: 14px;
  padding: 12px 14px;
  resize: vertical;
  width: 100%;
}

.comment-form__textarea:focus {
  border-color: var(--color-primary);
  box-shadow: 0 0 0 3px var(--color-primary-ring);
  outline: none;
}

.comment-form__footer {
  align-items: center;
  display: flex;
  justify-content: space-between;
  margin-top: 8px;
}

.comment-form__hint {
  color: var(--color-text-muted);
  font-size: 12px;
}

.comment-form__submit {
  background: var(--color-primary);
  border: 0;
  border-radius: 6px;
  color: var(--color-bg-card);
  cursor: pointer;
  font: inherit;
  font-size: 13px;
  padding: 8px 20px;
}

.comment-form__submit:hover:not(:disabled) {
  background: var(--color-primary-hover);
}

.comment-form__submit:disabled {
  opacity: 0.5;
  cursor: not-allowed;
}

.comment-login-hint {
  color: var(--color-text-muted);
  font-size: 14px;
  margin-bottom: 24px;
  text-align: center;
}

.comment-login-hint a {
  color: var(--color-primary);
  text-decoration: none;
}

@media (max-width: 780px) {
  .action-bar {
    gap: 4px;
    padding: 10px 12px;
  }

  .action-btn {
    font-size: 13px;
    padding: 6px 10px;
  }
}
</style>
