<script setup>
import { ref, onMounted, onUnmounted, computed } from 'vue'
import { useRouter } from 'vue-router'
import { useAuthStore } from '../stores/auth'
import { useToastStore } from '../stores/toast'
import { fetchNotifications, markNotificationsRead, fetchUnreadNotificationCount } from '../api/notifications'
import AppIcon from '../components/common/AppIcon.vue'
import Loading from '../components/common/Loading.vue'
import EmptyState from '../components/common/EmptyState.vue'
import Pagination from '../components/common/Pagination.vue'

const router = useRouter()
const auth = useAuthStore()
const toast = useToastStore()

const notifications = ref([])
const loading = ref(true)
const total = ref(0)
const page = ref(1)
const pageSize = 20
const filterType = ref('all')
const unreadCount = ref(0)

const typeOptions = [
  { value: 'all', label: '全部' },
  { value: 'follow', label: '关注' },
  { value: 'mention', label: '@提及' },
  { value: 'new_message', label: '私信' },
  { value: 'group_invite', label: '群组' },
  { value: 'system', label: '系统' },
]

const typeLabels = {
  follow: '关注',
  group_invite: '群组邀请',
  group_join_request: '入群申请',
  group_approved: '入群批准',
  group_rejected: '入群拒绝',
  new_message: '新私信',
  new_group_message: '群消息',
  mention: '@提及',
  system: '系统通知',
}

onMounted(async () => {
  await loadNotifications()
  await loadUnreadCount()
})

async function loadNotifications(p = 1) {
  loading.value = true
  page.value = p
  try {
    const params = { page: p, size: pageSize }
    if (filterType.value !== 'all') params.type = filterType.value
    const data = await fetchNotifications(params)
    notifications.value = data.items || []
    total.value = data.total || 0
  } catch (err) {
    console.error('加载通知失败:', err.message)
  } finally {
    loading.value = false
  }
}

async function loadUnreadCount() {
  try {
    const data = await fetchUnreadNotificationCount()
    unreadCount.value = data?.unread_count || 0
  } catch { /* ignore */ }
}

function handleFilterChange(type) {
  filterType.value = type
  loadNotifications(1)
}

async function handleMarkRead(notification) {
  if (notification.is_read) return
  try {
    await markNotificationsRead([notification.id])
    notification.is_read = true
    unreadCount.value = Math.max(0, unreadCount.value - 1)
  } catch (err) {
    console.error('标记已读失败:', err.message)
  }
}

async function handleMarkAllRead() {
  if (!unreadCount.value) return
  try {
    await markNotificationsRead()
    notifications.value.forEach(n => { n.is_read = true })
    unreadCount.value = 0
    toast.success('已全部标记为已读')
  } catch (err) {
    toast.error(err.message || '操作失败')
  }
}

function handleNotificationClick(notification) {
  handleMarkRead(notification)
  // 根据通知类型跳转到对应页面
  if (notification.target_type === 'post' && notification.target_id) {
    router.push(`/posts/${notification.target_id}`)
  } else if (notification.type === 'new_message') {
    router.push('/messages')
  } else if (notification.type === 'follow' && notification.sender) {
    router.push(`/users/${notification.sender.id}`)
  } else if (notification.type.startsWith('group_')) {
    router.push('/groups')
  }
}

function getTypeIcon(type) {
  const icons = {
    follow: 'user',
    group_invite: 'groups',
    group_join_request: 'groups',
    group_approved: 'groups',
    group_rejected: 'groups',
    new_message: 'message',
    new_group_message: 'message',
    mention: 'reply',
    system: 'bell',
  }
  return icons[type] || 'bell'
}

function formatTime(t) {
  if (!t) return ''
  const date = new Date(t)
  const now = new Date()
  const diff = (now - date) / 1000
  if (diff < 60) return '刚刚'
  if (diff < 3600) return `${Math.floor(diff / 60)}分钟前`
  if (diff < 86400) return `${Math.floor(diff / 3600)}小时前`
  if (diff < 604800) return `${Math.floor(diff / 86400)}天前`
  return date.toLocaleDateString('zh-CN')
}

function handlePageChange(p) {
  loadNotifications(p)
}
</script>

<template>
  <div class="notifications-page">
    <header class="toolbar">
      <div class="toolbar__left">
        <h1>通知</h1>
        <span v-if="unreadCount > 0" class="unread-badge">{{ unreadCount }} 条未读</span>
      </div>
      <button
        v-if="unreadCount > 0"
        class="mark-all-btn"
        @click="handleMarkAllRead"
      >
        <AppIcon name="check" :size="16" />
        全部标为已读
      </button>
    </header>

    <!-- 类型筛选 -->
    <div class="filter-tabs">
      <button
        v-for="opt in typeOptions"
        :key="opt.value"
        :class="['filter-tab', { 'filter-tab--active': filterType === opt.value }]"
        @click="handleFilterChange(opt.value)"
      >
        {{ opt.label }}
      </button>
    </div>

    <!-- 通知列表 -->
    <div class="notifications-list">
      <Loading v-if="loading" variant="skeleton" :rows="5" />

      <EmptyState
        v-else-if="notifications.length === 0"
        icon="bell"
        title="暂无通知"
        description="当有人关注您、@提及您或发送私信时，通知将显示在这里"
      />

      <TransitionGroup v-else name="list-fade" tag="div" class="notifications-items">
        <div
          v-for="n in notifications"
          :key="n.id"
          :class="['notification-item', { 'notification-item--unread': !n.is_read }]"
          @click="handleNotificationClick(n)"
        >
          <div class="notification-item__dot" v-if="!n.is_read" />
          <div class="notification-item__icon">
            <AppIcon :name="getTypeIcon(n.type)" :size="20" />
          </div>
          <div class="notification-item__body">
            <div class="notification-item__title">
              <strong>{{ n.title }}</strong>
            </div>
            <div class="notification-item__content">{{ n.content }}</div>
            <div class="notification-item__meta">
              <span class="notification-item__type">{{ typeLabels[n.type] || n.type }}</span>
              <span class="notification-item__time">{{ formatTime(n.created_at) }}</span>
            </div>
          </div>
          <button
            v-if="!n.is_read"
            class="notification-item__mark-btn"
            title="标记已读"
            @click.stop="handleMarkRead(n)"
          >
            <AppIcon name="check" :size="14" />
          </button>
        </div>
      </TransitionGroup>

      <Pagination
        v-if="total > pageSize"
        :page="page"
        :total="total"
        :size="pageSize"
        @change="handlePageChange"
      />
    </div>
  </div>
</template>

<style scoped>
.notifications-page {
  max-width: 720px;
  margin: 0 auto;
  padding: 24px;
}

.toolbar {
  align-items: center;
  display: flex;
  justify-content: space-between;
  margin-bottom: 20px;
}

.toolbar__left {
  align-items: baseline;
  display: flex;
  gap: 12px;
}

.toolbar__left h1 {
  font-size: 28px;
  margin: 0;
}

.unread-badge {
  background: var(--color-primary-light);
  border-radius: 12px;
  color: var(--color-primary);
  font-size: 13px;
  font-weight: 500;
  padding: 4px 10px;
}

.mark-all-btn {
  align-items: center;
  background: none;
  border: 1px solid var(--color-border-input);
  border-radius: 8px;
  color: var(--color-text-secondary);
  cursor: pointer;
  display: flex;
  font: inherit;
  font-size: 13px;
  gap: 6px;
  padding: 8px 14px;
  transition: all 0.15s;
}

.mark-all-btn:hover {
  border-color: var(--color-primary);
  color: var(--color-primary);
}

/* 类型筛选 */
.filter-tabs {
  display: flex;
  gap: 6px;
  margin-bottom: 16px;
  overflow-x: auto;
  padding-bottom: 4px;
}

.filter-tab {
  background: var(--color-bg-hover);
  border: 0;
  border-radius: 20px;
  color: var(--color-text-secondary);
  cursor: pointer;
  font: inherit;
  font-size: 13px;
  padding: 6px 16px;
  transition: all 0.15s;
  white-space: nowrap;
}

.filter-tab:hover {
  background: var(--color-border);
}

.filter-tab--active {
  background: var(--color-primary);
  color: var(--color-bg-card);
}

/* 通知列表 */
.notifications-list {
  min-height: 200px;
}

.notifications-items {
  display: grid;
  gap: 2px;
}

.notification-item {
  align-items: flex-start;
  background: var(--color-bg-card);
  border: 1px solid transparent;
  border-radius: 10px;
  cursor: pointer;
  display: flex;
  gap: 14px;
  padding: 16px 18px;
  position: relative;
  transition: all 0.15s;
}

.notification-item:hover {
  background: var(--color-bg-hover);
}

.notification-item--unread {
  background: var(--color-primary-light);
  border-color: var(--color-primary-ring);
}

.notification-item__dot {
  background: var(--color-primary);
  border-radius: 50%;
  flex-shrink: 0;
  height: 8px;
  margin-top: 6px;
  width: 8px;
}

.notification-item__icon {
  align-items: center;
  background: var(--color-bg-hover);
  border-radius: 50%;
  color: var(--color-text-secondary);
  display: flex;
  flex-shrink: 0;
  height: 40px;
  justify-content: center;
  width: 40px;
}

.notification-item--unread .notification-item__icon {
  background: var(--color-primary-light);
  color: var(--color-primary);
}

.notification-item__body {
  flex: 1;
  min-width: 0;
}

.notification-item__title {
  font-size: 14px;
  margin-bottom: 4px;
}

.notification-item__content {
  color: var(--color-text-secondary);
  font-size: 13px;
  line-height: 1.5;
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
}

.notification-item__meta {
  align-items: center;
  display: flex;
  gap: 10px;
  margin-top: 6px;
}

.notification-item__type {
  background: var(--color-bg-hover);
  border-radius: 4px;
  color: var(--color-text-muted);
  font-size: 11px;
  padding: 2px 6px;
}

.notification-item__time {
  color: var(--color-text-muted);
  font-size: 12px;
}

.notification-item__mark-btn {
  align-items: center;
  background: none;
  border: 0;
  border-radius: 6px;
  color: var(--color-text-muted);
  cursor: pointer;
  display: flex;
  flex-shrink: 0;
  height: 28px;
  justify-content: center;
  margin-top: 4px;
  opacity: 0;
  transition: all 0.15s;
  width: 28px;
}

.notification-item:hover .notification-item__mark-btn {
  opacity: 1;
}

.notification-item__mark-btn:hover {
  background: var(--color-bg-hover);
  color: var(--color-primary);
}

/* 列表动画 */
.list-fade-enter-active,
.list-fade-leave-active {
  transition: all 0.3s ease;
}

.list-fade-enter-from {
  opacity: 0;
  transform: translateY(-10px);
}

.list-fade-leave-to {
  opacity: 0;
  transform: translateX(20px);
}

.list-fade-move {
  transition: transform 0.3s ease;
}
</style>
