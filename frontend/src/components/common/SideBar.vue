<script setup>
import { ref, computed } from 'vue'
import { useRouter, useRoute } from 'vue-router'
import { useAuthStore } from '../../stores/auth'
import AppIcon from './AppIcon.vue'

const router = useRouter()
const route = useRoute()
const auth = useAuthStore()

const showMobileMenu = defineModel('showMobileMenu', { type: Boolean, default: false })

const navItems = [
  { label: '综合讨论', to: '/categories/1', icon: 'discuss' },
  { label: '股票市场', to: '/categories/2', icon: 'stock' },
  { label: '基金投资', to: '/categories/3', icon: 'fund' },
  { label: '问答求助', to: '/categories/4', icon: 'question' },
  { label: '投资策略', to: '/categories/5', icon: 'strategy' },
]

const expandedGroups = ref([])

const categoryGroups = [
  {
    key: 'market', label: '市场讨论区', icon: 'stock',
    items: [
      { label: 'A股', to: '/search', query: { keyword: 'A股' } },
      { label: '港股', to: '/search', query: { keyword: '港股' } },
      { label: '美股', to: '/search', query: { keyword: '美股' } },
      { label: '期货', to: '/search', query: { keyword: '期货' } },
    ],
  },
  {
    key: 'theme', label: '主题专区', icon: 'discuss',
    items: [
      { label: '价值投资', to: '/search', query: { keyword: '价值投资' } },
      { label: '量化投资', to: '/search', query: { keyword: '量化投资' } },
      { label: '基金投资', to: '/search', query: { keyword: '基金投资' } },
      { label: '新股/新债', to: '/search', query: { keyword: '新股' } },
      { label: '宏观策略', to: '/search', query: { keyword: '宏观策略' } },
    ],
  },
  {
    key: 'company', label: '公司研究专区', icon: 'strategy',
    items: [
      { label: '行业分析', to: '/search', query: { keyword: '行业分析' } },
      { label: '个股深度', to: '/search', query: { keyword: '个股' } },
    ],
  },
  {
    key: 'qa', label: '问答求助区', icon: 'question',
    items: [
      { label: '新手提问', to: '/search', query: { keyword: '新手' } },
      { label: '投资解惑', to: '/search', query: { keyword: '投资解惑' } },
    ],
  },
]

function toggleGroup(key) {
  const idx = expandedGroups.value.indexOf(key)
  if (idx >= 0) expandedGroups.value.splice(idx, 1)
  else expandedGroups.value.push(key)
}

const discoverItems = [
  { label: '热门', to: '/', query: { tab: 'hot' }, icon: 'trending' },
  { label: '搜索', to: '/search', icon: 'search' },
]

const personalItems = computed(() => {
  if (!auth.isLoggedIn) return []
  return [
    { label: '我的动态', to: '/', query: { tab: 'feed' }, icon: 'feed' },
    { label: '我的收藏', to: '/me/collections', icon: 'collections' },
    { label: '关注列表', to: `/users/${auth.user?.id || 'me'}/follow`, icon: 'followers' },
    { label: '我的群组', to: '/groups', icon: 'groups' },
    { label: '私信', to: '/messages', icon: 'message' },
  ]
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

function navigate(item) {
  router.push({ path: item.to, query: item.query })
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

    <!-- 论坛板块 -->
    <div class="nav-section">
      <div class="nav-section__label">论坛板块</div>
      <nav class="nav-list" aria-label="论坛板块">
        <a
          v-for="item in navItems"
          :key="item.to"
          :class="['nav-item', { active: isActive(item) }]"
          href="javascript:void(0)"
          @click="navigate(item)"
        >
          <AppIcon :name="item.icon" :size="18" />
          {{ item.label }}
        </a>
      </nav>
    </div>

    <!-- 分组导航 -->
    <div class="nav-section">
      <div class="nav-section__label">分组导航</div>
      <div v-for="grp in categoryGroups" :key="grp.key" class="nav-group">
        <button class="nav-group__header" @click="toggleGroup(grp.key)">
          <AppIcon :name="grp.icon" :size="16" />
          <span>{{ grp.label }}</span>
          <span class="nav-group__arrow" :class="{ open: expandedGroups.includes(grp.key) }">&#9662;</span>
        </button>
        <div v-if="expandedGroups.includes(grp.key)" class="nav-group__body">
          <a
            v-for="item in grp.items"
            :key="item.label"
            :class="['nav-item nav-item--child', { active: route.path === item.to && route.query.keyword === item.query.keyword }]"
            href="javascript:void(0)"
            @click="navigate(item)"
          >
            <span class="nav-item__dot" />
            {{ item.label }}
          </a>
        </div>
      </div>
    </div>

    <!-- 发现 -->
    <div class="nav-section">
      <div class="nav-section__label">发现</div>
      <nav class="nav-list" aria-label="发现">
        <a
          v-for="item in discoverItems"
          :key="item.to"
          :class="['nav-item', { active: isActive(item) }]"
          href="javascript:void(0)"
          @click="navigate(item)"
        >
          <AppIcon :name="item.icon" :size="18" />
          {{ item.label }}
        </a>
      </nav>
    </div>

    <!-- 个人（需登录） -->
    <div v-if="personalItems.length" class="nav-section">
      <div class="nav-section__label">个人</div>
      <nav class="nav-list" aria-label="个人">
        <a
          v-for="item in personalItems"
          :key="item.to"
          :class="['nav-item', { active: isActive(item) }]"
          href="javascript:void(0)"
          @click="navigate(item)"
        >
          <AppIcon :name="item.icon" :size="18" />
          {{ item.label }}
        </a>
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