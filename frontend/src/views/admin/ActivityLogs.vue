<script setup>
import { ref, onMounted } from 'vue'
import { useToastStore } from '../../stores/toast'
import { fetchActivityLogs } from '../../api/admin'
import AppLayout from '../../components/layout/AppLayout.vue'
import Loading from '../../components/common/Loading.vue'
import Pagination from '../../components/common/Pagination.vue'

const toast = useToastStore()

const items = ref([])
const loading = ref(true)
const pagination = ref({ page: 1, total: 0, size: 30 })

async function load(page = 1) {
  loading.value = true
  try {
    const data = await fetchActivityLogs({ page, size: pagination.value.size })
    items.value = data.items || []
    pagination.value.total = data.total || 0
    pagination.value.page = page
  } catch (err) {
    toast.error('加载失败: ' + err.message)
  } finally {
    loading.value = false
  }
}

onMounted(() => load())
</script>

<template>
  <AppLayout>
    <header class="toolbar"><h1>管理后台 / 操作日志</h1></header>
    <div class="admin-nav">
      <router-link to="/admin" class="admin-nav__item">总览</router-link>
      <router-link to="/admin/review" class="admin-nav__item">审核队列</router-link>
      <router-link to="/admin/users" class="admin-nav__item">用户管理</router-link>
      <router-link to="/admin/certifications" class="admin-nav__item">认证审核</router-link>
      <router-link to="/admin/sensitive-words" class="admin-nav__item">敏感词</router-link>
      <router-link to="/admin/logs" class="admin-nav__item admin-nav__item--active">操作日志</router-link>
    </div>

    <Loading v-if="loading" variant="skeleton" :rows="2" />

    <div v-else-if="items.length === 0" class="empty-state"><p>暂无操作日志</p></div>

    <table v-else class="log-table">
      <thead>
        <tr><th>时间</th><th>用户</th><th>操作</th><th>详情</th></tr>
      </thead>
      <tbody>
        <tr v-for="item in items" :key="item.id">
          <td class="log-time">{{ item.created_at || '--' }}</td>
          <td>{{ item.user?.nickname || item.user_id || '--' }}</td>
          <td><span class="action-tag">{{ item.action || item.activity_type || '--' }}</span></td>
          <td class="log-detail">{{ item.detail || item.description || '--' }}</td>
        </tr>
      </tbody>
    </table>

    <Pagination
      v-if="pagination.total > pagination.size"
      :current="pagination.page"
      :total="pagination.total"
      :size="pagination.size"
      @update:current="load"
    />
  </AppLayout>
</template>

<style scoped>
.toolbar { margin-bottom: 24px; }
.toolbar h1 { font-size: 24px; margin: 0; }
.admin-nav { background: var(--color-bg-card); border: 1px solid var(--color-border); border-radius: 8px; display: flex; gap: 0; margin-bottom: 24px; overflow: hidden; flex-wrap: wrap; }
.admin-nav__item { color: var(--color-text-secondary); font-size: 14px; padding: 12px 20px; text-decoration: none; }
.admin-nav__item:hover { background: var(--color-bg-hover); }
.admin-nav__item--active { background: var(--color-primary); color: #fff; }
.log-table { background: var(--color-bg-card); border: 1px solid var(--color-border); border-radius: 8px; width: 100%; border-collapse: collapse; overflow: hidden; }
.log-table th, .log-table td { padding: 10px 14px; text-align: left; border-bottom: 1px solid var(--color-border-light); font-size: 13px; }
.log-table th { background: var(--color-bg-hover); font-weight: 600; }
.log-time { white-space: nowrap; color: var(--color-text-muted); font-size: 12px; }
.log-detail { max-width: 300px; overflow: hidden; text-overflow: ellipsis; white-space: nowrap; }
.action-tag { background: var(--color-primary-light); border-radius: 4px; color: var(--color-primary); font-size: 12px; padding: 2px 8px; }
.empty-state { background: var(--color-bg-card); border: 1px solid var(--color-border); border-radius: 8px; padding: 40px; text-align: center; color: var(--color-text-muted); }
</style>
