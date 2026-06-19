<script setup>
import { ref, onMounted } from 'vue'
import { useRoute } from 'vue-router'
import AppLayout from '../components/layout/AppLayout.vue'
import PostCard from '../components/post/PostCard.vue'
import UserCard from '../components/user/UserCard.vue'
import Loading from '../components/common/Loading.vue'
import EmptyState from '../components/common/EmptyState.vue'
import Pagination from '../components/common/Pagination.vue'
import { search as searchApi, searchSuggestions } from '../api/search'
import { usePostsStore } from '../stores/posts'

const route = useRoute()
const postsStore = usePostsStore()

const keyword = ref(route.query.keyword || '')
const searchType = ref('all') // all | post | user | stock
const timeRange = ref('all')
const sortBy = ref('relevance')
const results = ref([])
const users = ref([])
const suggestions = ref(null)
const loading = ref(false)
const searched = ref(false)
const total = ref(0)
const page = ref(1)

onMounted(() => {
  if (keyword.value) doSearch()
})

async function doSearch(p = 1) {
  if (!keyword.value.trim()) return
  loading.value = true
  searched.value = true
  page.value = p
  try {
    const data = await searchApi({
      keyword: keyword.value.trim(),
      type: searchType.value,
      time_range: timeRange.value,
      sort: sortBy.value,
      page: p,
      size: 20,
    })
    results.value = data.items || []
    total.value = data.total || 0
  } catch (err) {
    console.error('搜索失败:', err.message)
  } finally {
    loading.value = false
  }
}

async function handleInput(e) {
  if (e.key === 'Enter') doSearch(1)
  // 搜索联想
  if (keyword.value.trim().length >= 2) {
    try {
      const data = await searchSuggestions(keyword.value.trim())
      suggestions.value = data
    } catch { suggestions.value = null }
  } else {
    suggestions.value = null
  }
}

function handleLike(postId) { postsStore.togglePostLike(postId) }
function handlePageChange(p) { doSearch(p) }
</script>

<template>
  <AppLayout>
    <!-- 搜索框 -->
    <div class="search-header">
      <div class="search-box">
        <span class="search-box__icon">🔍</span>
        <input
          v-model="keyword"
          type="text"
          placeholder="搜索股票代码/名称/话题/用户..."
          class="search-box__input"
          @keydown="handleInput"
        >
        <button class="search-box__btn" @click="doSearch(1)">搜索</button>
      </div>

      <!-- 搜索联想 -->
      <div v-if="suggestions" class="suggestions">
        <div v-if="suggestions.stocks?.length" class="suggestions__group">
          <div class="suggestions__label">📈 股票</div>
          <div
            v-for="s in suggestions.stocks"
            :key="s.code"
            class="suggestions__item"
          >
            {{ s.code }} {{ s.name }} ({{ s.market }})
          </div>
        </div>
        <div v-if="suggestions.users?.length" class="suggestions__group">
          <div class="suggestions__label">👤 用户</div>
          <div
            v-for="u in suggestions.users"
            :key="u.id"
            class="suggestions__item"
            @click="$router.push(`/users/${u.id}`)"
          >
            {{ u.nickname }}
          </div>
        </div>
        <div v-if="suggestions.topics?.length" class="suggestions__group">
          <div class="suggestions__label">💬 话题</div>
          <div
            v-for="t in suggestions.topics"
            :key="t"
            class="suggestions__item"
          >
            {{ t }}
          </div>
        </div>
      </div>
    </div>

    <!-- 筛选器 -->
    <div class="filters">
      <select v-model="searchType" class="filter-select" @change="doSearch(1)">
        <option value="all">全部</option>
        <option value="post">帖子</option>
        <option value="user">用户</option>
        <option value="stock">股票</option>
      </select>
      <select v-model="timeRange" class="filter-select" @change="doSearch(1)">
        <option value="all">全部时间</option>
        <option value="day">今天</option>
        <option value="week">本周</option>
        <option value="month">本月</option>
      </select>
      <select v-model="sortBy" class="filter-select" @change="doSearch(1)">
        <option value="relevance">按相关度</option>
        <option value="time">按时间</option>
        <option value="heat">按热度</option>
      </select>
    </div>

    <!-- 搜索结果 -->
    <div v-if="searched">
      <p class="results-count">共找到 {{ total }} 条结果</p>

      <Loading v-if="loading" variant="skeleton" :rows="2" />
      <EmptyState
        v-else-if="!results.length"
        icon="🔍"
        title="未找到相关内容"
        description="尝试更换关键词或筛选条件"
      />
      <div v-else class="post-list">
        <PostCard
          v-for="item in results"
          :key="item.id"
          :post="item"
          @like="handleLike"
        />
      </div>

      <Pagination
        v-if="total > 20"
        :current="page"
        :total="total"
        :size="20"
        @update:current="handlePageChange"
      />
    </div>

    <!-- 未搜索时的占位 -->
    <EmptyState v-else icon="🔍" title="搜索投资话题" description="输入股票代码、名称或话题关键词搜索" />
  </AppLayout>
</template>

<style scoped>
.search-header { margin-bottom: 16px; position: relative; }

.search-box {
  align-items: center;
  background: var(--color-bg-card);
  border: 2px solid var(--color-border-input);
  border-radius: 12px;
  display: flex;
  gap: 12px;
  overflow: hidden;
  padding: 0 16px;
  transition: border-color 0.2s;
}

.search-box:focus-within {
  border-color: var(--color-primary);
  box-shadow: 0 0 0 3px var(--color-primary-ring);
}

.search-box__icon { font-size: 18px; color: var(--color-text-muted); }

.search-box__input {
  border: 0;
  flex: 1;
  font: inherit;
  font-size: 16px;
  outline: none;
  padding: 14px 0;
}

.search-box__btn {
  background: var(--color-primary);
  border: 0;
  border-radius: 6px;
  color: var(--color-bg-card);
  cursor: pointer;
  font: inherit;
  font-size: 14px;
  padding: 8px 20px;
}

/* 搜索联想 */
.suggestions {
  background: var(--color-bg-card);
  border: 1px solid var(--color-border);
  border-radius: 10px;
  box-shadow: 0 10px 25px var(--color-bg-overlay);
  left: 0;
  position: absolute;
  right: 0;
  top: calc(100% + 4px);
  z-index: 20;
}

.suggestions__group { padding: 8px 0; }
.suggestions__group + .suggestions__group { border-top: 1px solid var(--color-border-light); }

.suggestions__label {
  color: var(--color-text-muted);
  font-size: 11px;
  font-weight: 600;
  padding: 4px 16px 8px;
  text-transform: uppercase;
}

.suggestions__item {
  color: var(--color-text-body);
  cursor: pointer;
  font-size: 14px;
  padding: 8px 16px;
}

.suggestions__item:hover { background: var(--color-bg-hover); }

.filters {
  display: flex;
  gap: 8px;
  margin-bottom: 20px;
}

.filter-select {
  background: var(--color-bg-card);
  border: 1px solid var(--color-border-input);
  border-radius: 6px;
  color: var(--color-text-body);
  font: inherit;
  font-size: 13px;
  padding: 8px 12px;
}

.results-count {
  color: var(--color-text-secondary);
  font-size: 14px;
  margin: 0 0 16px;
}

.post-list { display: grid; gap: 14px; }

@media (max-width: 780px) {
  .filters { flex-wrap: wrap; }
}
</style>
