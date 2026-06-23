<script setup>
import { ref, onMounted, onUnmounted } from 'vue'
import { useRouter } from 'vue-router'
import { fetchUnreadMessageCount } from '../../api/messages'
import { useAuthStore } from '../../stores/auth'
import AppIcon from './AppIcon.vue'

const router = useRouter()
const auth = useAuthStore()

const emit = defineEmits(['toggle-mobile-menu'])
const showMobileMenu = defineModel('showMobileMenu', { type: Boolean, default: false })

const showUserMenu = ref(false)
const showSearchBox = ref(false)
const searchKeyword = ref('')

function goSearch() {
  if (searchKeyword.value.trim()) {
    router.push({ name: 'search', query: { keyword: searchKeyword.value.trim() } })
  } else {
    router.push({ name: 'search' })
  }
  showSearchBox.value = false
  searchKeyword.value = ''
}

function handleSearchKeydown(e) {
  if (e.key === 'Enter') goSearch()
  if (e.key === 'Escape') {
    showSearchBox.value = false
    searchKeyword.value = ''
  }
}

function logout() {
  auth.logout()
  showUserMenu.value = false
  router.push({ name: 'home' })
}

function goTo(path) {
  showUserMenu.value = false
  router.push(path)
}

// ===== 未读私信角标 =====
const unreadCount = ref(0)
let notifyPollTimer = null

async function loadUnreadCount() {
  if (!auth.isLoggedIn) return
  try {
    const result = await fetchUnreadMessageCount()
    unreadCount.value = result?.unread_count || 0
  } catch { /* ignore */ }
}

// 监听"消息已读"事件，即时刷新角标
function handleMessagesRead() {
  loadUnreadCount()
}

onMounted(() => {
  loadUnreadCount()
  notifyPollTimer = setInterval(loadUnreadCount, 15000) // 每 15s
  window.addEventListener('messages-read', handleMessagesRead)
})

onUnmounted(() => {
  if (notifyPollTimer) clearInterval(notifyPollTimer)
  window.removeEventListener('messages-read', handleMessagesRead)
  document.removeEventListener('visibilitychange', onVisibilityChange)
})

function onVisibilityChange() {
  if (!document.hidden) {
    loadUnreadCount()
  }
}
document.addEventListener('visibilitychange', onVisibilityChange)
</script>

<template>
  <header class="navbar">
    <div class="navbar__left">
      <!-- 移动端汉堡菜单 -->
      <button class="navbar__burger" aria-label="菜单" @click="emit('toggle-mobile-menu')">
        <span />
        <span />
        <span />
      </button>

      <!-- 移动端 Logo -->
      <span class="navbar__brand" @click="router.push('/')">股票基金投资论坛</span>
    </div>

    <!-- 搜索区 -->
    <div class="navbar__center">
      <div v-if="showSearchBox" class="search-box">
        <input
          ref="searchInput"
          v-model="searchKeyword"
          type="text"
          placeholder="搜索股票/话题/用户..."
          @keydown="handleSearchKeydown"
          @blur="showSearchBox = false"
        >
      </div>
      <button class="navbar__icon-btn" aria-label="搜索" @click="showSearchBox = !showSearchBox">
        <AppIcon name="search" :size="20" />
      </button>
    </div>

    <!-- 右侧操作区 -->
    <div class="navbar__right">
      <template v-if="auth.isLoggedIn">
        <!-- 通知 -->
        <button class="navbar__icon-btn navbar__bell-btn" aria-label="通知" @click="goTo('/messages')">
          <AppIcon name="bell" :size="20" />
          <span v-if="unreadCount > 0" class="notify-badge">{{ unreadCount > 99 ? '99+' : unreadCount }}</span>
        </button>

        <!-- 用户菜单 -->
        <div class="user-menu-wrapper">
          <button class="navbar__avatar-btn" @click="showUserMenu = !showUserMenu">
            <img
              :src="auth.user?.avatar_url || ''"
              :alt="auth.user?.nickname || '用户'"
              class="navbar__avatar"
              @error="$event.target.src = 'data:image/svg+xml,%3Csvg xmlns=%22http://www.w3.org/2000/svg%22 viewBox=%220 0 32 32%22%3E%3Ccircle fill=%22%23374151%22 cx=%2216%22 cy=%2216%22 r=%2216%22/%3E%3Ctext fill=%22%239ca3af%22 x=%2216%22 y=%2221%22 text-anchor=%22middle%22 font-size=%2212%22%3E%F0%9F%91%A4%3C/text%3E%3C/svg%3E'"
            >
          </button>

          <div v-if="showUserMenu" class="user-dropdown">
            <div class="user-dropdown__header">
              <strong>{{ auth.user?.nickname }}</strong>
              <span>{{ auth.user?.role === 'admin' ? '管理员' : auth.user?.auth_level === 'professional' ? '专业认证' : '普通用户' }}</span>
            </div>
            <div class="user-dropdown__divider" />
            <button @click="goTo(`/users/${auth.user?.id || 'me'}`)">个人主页</button>
            <button @click="goTo('/messages')">私信</button>
            <button @click="goTo('/me/settings')">设置</button>
            <button v-if="auth.isAdmin" @click="goTo('/admin')">管理后台</button>
            <div class="user-dropdown__divider" />
            <button class="user-dropdown__logout" @click="logout">退出登录</button>
          </div>
        </div>

        <!-- 发布按钮 -->
        <button class="navbar__publish-btn" @click="router.push('/posts/new')">
          + 发布
        </button>
      </template>

      <template v-else>
        <button class="navbar__text-btn" @click="router.push('/login')">登录</button>
        <button class="navbar__primary-btn" @click="router.push('/register')">注册</button>
      </template>
    </div>
  </header>
</template>

<style scoped>
.navbar {
  align-items: center;
  background: var(--color-bg-card);
  border-bottom: 1px solid var(--color-border);
  display: flex;
  gap: 16px;
  height: 56px;
  padding: 0 24px;
  position: sticky;
  top: 0;
  z-index: 10;
}

.navbar__left {
  align-items: center;
  display: flex;
  gap: 12px;
}

.navbar__burger {
  align-items: center;
  background: none;
  border: 0;
  border-radius: 6px;
  cursor: pointer;
  display: none;
  flex-direction: column;
  gap: 4px;
  padding: 8px;
}

.navbar__burger span {
  background: var(--color-text-body);
  border-radius: 2px;
  display: block;
  height: 2px;
  transition: all 0.2s;
  width: 20px;
}

.navbar__brand {
  color: var(--color-text-primary);
  cursor: pointer;
  display: none;
  font-size: 16px;
  font-weight: 700;
}

.navbar__center {
  align-items: center;
  display: flex;
  margin-left: auto;
}

.search-box {
  position: relative;
}

.search-box input {
  border: 1px solid var(--color-border-input);
  border-radius: 8px;
  font: inherit;
  padding: 8px 12px;
  width: 280px;
}

.search-box input:focus {
  border-color: var(--color-primary);
  box-shadow: 0 0 0 3px var(--color-primary-ring);
  outline: none;
}

.navbar__right {
  align-items: center;
  display: flex;
  gap: 8px;
}

.navbar__icon-btn {
  align-items: center;
  background: none;
  border: 0;
  border-radius: 8px;
  color: var(--color-text-body);
  cursor: pointer;
  display: flex;
  font-size: 18px;
  height: 36px;
  justify-content: center;
  padding: 0;
  width: 36px;
}

.navbar__icon-btn:hover {
  background: var(--color-bg-hover);
}

.navbar__bell-btn {
  position: relative;
}
.notify-badge {
  position: absolute;
  top: 0;
  right: 0;
  background: var(--color-danger);
  color: #fff;
  font-size: 10px;
  font-weight: 700;
  min-width: 16px;
  height: 16px;
  border-radius: 8px;
  display: flex;
  align-items: center;
  justify-content: center;
  padding: 0 5px;
  line-height: 1;
  transform: translate(25%, -25%);
  pointer-events: none;
}

.navbar__avatar-btn {
  background: none;
  border: 0;
  cursor: pointer;
  padding: 2px;
}

.navbar__avatar {
  border-radius: 50%;
  height: 32px;
  object-fit: cover;
  width: 32px;
}

.navbar__publish-btn {
  background: var(--color-primary);
  border: 0;
  border-radius: 6px;
  color: var(--color-bg-card);
  cursor: pointer;
  font: inherit;
  font-size: 14px;
  font-weight: 500;
  margin-left: 4px;
  padding: 8px 16px;
}

.navbar__publish-btn:hover {
  background: var(--color-primary-hover);
}

.navbar__text-btn {
  background: none;
  border: 0;
  color: var(--color-text-body);
  cursor: pointer;
  font: inherit;
  font-size: 14px;
  padding: 8px 12px;
}

.navbar__text-btn:hover {
  color: var(--color-primary);
}

.navbar__primary-btn {
  background: var(--color-primary);
  border: 0;
  border-radius: 6px;
  color: var(--color-bg-card);
  cursor: pointer;
  font: inherit;
  font-size: 14px;
  padding: 8px 16px;
}

.navbar__primary-btn:hover {
  background: var(--color-primary-hover);
}

/* 用户下拉菜单 */
.user-menu-wrapper {
  position: relative;
}

.user-dropdown {
  background: var(--color-bg-card);
  border: 1px solid var(--color-border);
  border-radius: 10px;
  box-shadow: 0 10px 25px var(--color-bg-overlay);
  display: grid;
  min-width: 180px;
  padding: 8px;
  position: absolute;
  right: 0;
  top: calc(100% + 8px);
  z-index: 50;
}

.user-dropdown__header {
  padding: 8px 12px 4px;
}

.user-dropdown__header strong {
  display: block;
  font-size: 14px;
}

.user-dropdown__header span {
  color: var(--color-text-secondary);
  font-size: 12px;
}

.user-dropdown__divider {
  border-top: 1px solid var(--color-border);
  margin: 4px 0;
}

.user-dropdown button {
  background: none;
  border: 0;
  border-radius: 6px;
  color: var(--color-text-body);
  cursor: pointer;
  font: inherit;
  font-size: 14px;
  padding: 8px 12px;
  text-align: left;
}

.user-dropdown button:hover {
  background: var(--color-bg-hover);
}

.user-dropdown__logout {
  color: var(--color-danger) !important;
}

@media (max-width: 780px) {
  .navbar {
    padding: 0 16px;
  }

  .navbar__burger {
    display: flex;
  }

  .navbar__brand {
    display: block;
  }

  .search-box input {
    width: 200px;
  }

  .navbar__publish-btn {
    padding: 6px 12px;
    font-size: 13px;
  }
}
</style>
