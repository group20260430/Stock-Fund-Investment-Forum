<script setup>
import { ref, computed, onMounted } from "vue"
import { useRoute, useRouter } from "vue-router"
import { useAuthStore } from "../stores/auth"
import { usePostsStore } from "../stores/posts"
import { useToastStore } from "../stores/toast"
import { fetchComments, createComment, deleteComment, likeComment } from "../api/comments"
import { sharePost } from "../api/posts"
import { submitReport } from "../api/admin"
import AppLayout from "../components/layout/AppLayout.vue"
import PostDetailComponent from "../components/post/PostDetail.vue"
import CommentList from "../components/comment/CommentList.vue"
import MentionTextarea from "../components/common/MentionTextarea.vue"
import Loading from "../components/common/Loading.vue"
import ErrorState from "../components/common/ErrorState.vue"
import Pagination from "../components/common/Pagination.vue"
import AppIcon from "../components/common/AppIcon.vue"

const route = useRoute()
const router = useRouter()
const auth = useAuthStore()
const postsStore = usePostsStore()
const toast = useToastStore()

const comments = ref([])
const commentsPage = ref(1)
const commentsTotal = ref(0)
const commentsLoading = ref(false)
const commentText = ref("")
const submittingComment = ref(false)
const sharing = ref(false)

// 举报
const showReport = ref(false)
const reportReason = ref("")
const reportComment = ref("")
const reporting = ref(false)
const reportReasons = [
  { value: "fake", label: "虚假信息" },
  { value: "abuse", label: "人身攻击" },
  { value: "ad", label: "违规荐股" },
  { value: "spam", label: "垃圾广告" },
  { value: "other", label: "其他" },
]

onMounted(async () => {
  const id = route.params.id
  await postsStore.loadPostDetail(id)
  if (postsStore.currentPost) { await loadComments() }
})

async function loadComments(page = 1) {
  commentsLoading.value = true
  try {
    const data = await fetchComments(route.params.id, { page, size: 20 })
    comments.value = data.items || []
    commentsTotal.value = data.total || 0
    commentsPage.value = page
  } catch (err) {
    console.error("加载评论失败:", err.message)
  } finally {
    commentsLoading.value = false
  }
}

async function handleSubmitComment() {
  if (!commentText.value.trim() || submittingComment.value) return
  submittingComment.value = true
  try {
    await createComment(route.params.id, { content: commentText.value.trim() })
    commentText.value = ""
    toast.success("评论发表成功")
    await loadComments(1)
    if (postsStore.currentPost) {
      postsStore.currentPost.comment_count = (postsStore.currentPost.comment_count || 0) + 1
    }
  } catch (err) {
    toast.error(err.message || "评论失败")
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
    toast.success("回复发表成功")
    await loadComments(commentsPage.value)
  } catch (err) {
    toast.error(err.message || "回复失败")
  } finally {
    submittingComment.value = false
  }
}

async function handleCommentDelete(commentId) {
  comments.value = comments.value.filter(c => c.id !== commentId)
  function removeNested(list) {
    return list.filter(c => { if (c.replies) c.replies = removeNested(c.replies); return c.id !== commentId })
  }
  comments.value = removeNested(comments.value)
  if (postsStore.currentPost && postsStore.currentPost.comment_count > 0) {
    postsStore.currentPost.comment_count -= 1
  }
}

async function handleSubmitReport() {
  if (!reportReason.value || reporting.value) return
  reporting.value = true
  try {
    await submitReport({
      target_type: "post",
      target_id: route.params.id,
      reason: reportReason.value,
      comment: reportComment.value.trim(),
    })
    toast.success("举报已提交，感谢您的反馈")
    showReport.value = false
    reportReason.value = ""
    reportComment.value = ""
  } catch (err) {
    toast.error(err.message || "举报失败")
  } finally {
    reporting.value = false
  }
}

async function handleLikePost() {
  if (!auth.isLoggedIn) return
  const id = Number(route.params.id)
  await postsStore.togglePostLike(id)
}

async function handleCollectPost() {
  if (!auth.isLoggedIn) return
  const id = Number(route.params.id)
  await postsStore.togglePostCollect(id)
}

async function handleShare() {
  if (!auth.isLoggedIn) { toast.info('请先登录'); return }
  if (sharing.value) return
  sharing.value = true
  try {
    const data = await sharePost(route.params.id, 'timeline', '')
    if (postsStore.currentPost) {
      postsStore.currentPost.share_count = data.share_count || (postsStore.currentPost.share_count || 0) + 1
    }
    toast.success('已转发到动态')
  } catch (err) {
    toast.error(err.message || '转发失败')
  } finally {
    sharing.value = false
  }
}

async function handleReport() {
  if (!auth.isLoggedIn) { toast.info('请先登录'); return }
  if (!reportReason.value.trim()) { toast.warning('请填写举报原因'); return }
  reporting.value = true
  try {
    await submitReport({
      target_type: 'post',
      target_id: Number(route.params.id),
      reason: reportReason.value.trim(),
    })
    toast.success('举报已提交，我们会尽快处理')
    showReport.value = false
    reportReason.value = ''
  } catch (err) {
    toast.error(err.message || '举报失败')
  } finally {
    reporting.value = false
  }
}

async function handleCommentLike(commentId) {
  if (!auth.isLoggedIn) return
  try {
    await likeComment(commentId)
    await loadComments(commentsPage.value)
  } catch (err) {
    console.error("点赞评论失败:", err.message)
  }
}

function handleCommentsPageChange(page) {
  loadComments(page)
  document.querySelector(".comments-section")?.scrollIntoView({ behavior: "smooth" })
}

const post = computed(() => postsStore.currentPost)
</script>

<template>
  <AppLayout>
    <Loading v-if="postsStore.loading && !post" variant="skeleton" :rows="1" />
    <ErrorState v-else-if="postsStore.error && !post" :message="postsStore.error" @retry="postsStore.loadPostDetail(route.params.id)" />
    <ErrorState v-else-if="!post" message="帖子不存在或已被删除" />

    <template v-else>
      <button class="back-btn" @click="router.back()">&larr; 返回</button>
      <PostDetailComponent :post="post" />

      <div class="action-bar">
        <button :class="['action-btn', { 'action-btn--active': post.is_liked }]" @click="handleLikePost">
          <AppIcon name="like" :solid="post.is_liked" :size="18" />
          <span>{{ post.like_count || 0 }}</span>
        </button>
        <button :class="['action-btn', { 'action-btn--active': post.is_collected }]" @click="handleCollectPost">
          <AppIcon name="collect" :solid="post.is_collected" :size="18" />
          <span>{{ post.collect_count || 0 }}</span>
        </button>
        <button class="action-btn" :disabled="sharing" @click="handleShare">
          <AppIcon name="share" :size="18" />
          <span>{{ post.share_count || 0 }}</span>
        </button>
        <button class="action-btn" @click="router.push('/posts/' + post.id + '#comments')">
          <AppIcon name="comment" :size="18" />
          <span>{{ post.comment_count || 0 }}</span>
        </button>
        <button v-if="auth.isLoggedIn" class="action-btn action-btn--report" @click="showReport = !showReport">
          <AppIcon name="flag" :size="16" />
          <span>举报</span>
        </button>
      </div>

      <!-- 举报弹窗 -->
      <div v-if="showReport" class="report-dialog">
        <h4>举报帖子</h4>
        <div class="report-dialog__reasons">
          <label v-for="r in reportReasons" :key="r.value" :class="['report-reason', { 'report-reason--active': reportReason === r.value }]">
            <input v-model="reportReason" type="radio" :value="r.value" />
            {{ r.label }}
          </label>
        </div>
        <textarea v-model="reportComment" placeholder="补充说明（可选）" class="report-dialog__comment" rows="2" maxlength="500" />
        <div class="report-dialog__actions">
          <button class="report-dialog__cancel" @click="showReport = false">取消</button>
          <button class="report-dialog__submit" :disabled="!reportReason || reporting" @click="handleSubmitReport">{{ reporting ? "提交中..." : "提交举报" }}</button>
        </div>
      </div>

      <section id="comments" class="comments-section">
        <h3>{{ commentsTotal }} 条评论</h3>

        <div v-if="auth.isLoggedIn" class="comment-form">
          <MentionTextarea v-model="commentText" placeholder="发表评论... 输入 @ 可以提及用户" :rows="3" :maxlength="2000" @submit="handleSubmitComment" />
          <div class="comment-form__footer">
            <span class="comment-form__hint">{{ commentText.length }}/2000</span>
            <button class="comment-form__submit" :disabled="!commentText.trim() || submittingComment" @click="handleSubmitComment">{{ submittingComment ? "提交中..." : "发表评论" }}</button>
          </div>
        </div>
        <div v-else class="comment-login-hint">
          <router-link :to="'/login?redirect=/posts/' + route.params.id">登录</router-link> 后即可参与评论
        </div>

        <CommentList :comments="comments" :loading="commentsLoading" @reply="handleReply" @like="handleCommentLike" @delete="handleCommentDelete" />

        <Pagination v-if="commentsTotal > 20" :current="commentsPage" :total="commentsTotal" :size="20" @update:current="handleCommentsPageChange" />
      </section>
    </template>
  </AppLayout>
</template>

<style scoped>
.back-btn { background: none; border: 0; color: var(--color-text-secondary); cursor: pointer; font: inherit; font-size: 14px; margin-bottom: 16px; padding: 4px 0; }
.back-btn:hover { color: var(--color-primary); }
.action-bar { background: var(--color-bg-card); border: 1px solid var(--color-border); border-radius: 10px; display: flex; gap: 8px; margin-bottom: 16px; padding: 12px 20px; }
.action-btn { align-items: center; background: none; border: 0; border-radius: 8px; color: var(--color-text-secondary); cursor: pointer; display: inline-flex; font: inherit; font-size: 15px; gap: 6px; padding: 8px 16px; transition: background 0.15s, color 0.15s; }
.action-btn:hover { background: var(--color-border-light); color: var(--color-primary); }
.action-btn--active { color: var(--color-primary); font-weight: 600; }
.action-btn--report { margin-left: auto; color: var(--color-text-muted); font-size: 14px; }
.report-dialog {
  background: var(--color-bg-card);
  border: 1px solid var(--color-border);
  border-radius: var(--radius-xl);
  margin-bottom: 20px;
  padding: 24px;
}
.report-dialog h4 { font-size: var(--font-size-lg); margin: 0 0 16px; }
.report-dialog__reasons { display: flex; flex-wrap: wrap; gap: 8px; margin-bottom: 16px; }
.report-reason {
  align-items: center;
  background: var(--color-bg-hover);
  border: 1px solid var(--color-border-light);
  border-radius: var(--radius-pill);
  cursor: pointer;
  display: flex;
  font-size: var(--font-size-sm);
  gap: 6px;
  padding: 6px 14px;
  transition: all var(--duration-fast) var(--ease-out);
}
.report-reason:hover { border-color: var(--color-primary); }
.report-reason--active { background: var(--color-danger-light); border-color: var(--color-danger); color: var(--color-danger); }
.report-dialog__comment {
  border: 1px solid var(--color-border-input);
  border-radius: var(--radius-lg);
  font: inherit;
  font-size: var(--font-size-sm);
  margin-bottom: 16px;
  padding: 10px 12px;
  resize: vertical;
  width: 100%;
}
.report-dialog__comment:focus { border-color: var(--color-primary); box-shadow: 0 0 0 3px var(--color-primary-ring); outline: none; }
.report-dialog__actions { display: flex; gap: 8px; justify-content: flex-end; }
.report-dialog__cancel {
  background: var(--color-bg-card);
  border: 1px solid var(--color-border-input);
  border-radius: var(--radius-lg);
  color: var(--color-text-secondary);
  cursor: pointer;
  font: inherit;
  font-size: var(--font-size-sm);
  padding: 8px 20px;
}
.report-dialog__cancel:hover { background: var(--color-bg-hover); }
.report-dialog__submit {
  background: var(--color-danger);
  border: 0;
  border-radius: var(--radius-lg);
  color: var(--color-bg-card);
  cursor: pointer;
  font: inherit;
  font-size: var(--font-size-sm);
  font-weight: var(--font-weight-medium);
  padding: 8px 20px;
}
.report-dialog__submit:hover:not(:disabled) { background: var(--color-danger-hover); }
.report-dialog__submit:disabled { opacity: 0.5; cursor: not-allowed; }

.comments-section { background: var(--color-bg-card); border: 1px solid var(--color-border); border-radius: 10px; padding: 24px; }
.comments-section h3 { font-size: 18px; margin: 0 0 20px; }
.comment-form { margin-bottom: 24px; }
.comment-form__footer { align-items: center; display: flex; justify-content: space-between; margin-top: 8px; }
.comment-form__hint { color: var(--color-text-muted); font-size: 12px; }
.comment-form__submit { background: var(--color-primary); border: 0; border-radius: 6px; color: var(--color-bg-card); cursor: pointer; font: inherit; font-size: 13px; padding: 8px 20px; }
.comment-form__submit:hover:not(:disabled) { background: var(--color-primary-hover); }
.comment-form__submit:disabled { opacity: 0.5; cursor: not-allowed; }
.comment-login-hint { color: var(--color-text-muted); font-size: 14px; margin-bottom: 24px; text-align: center; }
.comment-login-hint a { color: var(--color-primary); text-decoration: none; }
@media (max-width: 780px) {
  .action-bar { gap: 4px; padding: 10px 12px; }
  .action-btn { font-size: 13px; padding: 6px 10px; }
}
</style>
