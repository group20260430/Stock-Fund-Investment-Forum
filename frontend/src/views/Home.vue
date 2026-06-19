<script setup>
import { ref, onMounted, watch } from 'vue'
import { useRoute } from 'vue-router'
import { useAutoAnimate } from '@formkit/auto-animate/vue'
import { useAuthStore } from '../stores/auth'
import { usePostsStore } from '../stores/posts'
import { fetchHot } from '../api/social'
import { fetchIndices, fetchKline } from '../api/market'
import AppLayout from '../components/layout/AppLayout.vue'
import PostCard from '../components/post/PostCard.vue'
import MarketCard from '../components/common/MarketCard.vue'
import Loading from '../components/common/Loading.vue'
import ErrorState from '../components/common/ErrorState.vue'
import EmptyState from '../components/common/EmptyState.vue'
import Pagination from '../components/common/Pagination.vue'

const route = useRoute()
const auth = useAuthStore()
const postsStore = usePostsStore()

const sortType = ref('latest')
const isHotTab = ref(false)
const [postListRef] = useAutoAnimate({ duration: 250, easing: 'ease-out' })
const [hotListRef] = useAutoAnimate({ duration: 250, easing: 'ease-out' })

// 实时行情数据（从东方财富代理获取）
const indices = ref([])
const indexKlines = ref({})
const indicesLoading = ref(true)

const hotTopics = ref([])

// 默认展示的指数 ID
const DEFAULT_INDICES = '1.000001,1.000300,0.399001'

async function loadMarketData() {
  indicesLoading.value = true
  try {
    const data = await fetchIndices(DEFAULT_INDICES)
    indices.value = Array.isArray(data) ? data : []

    // 并行加载各指数 K 线（迷你走势图）
    const klinePromises = indices.value.map(item =>
      fetchKline(`1.${item.code}`, 101, 20).catch(() => [])
    )
    const klines = await Promise.all(klinePromises)
    indices.value.forEach((item, i) => {
      indexKlines.value[item.code] = klines[i] || []
    })
  } catch (err) {
    console.error('获取行情数据失败:', err.message)
  } finally {
    indicesLoading.value = false
  }
}

async function loadContent() {
  if (isHotTab.value) {
    await loadHot()
  } else {
    await postsStore.loadPosts({ sort: sortType.value })
  }
}

async function loadHot() {
  try {
    const data = await fetchHot({ period: 'daily' })
    hotTopics.value = Array.isArray(data) ? data : (data?.items || [])
  } catch (err) {
    console.error('加载热榜失败:', err.message)
  }
}

function handleSortChange(sort) {
  sortType.value = sort
  isHotTab.value = false
  postsStore.pagination.page = 1
  loadContent()
}

function handleTabHot() {
  isHotTab.value = true
  loadHot()
}

function handlePageChange(page) {
  postsStore.pagination.page = page
  if (isHotTab.value) {
    loadHot()
  } else {
    postsStore.loadPosts({ sort: sortType.value })
  }
}

async function handleLike(postId) {
  if (!auth.isLoggedIn) {
    // 未登录引导
    return
  }
  await postsStore.togglePostLike(postId)
}

async function handleCollect(postId) {
  if (!auth.isLoggedIn) return
  await postsStore.togglePostCollect(postId)
}

function handleRetry() {
  loadContent()
}

onMounted(() => {
  // 检查 URL 参数
  if (route.query.tab === 'hot') {
    isHotTab.value = true
  }
  loadContent()
  loadMarketData()
})
</script>

<template>
  <AppLayout>
    <!-- 标题栏 -->
    <header class="toolbar">
      <div>
        <h1>投资社区讨论</h1>
        <p>关注市场观点、基金配置与投资问答。</p>
      </div>
    </header>

    <!-- 实时行情卡片 -->
    <section class="market-strip" aria-label="市场概览">
      <!-- 加载骨架 -->
      <template v-if="indicesLoading && !indices.length">
        <div v-for="i in 3" :key="i" class="market-loading-skeleton">
          <div class="skeleton-line skeleton-line--short" />
          <div class="skeleton-line skeleton-line--tall" />
          <div class="skeleton-line skeleton-line--medium" />
        </div>
      </template>

      <!-- 行情卡片 -->
      <MarketCard
        v-for="item in indices"
        :key="item.code"
        :data="item"
        :kline="indexKlines[item.code] || []"
        :loading="indicesLoading"
      />

      <!-- 错误降级：连代理都不可用 -->
      <div v-if="!indicesLoading && !indices.length" class="market-strip__error">
        <span>📡 行情数据暂不可用</span>
      </div>
    </section>

    <!-- 排序Tab -->
    <div class="tabs">
      <button
        :class="['tab', { 'tab--active': !isHotTab && sortType === 'latest' }]"
        @click="handleSortChange('latest')"
      >
        最新
      </button>
      <button
        :class="['tab', { 'tab--active': !isHotTab && sortType === 'hot' }]"
        @click="handleSortChange('hot')"
      >
        热门
      </button>
      <button
        :class="['tab', { 'tab--active': !isHotTab && sortType === 'elite' }]"
        @click="handleSortChange('elite')"
      >
        精华
      </button>
      <button
        :class="['tab', { 'tab--active': isHotTab }]"
        @click="handleTabHot"
      >
        🔥 热榜
      </button>
    </div>

    <!-- 热榜视图 -->
    <template v-if="isHotTab">
      <div v-if="hotTopics.length" ref="hotListRef" class="hot-list">
        <div v-for="(topic, idx) in hotTopics.slice(0, 10)" :key="idx" class="hot-item">
          <span class="hot-item__rank" :class="{ 'hot-item__rank--top3': idx < 3 }">{{ idx + 1 }}</span>
          <div class="hot-item__info">
            <strong>{{ topic.topic }}</strong>
            <span>{{ topic.heat_score || topic.discussion_count }} 讨论</span>
          </div>
        </div>
      </div>
      <EmptyState v-else icon="📊" title="暂无热榜数据" />
    </template>

    <!-- 帖子列表视图 -->
    <template v-else>
      <!-- 加载态 -->
      <Loading v-if="postsStore.loading && !postsStore.list.length" variant="skeleton" :rows="3" />

      <!-- 错误态 -->
      <ErrorState
        v-else-if="postsStore.error && !postsStore.list.length"
        :message="postsStore.error"
        @retry="handleRetry"
      />

      <!-- 空态 -->
      <EmptyState
        v-else-if="!postsStore.list.length"
        icon="📝"
        title="暂无帖子"
        description="还没有人发布帖子，来发表第一篇吧"
        action-label="发布帖子"
        @action="$router.push('/posts/new')"
      />

      <!-- 列表 -->
      <div v-else ref="postListRef" class="post-list">
        <PostCard
          v-for="post in postsStore.list"
          :key="post.id"
          :post="post"
          @like="handleLike"
          @collect="handleCollect"
        />
      </div>

      <Pagination
        v-if="postsStore.pagination.total > postsStore.pagination.size"
        :current="postsStore.pagination.page"
        :total="postsStore.pagination.total"
        :size="postsStore.pagination.size"
        @update:current="handlePageChange"
      />
    </template>
  </AppLayout>
</template>

<style scoped>
.toolbar {
  align-items: center;
  display: flex;
  gap: 20px;
  justify-content: space-between;
  margin-bottom: 24px;
}

.toolbar h1 {
  font-size: 28px;
  margin: 0 0 8px;
  color: var(--color-text-primary);
}

.toolbar p {
  color: var(--color-text-secondary);
  margin: 0;
  font-size: 14px;
}

/* 行情卡片 */
.market-strip {
  display: grid;
  gap: 12px;
  grid-template-columns: repeat(3, minmax(0, 1fr));
  margin-bottom: 24px;
}

.market-loading-skeleton {
  animation: pulse 1.6s ease-in-out infinite;
  background: var(--color-bg-card);
  border: 1px solid var(--color-border);
  border-radius: var(--radius-lg);
  display: grid;
  gap: 10px;
  padding: 16px;
}

.skeleton-line {
  background: var(--color-border);
  border-radius: 4px;
  height: 12px;
}

.skeleton-line--short { width: 40%; }
.skeleton-line--tall { height: 24px; width: 70%; }
.skeleton-line--medium { width: 55%; }

.market-strip__error {
  color: var(--color-text-muted);
  font-size: var(--font-size-sm);
  grid-column: 1 / -1;
  padding: 20px;
  text-align: center;
}

@keyframes pulse {
  0%, 100% { opacity: 1; }
  50% { opacity: 0.4; }
}

.text-up { color: var(--color-danger); }
.text-down { color: var(--color-success); }

/* Tab */
.tabs {
  border-bottom: 2px solid var(--color-border);
  display: flex;
  gap: 0;
  margin-bottom: 20px;
}

.tab {
  background: none;
  border: 0;
  border-bottom: 2px solid transparent;
  color: var(--color-text-secondary);
  cursor: pointer;
  font: inherit;
  font-size: 14px;
  font-weight: 500;
  margin-bottom: -2px;
  padding: 12px 20px;
  transition: color 0.15s, border-color 0.15s;
}

.tab:hover {
  color: var(--color-text-body);
}

.tab--active {
  border-bottom-color: var(--color-primary);
  color: var(--color-primary);
}

/* 热榜 */
.hot-list {
  background: var(--color-bg-card);
  border: 1px solid var(--color-border);
  border-radius: 8px;
  overflow: hidden;
}

.hot-item {
  align-items: center;
  border-bottom: 1px solid var(--color-border-light);
  cursor: pointer;
  display: flex;
  gap: 16px;
  padding: 14px 20px;
  transition: background 0.1s;
}

.hot-item:last-child {
  border-bottom: 0;
}

.hot-item:hover {
  background: var(--color-bg-hover);
}

.hot-item__rank {
  color: var(--color-text-muted);
  font-size: 16px;
  font-weight: 700;
  min-width: 24px;
  text-align: center;
}

.hot-item__rank--top3 {
  color: var(--color-danger);
}

.hot-item__info {
  display: grid;
  gap: 2px;
}

.hot-item__info strong {
  font-size: 15px;
  color: var(--color-text-primary);
}

.hot-item__info span {
  color: var(--color-text-muted);
  font-size: 12px;
}

/* 帖子列表 */
.post-list {
  display: grid;
  gap: 14px;
}

/* 移动端 */
@media (max-width: 780px) {
  .toolbar {
    align-items: stretch;
    flex-direction: column;
  }

  .toolbar h1 {
    font-size: 22px;
  }

  .market-strip {
    grid-template-columns: 1fr;
  }

  .tab {
    font-size: 13px;
    padding: 10px 14px;
  }
}
</style>
