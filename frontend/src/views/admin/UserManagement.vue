<script setup>
import { ref, onMounted, reactive } from 'vue'
import UserCard from '../../components/user/UserCard.vue'
import Loading from '../../components/common/Loading.vue'
import Pagination from '../../components/common/Pagination.vue'
import { useToastStore } from '../../stores/toast'
import { fetchUsers, banUser } from '../../api/admin'

const toast = useToastStore()

const users = ref([])
const loading = ref(true)
const pagination = reactive({ page: 1, size: 20, total: 0 })

onMounted(async () => {
  await loadUsers()
})

async function loadUsers(page = 1) {
  loading.value = true
  try {
    const data = await fetchUsers({ page, size: 20 })
    users.value = data.items || []
    pagination.total = data.total || 0
    pagination.page = page
  } catch (err) {
    console.error('加载用户列表失败:', err.message)
  } finally {
    loading.value = false
  }
}

async function handleBan(userId) {
  try {
    await banUser(userId, 'ban', '违规操作', 72)
    toast.success('用户已封禁')
    await loadUsers(pagination.page)
  } catch (err) {
    toast.error(err.message || '封禁失败')
  }
}

function handlePageChange(page) { loadUsers(page) }
</script>

<template>
    <header class="toolbar">
      <h1>管理后台 / 用户管理</h1>
    </header>

    <div class="admin-nav">
      <router-link to="/admin" class="admin-nav__item">总览</router-link>
      <router-link to="/admin/review" class="admin-nav__item">审核队列</router-link>
      <router-link to="/admin/users" class="admin-nav__item admin-nav__item--active">用户管理</router-link>
      <router-link to="/admin/certifications" class="admin-nav__item">认证审核</router-link>
      <router-link to="/admin/sensitive-words" class="admin-nav__item">敏感词</router-link>
      <router-link to="/admin/compliance" class="admin-nav__item">合规检查</router-link>
      <router-link to="/admin/duplicate-content" class="admin-nav__item">重复检测</router-link>
      <router-link to="/admin/behavior" class="admin-nav__item">行为监控</router-link>
      <router-link to="/admin/logs" class="admin-nav__item">操作日志</router-link>
      <router-link to="/admin/hot-topics" class="admin-nav__item">热门话题分析</router-link>
      <router-link to="/admin/engagement" class="admin-nav__item">用户参与度</router-link>
      <router-link to="/admin/categories" class="admin-nav__item">板块管理</router-link>
    </div>

    <Loading v-if="loading" variant="skeleton" :rows="3" />

    <div v-else class="user-list">
      <div v-for="user in users" :key="user.id" class="user-row">
        <UserCard :user="user" :show-follow-btn="false" />
        <button class="ban-btn" @click="handleBan(user.id)">封禁</button>
      </div>
    </div>

    <Pagination
      v-if="pagination.total > 20"
      :current="pagination.page"
      :total="pagination.total"
      :size="20"
      @update:current="handlePageChange"
    />
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

.user-list { display: grid; gap: 10px; }

.user-row {
  align-items: center;
  display: flex;
  gap: 12px;
}

.user-row .user-card { flex: 1; }

.ban-btn {
  background: var(--color-bg-card);
  border: 1px solid var(--color-danger);
  border-radius: 6px;
  color: var(--color-danger);
  cursor: pointer;
  font: inherit;
  font-size: 12px;
  padding: 6px 14px;
  white-space: nowrap;
}

.ban-btn:hover { background: var(--color-danger-light); }

@media (max-width: 780px) {
  .admin-nav__item { padding: 10px 14px; font-size: 13px; }
  .user-row { flex-direction: column; }
}
</style>
