<script setup>
import { ref, onMounted } from 'vue'
import { useToastStore } from '../../stores/toast'
import { fetchCertifications, reviewCertification } from '../../api/admin'
import Loading from '../../components/common/Loading.vue'

const toast = useToastStore()

const items = ref([])
const loading = ref(true)
const pagination = ref({ page: 1, total: 0 })
const filter = ref({ status: 'pending' })
const reviewComment = ref({})

async function load() {
  loading.value = true
  try {
    const data = await fetchCertifications({ ...filter.value, page: pagination.value.page, size: 20 })
    items.value = data.items || []
    pagination.value.total = data.total || 0
  } catch (err) {
    toast.error('加载失败: ' + err.message)
  } finally {
    loading.value = false
  }
}

async function handleReview(id, action) {
  if (action === 'reject' && !(reviewComment.value[id] || '').trim()) {
    toast.warning('拒绝时必须填写审核意见')
    return
  }
  try {
    await reviewCertification(id, action, reviewComment.value[id] || '')
    toast.success(action === 'approve' ? '认证已通过' : '认证已拒绝')
    items.value = items.value.filter(item => item.id !== id)
    pagination.value.total = Math.max(0, pagination.value.total - 1)
  } catch (err) {
    toast.error(err.message || '操作失败')
  }
}

onMounted(load)
</script>

<template>
    <header class="toolbar"><h1>管理后台 / 认证审核</h1></header>
    <div class="admin-nav">
      <router-link to="/admin" class="admin-nav__item">总览</router-link>
      <router-link to="/admin/review" class="admin-nav__item">审核队列</router-link>
      <router-link to="/admin/users" class="admin-nav__item">用户管理</router-link>
      <router-link to="/admin/certifications" class="admin-nav__item admin-nav__item--active">认证审核</router-link>
    </div>

    <div class="filter-bar">
      <label>状态：
        <select v-model="filter.status" @change="load()" class="filter-select">
          <option value="pending">待审核</option>
          <option value="approved">已通过</option>
          <option value="rejected">已拒绝</option>
        </select>
      </label>
    </div>

    <Loading v-if="loading" variant="skeleton" :rows="3" />

    <div v-else-if="items.length === 0" class="empty-state"><p>暂无认证申请</p></div>

    <div v-else class="list">
      <div v-for="item in items" :key="item.id" class="review-card">
        <div class="review-card__header">
          <strong>{{ item.real_name || item.user?.nickname || '未知' }}</strong>
          <span :class="['status-badge', 'status-badge--' + item.status]">{{ item.status }}</span>
        </div>
        <p class="review-card__info">身份证：{{ item.id_number || '未提供' }}</p>
        <p class="review-card__info">提交时间：{{ item.created_at || '未知' }}</p>

        <div v-if="item.status === 'pending'" class="review-card__actions">
          <button class="btn-approve" @click="handleReview(item.id, 'approve')">通过</button>
          <div class="reject-group">
            <input v-model="reviewComment[item.id]" class="reject-input" placeholder="拒绝原因（必填）" />
            <button class="btn-reject" @click="handleReview(item.id, 'reject')">拒绝</button>
          </div>
        </div>
      </div>
    </div>
</template>

<style scoped>
.toolbar { margin-bottom: 24px; }
.toolbar h1 { font-size: 24px; margin: 0; }
.admin-nav { background: var(--color-bg-card); border: 1px solid var(--color-border); border-radius: 8px; display: flex; gap: 0; margin-bottom: 24px; overflow: hidden; }
.admin-nav__item { color: var(--color-text-secondary); font-size: 14px; padding: 12px 20px; text-decoration: none; transition: background 0.15s, color 0.15s; }
.admin-nav__item:hover { background: var(--color-bg-hover); }
.admin-nav__item--active { background: var(--color-primary); color: #fff; }
.filter-bar { margin-bottom: 16px; }
.filter-select { border: 1px solid var(--color-border-input); border-radius: 6px; font: inherit; padding: 6px 10px; }
.list { display: grid; gap: 12px; }
.review-card { background: var(--color-bg-card); border: 1px solid var(--color-border); border-radius: 8px; padding: 16px; }
.review-card__header { align-items: center; display: flex; gap: 8px; margin-bottom: 8px; }
.review-card__info { color: var(--color-text-secondary); font-size: 13px; margin: 4px 0; }
.status-badge { border-radius: 4px; font-size: 12px; font-weight: 600; padding: 2px 8px; }
.status-badge--pending { background: var(--color-warning-light); color: var(--color-warning); }
.status-badge--approved { background: var(--color-success-light); color: var(--color-success); }
.status-badge--rejected { background: var(--color-danger-light); color: var(--color-danger); }
.review-card__actions { display: flex; gap: 8px; margin-top: 12px; }
.btn-approve { background: var(--color-success); border: 0; border-radius: 6px; color: #fff; cursor: pointer; font: inherit; font-size: 13px; padding: 8px 16px; }
.reject-group { display: flex; flex: 1; gap: 6px; }
.reject-input { border: 1px solid var(--color-border-input); border-radius: 6px; flex: 1; font: inherit; font-size: 13px; padding: 8px 10px; min-width: 0; }
.btn-reject { background: var(--color-danger); border: 0; border-radius: 6px; color: #fff; cursor: pointer; font: inherit; font-size: 13px; padding: 8px 16px; }
.empty-state { background: var(--color-bg-card); border: 1px solid var(--color-border); border-radius: 8px; padding: 40px; text-align: center; color: var(--color-text-muted); }
</style>
