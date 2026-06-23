<script setup>
import { ref, computed, onMounted, watch } from "vue"
import { useRoute, useRouter } from "vue-router"
import PostCard from "../components/post/PostCard.vue"
import UserCard from "../components/user/UserCard.vue"
import Loading from "../components/common/Loading.vue"
import EmptyState from "../components/common/EmptyState.vue"
import Pagination from "../components/common/Pagination.vue"
import AppIcon from "../components/common/AppIcon.vue"
import { search as searchApi, searchSuggestions, searchRecommendations } from "../api/search"
import { toggleFollow } from "../api/users"
import { usePostsStore } from "../stores/posts"
import { useAuthStore } from "../stores/auth"
import { useToastStore } from "../stores/toast"

const route = useRoute()
const router = useRouter()
const postsStore = usePostsStore()
const auth = useAuthStore()
const toast = useToastStore()

const keyword = ref(route.query.keyword || "")
const searchType = ref(route.query.type || "all")
const timeRange = ref(route.query.time || "all")
const sortBy = ref(route.query.sort || "relevance")
const isElite = ref(route.query.elite === "1")
const market = ref(route.query.market || "")
const results = ref([])
const suggestions = ref(null)
const recommendations = ref({ posts: [], users: [], stocks: [] })
const loading = ref(false)
const searched = ref(false)
const total = ref(0)
const page = ref(1)
const inputFocused = ref(false)
const historyKeywords = ref(JSON.parse(localStorage.getItem("search_history") || "[]").slice(0, 5))
let debounceTimer = null

// 市场选项
const marketOptions = [
  { value: "", label: "全部市场" },
  { value: "a_stock", label: "A股" },
  { value: "hk_stock", label: "港股" },
  { value: "us_stock", label: "美股" },
  { value: "fund", label: "基金" },
]

const showSuggestions = computed(() => {
  return inputFocused.value && suggestions.value && (
    (suggestions.value.stocks?.length) ||
    (suggestions.value.users?.length) ||
    (suggestions.value.topics?.length)
  )
})

onMounted(() => {
  loadRecommendations()
  if (keyword.value) doSearch()
})

watch(() => route.query.keyword, (val) => {
  if (val && val !== keyword.value) {
    keyword.value = val
    doSearch()
  }
})

async function doSearch(p = 1) {
  if (!keyword.value.trim()) return
  loading.value = true
  searched.value = true
  page.value = p

  // 保存搜索历史
  saveHistory(keyword.value.trim())

  try {
    const params = {
      keyword: keyword.value.trim(),
      type: searchType.value,
      time_range: timeRange.value,
      sort: sortBy.value,
      page: p,
      size: 20,
    }
    if (isElite.value) params.is_elite = "1"
    if (market.value) params.market = market.value

    const data = await searchApi(params)
    results.value = data.items || []
    total.value = data.total || 0
  } catch (err) {
    console.error("搜索失败:", err.message)
  } finally {
    loading.value = false
    suggestions.value = null
  }
}

async function loadRecommendations() {
  try {
    recommendations.value = await searchRecommendations()
  } catch {
    recommendations.value = { posts: [], users: [], stocks: [] }
  }
}

function saveHistory(kw) {
  const history = JSON.parse(localStorage.getItem("search_history") || "[]")
  const filtered = history.filter(h => h !== kw)
  filtered.unshift(kw)
  const trimmed = filtered.slice(0, 10)
  localStorage.setItem("search_history", JSON.stringify(trimmed))
  historyKeywords.value = trimmed.slice(0, 5)
}

function handleInput() {
  if (debounceTimer) clearTimeout(debounceTimer)
  const kw = keyword.value.trim()
  if (kw.length >= 2) {
    debounceTimer = setTimeout(async () => {
      try {
        const data = await searchSuggestions(kw)
        suggestions.value = data
      } catch { suggestions.value = null }
    }, 250)
  } else {
    suggestions.value = null
  }
}

function handleKeydown(e) {
  if (e.key === "Enter") {
    suggestions.value = null
    doSearch(1)
  }
}

// 点击联想词 → 填入并搜索
function applySuggestion(text) {
  keyword.value = text
  suggestions.value = null
  inputFocused.value = false
  doSearch(1)
}

// 点击历史词
function applyHistory(kw) {
  keyword.value = kw
  suggestions.value = null
  doSearch(1)
}

function clearKeyword() {
  keyword.value = ""
  suggestions.value = null
}

function onFilterChange() {
  doSearch(1)
}

function handleLike(postId) { postsStore.togglePostLike(postId) }
function handleCollect(postId) { postsStore.togglePostCollect(postId) }
async function handleFollow(userId) {
  if (!auth.isLoggedIn) { toast.info('请先登录'); return }
  const user = [...results.value, ...(recommendations.value.users || [])].find(item => item.result_type === "user" && item.id === userId)
  try {
    const data = await toggleFollow(userId)
    if (user && data) {
      user.is_followed = data.is_followed
      user.followers_count = data.followers_count
    }
    toast.success(user?.is_followed ? '已关注' : '已取消关注')
  } catch (err) {
    toast.error(err.message || '操作失败')
  }
}
async function handleShare(postId) {
  if (!auth.isLoggedIn) { toast.info('请先登录'); return }
  const post = results.value.find(p => p.id === postId)
  if (post) post.share_count = (post.share_count || 0) + 1
  try {
    const { sharePost } = await import('../api/posts')
    const data = await sharePost(postId, 'timeline', '')
    if (post && data) post.share_count = data.share_count
    toast.success('已转发到动态')
  } catch (err) {
    if (post) post.share_count = (post.share_count || 1) - 1
    toast.error(err.message || '转发失败')
  }
}
function handlePageChange(p) { doSearch(p) }

function isPost(item) {
  return !item.result_type || item.result_type === "post"
}

function clearHistory() {
  localStorage.removeItem("search_history")
  historyKeywords.value = []
}
</script>

<template>
    <div class="search-page">
      <!-- 搜索框 -->
      <div class="search-header">
        <div :class="['search-box', { 'search-box--focused': inputFocused }]">
          <AppIcon name="search" :size="20" class="search-box__icon" />
          <input
            v-model="keyword"
            type="text"
            placeholder="搜索股票代码/名称/话题/用户..."
            class="search-box__input"
            @input="handleInput"
            @keydown="handleKeydown"
            @focus="inputFocused = true"
            @blur="inputFocused = false"
          >
          <button v-if="keyword" class="search-box__clear" @mousedown.prevent="clearKeyword">
            <AppIcon name="close" :size="14" />
          </button>
          <button class="search-box__btn" @click="doSearch(1)">搜索</button>
        </div>

        <!-- 搜索联想 / 历史 -->
        <div v-if="inputFocused && !searched" class="search-panel">
          <!-- 联想词 -->
          <div v-if="showSuggestions" class="suggestions">
            <div v-if="suggestions.stocks?.length" class="suggestions__group">
              <div class="suggestions__label">📈 股票</div>
              <div
                v-for="s in suggestions.stocks"
                :key="s.code"
                class="suggestions__item"
                @mousedown.prevent="applySuggestion(s.code + ' ' + s.name)"
              >{{ s.code }} <strong>{{ s.name }}</strong> <span class="suggestions__market">({{ s.market }})</span></div>
            </div>
            <div v-if="suggestions.users?.length" class="suggestions__group">
              <div class="suggestions__label">👤 用户</div>
              <div
                v-for="u in suggestions.users"
                :key="u.id"
                class="suggestions__item"
                @mousedown.prevent="router.push('/users/' + u.id)"
              >{{ u.nickname }} <span v-if="u.username" class="suggestions__username">@{{ u.username }}</span></div>
            </div>
            <div v-if="suggestions.topics?.length" class="suggestions__group">
              <div class="suggestions__label">💬 话题</div>
              <div
                v-for="t in suggestions.topics"
                :key="t"
                class="suggestions__item"
                @mousedown.prevent="applySuggestion(t)"
              >#{{ t }}</div>
            </div>
          </div>

          <!-- 搜索历史 -->
          <div v-else-if="!keyword && historyKeywords.length" class="history-panel">
            <div class="history-panel__header">
              <span class="history-panel__title">搜索历史</span>
              <button class="history-panel__clear" @click="clearHistory">清空</button>
            </div>
            <div class="history-panel__list">
              <span
                v-for="h in historyKeywords"
                :key="h"
                class="history-panel__item"
                @mousedown.prevent="applyHistory(h)"
              >{{ h }}</span>
            </div>
          </div>
        </div>
      </div>

      <!-- 筛选栏 -->
      <div class="filters">
        <!-- 类型标签 -->
        <div class="filter-group">
          <button
            v-for="t in [{ v: 'all', l: '全部' }, { v: 'post', l: '帖子' }, { v: 'user', l: '用户' }, { v: 'stock', l: '股票' }, { v: 'group', l: '群组' }]"
            :key="t.v"
            :class="['filter-chip', { 'filter-chip--active': searchType === t.v }]"
            @click="searchType = t.v; onFilterChange()"
          >{{ t.l }}</button>
        </div>

        <span class="filter-divider" />

        <!-- 时间 -->
        <select v-model="timeRange" class="filter-select" @change="onFilterChange()">
          <option value="all">全部时间</option>
          <option value="day">今天</option>
          <option value="week">本周</option>
          <option value="month">本月</option>
        </select>

        <!-- 排序 -->
        <select v-model="sortBy" class="filter-select" @change="onFilterChange()">
          <option value="relevance">按相关度</option>
          <option value="time">按时间</option>
          <option value="heat">按热度</option>
        </select>

        <span class="filter-divider" />

        <!-- 精华 -->
        <button
          :class="['filter-chip filter-chip--toggle', { 'filter-chip--active': isElite }]"
          @click="isElite = !isElite; onFilterChange()"
        >⭐ 精华</button>

        <!-- 市场 -->
        <select v-model="market" class="filter-select" @change="onFilterChange()">
          <option v-for="m in marketOptions" :key="m.value" :value="m.value">{{ m.label }}</option>
        </select>
      </div>

      <!-- 搜索结果 -->
      <div v-if="searched">
        <p class="results-count">
          共找到 <strong>{{ total }}</strong> 条结果
          <span v-if="keyword"> — "{{ keyword }}"</span>
        </p>

        <Loading v-if="loading" variant="skeleton" :rows="2" />

        <template v-else-if="results.length">
          <div class="result-list">
            <template v-for="item in results" :key="`${item.result_type || 'post'}-${item.id || item.code}`">
              <PostCard
                v-if="isPost(item)"
                :post="item"
                @like="handleLike"
                @collect="handleCollect"
                @share="handleShare"
              />
              <UserCard
                v-else-if="item.result_type === 'user'"
                :user="item"
                @follow="handleFollow"
                @click="router.push('/users/' + item.id)"
              />
              <div
                v-else-if="item.result_type === 'group'"
                class="plain-card"
                @click="router.push('/groups/' + item.id)"
              >
                <strong>{{ item.name }}</strong>
                <p>{{ item.description || '暂无群组简介' }}</p>
                <span>{{ item.member_count || 0 }} 成员 · {{ item.visibility === 'public' ? '公开' : '私密' }}</span>
              </div>
              <div v-else-if="item.result_type === 'stock'" class="plain-card">
                <strong>{{ item.code }} {{ item.name }}</strong>
                <p>{{ item.market }}</p>
              </div>
            </template>
          </div>
        </template>

        <EmptyState
          v-else
          icon="search"
          title="未找到相关内容"
          description="尝试更换关键词或筛选条件"
        />

        <Pagination
          v-if="total > 20"
          :current="page"
          :total="total"
          :size="20"
          @update:current="handlePageChange"
        />
      </div>

      <!-- 未搜索 -->
      <div v-else class="recommendations">
        <EmptyState icon="search" title="搜索投资话题" description="输入股票代码、名称或话题关键词搜索" />

        <section v-if="recommendations.posts?.length" class="recommend-section">
          <h2>推荐帖子</h2>
          <div class="result-list">
            <PostCard
              v-for="post in recommendations.posts"
              :key="post.id"
              :post="post"
              @like="handleLike"
              @collect="handleCollect"
              @share="handleShare"
            />
          </div>
        </section>

        <section v-if="recommendations.users?.length" class="recommend-section">
          <h2>推荐用户</h2>
          <div class="user-list">
            <UserCard
              v-for="user in recommendations.users"
              :key="user.id"
              :user="user"
              @follow="handleFollow"
              @click="router.push('/users/' + user.id)"
            />
          </div>
        </section>

        <section v-if="recommendations.stocks?.length" class="recommend-section">
          <h2>推荐股票</h2>
          <div class="stock-list">
            <div v-for="stock in recommendations.stocks" :key="stock.code" class="plain-card">
              <strong>{{ stock.code }} {{ stock.name }}</strong>
              <p>{{ stock.market }}</p>
            </div>
          </div>
        </section>
      </div>
    </div>
</template>

<style scoped>
.search-page { max-width: var(--content-max-width-wide); }

.search-header { margin-bottom: 20px; position: relative; }

.search-box {
  align-items: center;
  background: var(--color-bg-card);
  border: 2px solid var(--color-border-input);
  border-radius: var(--radius-2xl);
  display: flex;
  gap: 10px;
  overflow: hidden;
  padding: 0 16px;
  transition: border-color var(--duration-fast) var(--ease-out),
              box-shadow var(--duration-fast) var(--ease-out);
}

.search-box--focused,
.search-box:focus-within {
  border-color: var(--color-primary);
  box-shadow: 0 0 0 4px var(--color-primary-ring);
}

.search-box__icon { color: var(--color-text-muted); flex-shrink: 0; }
.search-box__input {
  border: 0;
  flex: 1;
  font: inherit;
  font-size: var(--font-size-lg);
  outline: none;
  padding: 14px 0;
  background: transparent;
  color: var(--color-text-primary);
}
.search-box__input::placeholder { color: var(--color-text-placeholder); }
.search-box__clear {
  background: none;
  border: 0;
  color: var(--color-text-muted);
  cursor: pointer;
  padding: 4px;
  border-radius: var(--radius-full);
}
.search-box__clear:hover { color: var(--color-text-secondary); background: var(--color-bg-hover); }
.search-box__btn {
  background: var(--color-primary);
  border: 0;
  border-radius: var(--radius-lg);
  color: var(--color-bg-card);
  cursor: pointer;
  flex-shrink: 0;
  font: inherit;
  font-size: var(--font-size-base);
  font-weight: var(--font-weight-medium);
  padding: 10px 22px;
  transition: background var(--duration-fast) var(--ease-out);
}
.search-box__btn:hover { background: var(--color-primary-hover); }

/* 联想 & 历史面板 */
.search-panel {
  background: var(--color-bg-card);
  border: 1px solid var(--color-border);
  border-radius: var(--radius-xl);
  box-shadow: var(--shadow-lg);
  left: 0;
  position: absolute;
  right: 0;
  top: calc(100% + 4px);
  z-index: var(--z-dropdown);
}

.suggestions__group { padding: 6px 0; }
.suggestions__group + .suggestions__group { border-top: 1px solid var(--color-border-light); }

.suggestions__label {
  color: var(--color-text-muted);
  font-size: 11px;
  font-weight: 600;
  padding: 4px 16px 8px;
  text-transform: uppercase;
  letter-spacing: 0.5px;
}

.suggestions__item {
  color: var(--color-text-body);
  cursor: pointer;
  font-size: var(--font-size-base);
  padding: 8px 16px;
  transition: background var(--duration-fast) var(--ease-out);
}

.suggestions__item:hover { background: var(--color-primary-light); }

.suggestions__market {
  color: var(--color-text-muted);
  font-size: var(--font-size-xs);
}

.suggestions__username {
  color: var(--color-text-muted);
  font-size: var(--font-size-xs);
  margin-left: 4px;
}

/* 搜索历史 */
.history-panel { padding: 8px 0; }
.history-panel__header {
  align-items: center;
  display: flex;
  justify-content: space-between;
  padding: 4px 16px 8px;
}
.history-panel__title { color: var(--color-text-muted); font-size: 11px; font-weight: 600; text-transform: uppercase; }
.history-panel__clear { background: none; border: 0; color: var(--color-text-muted); cursor: pointer; font: inherit; font-size: 11px; }
.history-panel__clear:hover { color: var(--color-danger); }
.history-panel__list { display: flex; flex-wrap: wrap; gap: 6px; padding: 0 16px 8px; }
.history-panel__item {
  background: var(--color-bg-hover);
  border-radius: var(--radius-pill);
  color: var(--color-text-secondary);
  cursor: pointer;
  font-size: var(--font-size-sm);
  padding: 4px 12px;
  transition: background var(--duration-fast) var(--ease-out), color var(--duration-fast) var(--ease-out);
}
.history-panel__item:hover { background: var(--color-primary-light); color: var(--color-primary); }

/* 筛选栏 */
.filters {
  align-items: center;
  display: flex;
  flex-wrap: wrap;
  gap: 8px;
  margin-bottom: 24px;
}

.filter-group { display: flex; gap: 4px; }

.filter-chip {
  background: var(--color-bg-card);
  border: 1px solid var(--color-border-input);
  border-radius: var(--radius-pill);
  color: var(--color-text-secondary);
  cursor: pointer;
  font: inherit;
  font-size: var(--font-size-sm);
  padding: 7px 16px;
  transition: all var(--duration-fast) var(--ease-out);
}

.filter-chip:hover { border-color: var(--color-primary); color: var(--color-primary); }

.filter-chip--active {
  background: var(--color-primary);
  border-color: var(--color-primary);
  color: var(--color-bg-card);
}

.filter-chip--toggle { display: inline-flex; align-items: center; gap: 4px; }

.filter-divider {
  background: var(--color-border-light);
  height: 20px;
  width: 1px;
}

.filter-select {
  background: var(--color-bg-card);
  border: 1px solid var(--color-border-input);
  border-radius: var(--radius-pill);
  color: var(--color-text-body);
  cursor: pointer;
  font: inherit;
  font-size: var(--font-size-sm);
  padding: 7px 28px 7px 12px;
  appearance: none;
  background-image: url("data:image/svg+xml,%3Csvg xmlns='http://www.w3.org/2000/svg' width='12' height='12' viewBox='0 0 24 24' fill='none' stroke='%239ca3af' stroke-width='2'%3E%3Cpath d='m6 9 6 6 6-6'/%3E%3C/svg%3E");
  background-repeat: no-repeat;
  background-position: right 8px center;
}

.filter-select:focus {
  border-color: var(--color-primary);
  box-shadow: 0 0 0 3px var(--color-primary-ring);
  outline: none;
}

.results-count {
  color: var(--color-text-secondary);
  font-size: var(--font-size-base);
  margin: 0 0 16px;
}
.results-count strong { color: var(--color-text-primary); }

.post-list,
.result-list,
.recommendations { display: grid; gap: 14px; }

.recommend-section { display: grid; gap: 12px; }
.recommend-section h2 {
  font-size: var(--font-size-lg);
  margin: 10px 0 0;
}

.plain-card {
  background: var(--color-bg-card);
  border: 1px solid var(--color-border);
  border-radius: var(--radius-lg);
  cursor: pointer;
  padding: 16px;
}

.plain-card:hover { box-shadow: 0 2px 8px rgba(15, 23, 42, 0.06); }
.plain-card strong { color: var(--color-text-primary); }
.plain-card p {
  color: var(--color-text-secondary);
  margin: 6px 0;
}
.plain-card span {
  color: var(--color-text-muted);
  font-size: var(--font-size-sm);
}

.stock-list {
  display: grid;
  gap: 12px;
  grid-template-columns: repeat(auto-fill, minmax(220px, 1fr));
}

.user-list {
  display: grid;
  gap: 12px;
  grid-template-columns: repeat(auto-fill, minmax(280px, 1fr));
}

@media (max-width: 780px) {
  .filters { gap: 6px; }
  .filter-chip { font-size: 12px; padding: 6px 12px; }
  .filter-select { font-size: 12px; padding: 6px 24px 6px 10px; }
  .filter-divider { display: none; }
  .user-list { grid-template-columns: 1fr; }
}
</style>
