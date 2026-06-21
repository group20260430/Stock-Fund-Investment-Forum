<script setup>
import { ref, onMounted, reactive } from "vue"
import AppLayout from "../../components/layout/AppLayout.vue"
import Loading from "../../components/common/Loading.vue"
import EmptyState from "../../components/common/EmptyState.vue"
import Pagination from "../../components/common/Pagination.vue"
import { fetchReviewQueue, reviewItem } from "../../api/admin"
import { useToastStore } from "../../stores/toast"
import { timeAgo } from "../../utils/format"

const toast = useToastStore()

const items = ref([])
const loading = ref(true)
const pagination = reactive({ page: 1, size: 20, total: 0 })
const reviewComments = reactive({})
const reviewing = reactive({})

onMounted(async () => { await loadQueue() })

async function loadQueue(page = 1) {
  loading.value = true
  try {
    const data = await fetchReviewQueue({ page, size: 20, status: "pending" })
    items.value = data.items || []
    pagination.total = data.total || 0
    pagination.page = page
  } catch (err) {
    toast.error("加载审核队列失败")
    console.error("加载审核队列失败:", err.message)
  } finally {
    loading.value = false
  }
}

async function handleReview(id, action) {
  if (action === "reject" && !(reviewComments[id] || "").trim()) {
    toast.warning("拒绝时必须填写审核意见")
    return
  }
  reviewing[id] = true
  try {
    await reviewItem(id, action, reviewComments[id] || "")
    toast.success(action === "approve" ? "已通过" : "已拒绝")
    reviewComments[id] = ""
    // 从列表中移除
    items.value = items.value.filter(item => item.id !== id)
    pagination.total = Math.max(0, pagination.total - 1)
  } catch (err) {
    toast.error(err.message || "审核操作失败")
  } finally {
    reviewing[id] = false
  }
}

function handlePageChange(page) { loadQueue(page) }

// 获取审核项内容摘要
function contentSummary(item) {
  if (item.content) return item.content.length > 150 ? item.content.slice(0, 150) + "..." : item.content
  if (item.excerpt) return item.excerpt
  return ""
}

// 举报原因标签颜色
function flagClass(flag) {
  const map = { spam: "flag--spam", abuse: "flag--abuse", fake: "flag--fake", ad: "flag--ad", other: "flag--other" }
  return map[flag] || "flag--other"
}

function flagLabel(flag) {
  const map = { spam: "垃圾广告", abuse: "人身攻击", fake: "虚假信息", ad: "违规荐股", other: "其他" }
  return map[flag] || flag
}
</script>

<template>
  <AppLayout>
    <header class="toolbar">
      <h1>管理后台 / 内容审核</h1>
    </header>

    <div class="admin-nav">
      <router-link to="/admin" class="admin-nav__item">总览</router-link>
      <router-link to="/admin/review" class="admin-nav__item admin-nav__item--active">审核队列</router-link>
      <router-link to="/admin/users" class="admin-nav__item">用户管理</router-link>
    </div>

    <Loading v-if="loading" variant="skeleton" :rows="2" />

    <EmptyState
      v-else-if="!items.length"
      icon="✅"
      title="暂无待审核内容"
      description="所有内容已完成审核"
    />

    <div v-else class="review-list">
      <div v-for="item in items" :key="item.id" class="review-card">
        <div class="review-card__header">
          <span class="review-card__type">
            {{ item.content_type === "post" ? "📝 帖子" : item.content_type === "comment" ? "💬 评论" : "内容" }}
          </span>
          <span v-if="item.flags && item.flags.length" class="review-card__flags">
            <span
              v-for="flag in item.flags"
              :key="flag"
              :class="['flag-tag', flagClass(flag)]"
            >{{ flagLabel(flag) }}</span>
          </span>
          <span class="review-card__time">{{ timeAgo(item.submitted_at || item.created_at) }}</span>
        </div>

        <h4>{{ item.title || "评论内容" }}</h4>
        <p v-if="contentSummary(item)" class="review-card__content">{{ contentSummary(item) }}</p>
        <p v-if="item.author" class="review-card__author">
          作者：{{ typeof item.author === "object" ? item.author.nickname : item.author }}
        </p>

        <div class="review-card__actions">
          <input
            v-model="reviewComments[item.id]"
            type="text"
            :placeholder="'审核意见...'"
            class="review-input"
          >
          <div class="review-card__btns">
            <button
              class="review-btn review-btn--approve"
              :disabled="reviewing[item.id]"
              @click="handleReview(item.id, 'approve')"
            >{{ reviewing[item.id] ? "处理中..." : "✓ 通过" }}</button>
            <button
              class="review-btn review-btn--reject"
              :disabled="reviewing[item.id]"
              @click="handleReview(item.id, 'reject')"
            >{{ reviewing[item.id] ? "处理中..." : "✕ 拒绝" }}</button>
          </div>
        </div>
      </div>
    </div>

    <Pagination
      v-if="pagination.total > 20"
      :current="pagination.page"
      :total="pagination.total"
      :size="20"
      @update:current="handlePageChange"
    />
  </AppLayout>
</template>

<style scoped>
.toolbar { margin-bottom: 24px; }
.toolbar h1 { font-size: 24px; margin: 0; }

.admin-nav {
  background: var(--color-bg-card);
  border: 1px solid var(--color-border);
  border-radius: 8px;
  display: flex;
  gap: 0;
  margin-bottom: 24px;
  overflow: hidden;
}

.admin-nav__item {
  border-bottom: 2px solid transparent;
  color: var(--color-text-secondary);
  font-size: 14px;
  font-weight: 500;
  padding: 14px 24px;
  text-decoration: none;
}

.admin-nav__item:hover { color: var(--color-text-body); }
.admin-nav__item--active { border-bottom-color: var(--color-primary); color: var(--color-primary); }

.review-list { display: grid; gap: 14px; }

.review-card {
  background: var(--color-bg-card);
  border: 1px solid var(--color-border);
  border-left: 4px solid var(--color-warning);
  border-radius: 8px;
  padding: 20px;
}

.review-card__header {
  align-items: center;
  display: flex;
  flex-wrap: wrap;
  gap: 8px;
  margin-bottom: 8px;
}

.review-card__type {
  background: var(--color-primary-light);
  border-radius: var(--radius-sm);
  color: var(--color-primary);
  font-size: 12px;
  font-weight: 500;
  padding: 2px 8px;
}

.review-card__flags { display: flex; gap: 4px; flex-wrap: wrap; }

.flag-tag {
  border-radius: var(--radius-pill);
  font-size: 11px;
  font-weight: 600;
  padding: 2px 8px;
}

.flag--spam { background: #fef2f2; color: #dc2626; }
.flag--abuse { background: #fff7ed; color: #ea580c; }
.flag--fake { background: #fefce8; color: #ca8a04; }
.flag--ad { background: #eff6ff; color: #2563eb; }
.flag--other { background: var(--color-border-light); color: var(--color-text-secondary); }

.review-card__time { color: var(--color-text-muted); font-size: 12px; margin-left: auto; }

.review-card h4 { font-size: 16px; margin: 0 0 6px; }
.review-card__content { color: var(--color-text-secondary); font-size: 13px; line-height: 1.6; margin: 0 0 8px; }
.review-card__author { color: var(--color-text-muted); font-size: 13px; margin: 0 0 12px; }

.review-card__actions {
  align-items: center;
  border-top: 1px solid var(--color-border-light);
  display: flex;
  gap: 12px;
  padding-top: 12px;
}

.review-input {
  border: 1px solid var(--color-border-input);
  border-radius: 6px;
  flex: 1;
  font: inherit;
  font-size: 13px;
  padding: 8px 12px;
}

.review-input:focus {
  border-color: var(--color-primary);
  box-shadow: 0 0 0 3px var(--color-primary-ring);
  outline: none;
}

.review-card__btns { display: flex; gap: 6px; flex-shrink: 0; }

.review-btn {
  border: 0;
  border-radius: 6px;
  cursor: pointer;
  font: inherit;
  font-size: 13px;
  font-weight: 500;
  padding: 8px 18px;
  transition: opacity var(--duration-fast) var(--ease-out);
}

.review-btn:disabled { opacity: 0.6; cursor: not-allowed; }
.review-btn--approve { background: var(--color-success); color: var(--color-bg-card); }
.review-btn--approve:hover:not(:disabled) { background: var(--color-success-hover); }
.review-btn--reject { background: var(--color-danger); color: var(--color-bg-card); }
.review-btn--reject:hover:not(:disabled) { background: var(--color-danger-hover); }

@media (max-width: 780px) {
  .admin-nav__item { padding: 10px 14px; font-size: 13px; }
  .review-card__actions { flex-direction: column; align-items: stretch; }
  .review-card__btns { justify-content: flex-end; }
}
</style>
