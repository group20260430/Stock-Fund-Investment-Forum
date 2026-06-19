<script setup>
import { ref, onMounted, reactive } from 'vue'
import AppLayout from '../../components/layout/AppLayout.vue'
import Loading from '../../components/common/Loading.vue'
import EmptyState from '../../components/common/EmptyState.vue'
import Pagination from '../../components/common/Pagination.vue'
import { fetchReviewQueue, reviewItem } from '../../api/admin'
import { timeAgo } from '../../utils/format'

const items = ref([])
const loading = ref(true)
const pagination = reactive({ page: 1, size: 20, total: 0 })
const reviewComment = ref('')

onMounted(async () => {
  await loadQueue()
})

async function loadQueue(page = 1) {
  loading.value = true
  try {
    const data = await fetchReviewQueue({ page, size: 20, status: 'pending' })
    items.value = data.items || []
    pagination.total = data.total || 0
    pagination.page = page
  } catch (err) {
    console.error('加载审核队列失败:', err.message)
  } finally {
    loading.value = false
  }
}

async function handleReview(id, action) {
  try {
    await reviewItem(id, action, reviewComment.value)
    reviewComment.value = ''
    await loadQueue(pagination.page)
  } catch (err) {
    console.error('审核操作失败:', err.message)
  }
}

function handlePageChange(page) { loadQueue(page) }
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
          <span class="review-card__type">{{ item.content_type === 'post' ? '帖子' : '评论' }}</span>
          <span class="review-card__flags" v-if="item.flags">
            ⚠️ {{ item.flags.join(', ') }}
          </span>
          <span class="review-card__time">{{ timeAgo(item.submitted_at) }}</span>
        </div>
        <h4>{{ item.title || '评论内容' }}</h4>
        <p v-if="item.author">作者：{{ typeof item.author === 'object' ? item.author.nickname : item.author }}</p>

        <div class="review-card__actions">
          <input
            v-model="reviewComment"
            type="text"
            placeholder="审核意见（拒绝时必填）"
            class="review-input"
          >
          <div class="review-card__btns">
            <button class="review-btn review-btn--approve" @click="handleReview(item.id, 'approve')">
              通过
            </button>
            <button class="review-btn review-btn--reject" @click="handleReview(item.id, 'reject')">
              拒绝
            </button>
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
  gap: 10px;
  margin-bottom: 8px;
}

.review-card__type {
  background: var(--color-primary-light);
  border-radius: 4px;
  color: var(--color-primary);
  font-size: 12px;
  font-weight: 500;
  padding: 2px 8px;
}

.review-card__flags { color: var(--color-warning); font-size: 13px; }
.review-card__time { color: var(--color-text-muted); font-size: 12px; margin-left: auto; }
.review-card h4 { font-size: 16px; margin: 0 0 6px; }
.review-card p { color: var(--color-text-secondary); font-size: 13px; margin: 0 0 12px; }

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
  outline: none;
}

.review-card__btns { display: flex; gap: 6px; }

.review-btn {
  border: 0;
  border-radius: 6px;
  cursor: pointer;
  font: inherit;
  font-size: 13px;
  padding: 8px 18px;
}

.review-btn--approve { background: var(--color-success); color: var(--color-bg-card); }
.review-btn--approve:hover { background: var(--color-success-hover); }
.review-btn--reject { background: var(--color-danger); color: var(--color-bg-card); }
.review-btn--reject:hover { background: var(--color-danger-hover); }

@media (max-width: 780px) {
  .admin-nav__item { padding: 10px 14px; font-size: 13px; }
  .review-card__actions { flex-direction: column; align-items: stretch; }
}
</style>
