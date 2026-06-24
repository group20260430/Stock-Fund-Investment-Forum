<script setup>
import { ref, computed, onMounted } from 'vue'
import { useRouter, useRoute } from 'vue-router'
import { useAuthStore } from '../../stores/auth'
import { fetchCategories } from '../../api/posts'
import AppIcon from './AppIcon.vue'

const router = useRouter()
const route = useRoute()
const auth = useAuthStore()

const showMobileMenu = defineModel('showMobileMenu', { type: Boolean, default: false })

const forumSections = ref([])
const expandedSections = ref([])

onMounted(async () => {
  await loadSections()
})

// 用 key 强制重新挂载，保证从其他页面返回时刷新
const refreshKey = ref(0)
async function loadSections() {
  try {
    const data = await fetchCategories()
    forumSections.value = Array.isArray(data) ? data : []
  } catch {
    forumSections.value = []
  }
  // 默认展开第一个分区
  if (forumSections.value.length > 0 && expandedSections.value.length === 0) {
    expandedSections.value.push(forumSections.value[0].name)
  }
}

function toggleSection(name) {
  const idx = expandedSections.value.indexOf(name)
  if (idx >= 0) expandedSections.value.splice(idx, 1)
  else expandedSections.value.push(name)
}

const discoverItems = [
  { label: '热门', to: '/', query: { tab: 'hot' }, icon: 'trending' },
  { label: '搜索', to: '/search', icon: 'search' },
]

const personalItems = computed(() => {
  if (!auth.isLoggedIn) return []
  const items = [
    { label: '我的动态', to: '/', query: { tab: 'feed' }, icon: 'feed' },
    { label: '通知', to: '/notifications', icon: 'bell' },
    { label: '我的收藏', to: '/me/collections', icon: 'collections' },
    { label: '关注列表', to: `/users/${auth.user?.id || 'me'}/follow`, icon: 'followers' },
    { label: '我的群组', to: '/groups', icon: 'groups' },
    { label: '私信', to: '/messages', icon: 'message' },
  ]
  // 管理员额外显示"管理后台"入口
  if (auth.isAdmin) {
    items.push({ label: '管理后台', to: '/admin', icon: 'settings' })
  }
  return items
})

function isActive(item) {
  if (item.to === '/') {
    if (item.query) {
      return route.path === '/' && Object.entries(item.query).every(
        ([key, val]) => route.query[key] === val
      )
    }
    return route.path === '/'
  }
  return route.path.startsWith(item.to.split('?')[0])
}

function onNavClick() {
  showMobileMenu.value = false
}
</script>

<template>
  <!-- 移动端遮罩 -->
  <div
    v-if="showMobileMenu"
    class="sidebar-overlay"
    @click="showMobileMenu = false"
  />

  <aside :class="['sidebar', { 'sidebar--open': showMobileMenu }]" aria-label="论坛导航">
    <!-- 品牌区 -->
    <div class="brand" @click="router.push('/')">
      <strong class="brand-name">股票基金投资论坛</strong>
      <span>Stock &amp; Fund Forum</span>
    </div>

    <!-- ===== 论坛板块 ===== -->
      <div class="nav-section">
        <div class="nav-section__label">论坛板块</div>
        <div v-for="sec in forumSections" :key="sec.id" class="nav-group">
          <button class="nav-group__header" @click="toggleSection(sec.name)">
            <AppIcon name="stock" :size="16" />
            <span>{{ sec.name }}</span>
            <span class="nav-group__arrow" :class="{ open: expandedSections.includes(sec.name) }">&#9662;</span>
          </button>
          <div v-if="expandedSections.includes(sec.name)" class="nav-group__body">
            <router-link
              v-for="child in sec.children"
              :key="child.id"
              :to="`/categories/${child.id}`"
              :class="['nav-item nav-item--child', { active: route.path === `/categories/${child.id}` }]"
              @click="onNavClick()"
            >
              <span class="nav-item__dot" />
              {{ child.name }}
            </router-link>
          </div>
        </div>
      </div>

      <!-- 发现 -->
      <div class="nav-section">
        <div class="nav-section__label">发现</div>
        <nav class="nav-list" aria-label="发现">
          <router-link
            v-for="item in discoverItems"
            :key="item.to"
            :to="{ path: item.to, query: item.query }"
            :class="['nav-item', { active: isActive(item) }]"
            @click="onNavClick()"
          >
            <AppIcon :name="item.icon" :size="18" />
            {{ item.label }}
          </router-link>
        </nav>
      </div>

      <!-- 个人（需登录） -->
      <div v-if="personalItems.length" class="nav-section">
        <div class="nav-section__label">个人</div>
        <nav class="nav-list" aria-label="个人">
          <router-link
            v-for="item in personalItems"
            :key="item.to"
            :to="{ path: item.to, query: item.query }"
            :class="['nav-item', { active: isActive(item) }]"
            @click="onNavClick()"
          >
            <AppIcon :name="item.icon" :size="18" />
            {{ item.label }}
          </router-link>
        </nav>
      </div>

    <!-- 底部用户信息（已登录时） -->
    <div v-if="auth.isLoggedIn && auth.user" class="sidebar-footer">
      <img
        :src="auth.user.avatar_url || '/default-avatar.png'"
        :alt="auth.user.nickname"
        class="sidebar-avatar"
        @error="$event.target.src = 'data:image/svg+xml,%3Csvg xmlns=%22http://www.w3.org/2000/svg%22 viewBox=%220 0 40 40%22%3E%3Ccircle fill=%22%23374151%22 cx=%2220%22 cy=%2220%22 r=%2220%22/%3E%3Ctext fill=%22%239ca3af%22 x=%2220%22 y=%2226%22 text-anchor=%22middle%22 font-size=%2216%22%3E%F0%9F%91%A4%3C/text%3E%3C/svg%3E'"
      >
      <div class="sidebar-user-info">
        <strong>{{ auth.user.nickname }}</strong>
        <span>{{ auth.user.auth_level === 'professional' ? '专业认证' : auth.user.auth_level === 'verified' ? '实名认证' : '普通用户' }}</span>
      </div>
    </div>
  </aside>
</template>

<style scoped>
.sidebar {
  background: var(--color-bg-sidebar);
  color: var(--color-text-sidebar);
  padding: 28px 20px;
  display: flex;
  flex-direction: column;
  height: 100vh;
  position: sticky;
  top: 0;
  z-index: 20;
  overflow-y: auto;
}

.brand {
  cursor: pointer;
  display: grid;
  gap: 6px;
  margin-bottom: 24px;
}

.brand-name {
  font-size: 18px;
  color: var(--color-bg-card);
}

.brand span {
  color: var(--color-text-muted);
  font-size: 13px;
}

.nav-section {
  margin-bottom: 16px;
}

.nav-section__label {
  color: var(--color-text-secondary);
  font-size: 11px;
  font-weight: 600;
  letter-spacing: 0.05em;
  margin-bottom: 8px;
  padding: 0 12px;
  text-transform: uppercase;
}

.nav-list {
  display: grid;
  gap: 4px;
}

.nav-item {
  align-items: center;
  border-radius: 6px;
  color: var(--color-text-sidebar);
  display: flex;
  gap: 10px;
  padding: 10px 12px;
  text-decoration: none;
  transition: background 0.15s, color 0.15s;
}

.nav-item:hover {
  background: var(--color-bg-sidebar-hover);
  color: var(--color-bg-card);
}

.nav-item.active {
  background: var(--color-bg-sidebar-hover);
  color: var(--color-bg-card);
  box-shadow: inset 3px 0 0 var(--color-primary);
}

.nav-item--child {
  padding: 8px 12px 8px 28px;
  font-size: 13px;
}

.nav-item__dot {
  width: 5px;
  height: 5px;
  border-radius: 50%;
  background: var(--color-text-muted);
  flex-shrink: 0;
}

.nav-item.active .nav-item__dot {
  background: var(--color-primary);
}

/* group */
.nav-group {
  margin-bottom: 2px;
}

.nav-group__header {
  align-items: center;
  background: none;
  border: none;
  border-radius: 6px;
  color: var(--color-text-sidebar);
  cursor: pointer;
  display: flex;
  gap: 8px;
  padding: 9px 12px;
  width: 100%;
  font-size: 13px;
  transition: background 0.15s;
}

.nav-group__header:hover {
  background: var(--color-bg-sidebar-hover);
}

.nav-group__arrow {
  margin-left: auto;
  font-size: 10px;
  transition: transform 0.2s;
}

.nav-group__arrow.open {
  transform: rotate(180deg);
}

.nav-group__body {
  padding-left: 4px;
}

.sidebar-footer {
  align-items: center;
  border-top: 1px solid var(--color-bg-sidebar-hover);
  display: flex;
  gap: 12px;
  margin-top: auto;
  padding-top: 20px;
}

.sidebar-avatar {
  border-radius: 50%;
  height: 36px;
  object-fit: cover;
  width: 36px;
}

.sidebar-user-info {
  display: grid;
  gap: 2px;
}

.nav-item--back {
  border-top: 1px solid var(--color-bg-sidebar-hover);
  margin-top: 8px;
  padding-top: 16px;
}

.nav-item--back:hover {
  color: var(--color-primary-light) !important;
}

.sidebar-user-info strong {
  font-size: 14px;
  color: var(--color-text-white);
}

.sidebar-user-info span {
  font-size: 12px;
  color: var(--color-text-muted);
}

/* 移动端侧边栏抽屉 */
.sidebar-overlay {
  background: var(--color-bg-overlay);
  display: none;
  inset: 0;
  position: fixed;
  z-index: 30;
}

@media (max-width: 780px) {
  .sidebar {
    bottom: 0;
    left: 0;
    overflow-y: auto;
    position: fixed;
    top: 0;
    transform: translateX(-100%);
    transition: transform 0.25s ease;
    width: 260px;
    z-index: 40;
  }

  .sidebar--open {
    transform: translateX(0);
  }

  .sidebar-overlay {
    display: block;
  }
}
</style>