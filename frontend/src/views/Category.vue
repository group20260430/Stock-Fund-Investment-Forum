<script setup>
import { ref, computed, onMounted } from 'vue'
import { useRoute } from 'vue-router'
import PostCard from '../components/post/PostCard.vue'
import Loading from '../components/common/Loading.vue'
import EmptyState from '../components/common/EmptyState.vue'
import Pagination from '../components/common/Pagination.vue'
import { usePostsStore } from '../stores/posts'
import { useAuthStore } from '../stores/auth'
import { useToastStore } from '../stores/toast'

const route = useRoute()
const postsStore = usePostsStore()
const auth = useAuthStore()
const toast = useToastStore()

const categoryMap = {
  1: '综合讨论', 2: '股票市场', 3: '基金投资',
  4: '问答求助', 5: '投资策略',
  6: '科技公司', 7: '金融公司', 8: '医药公司',
  9: '消费公司', 10: '新能源', 11: '制造业',
  12: 'A股', 13: '港股', 14: '美股', 15: '期货',
  16: '价值投资', 17: '量化投资',
  19: '新股/新债', 20: '宏观策略',
  21: '新手提问', 22: '投资解惑',
}
const categoryName = computed(() => categoryMap[route.params.id] || '板块')

onMounted(() => {
  postsStore.pagination.page = 1
  postsStore.loadPosts({ category_id: route.params.id })
})

async function handleLike(postId) {
  if (!auth.isLoggedIn) return
  await postsStore.togglePostLike(postId)
}

async function handleCollect(postId) {
  if (!auth.isLoggedIn) return
  await postsStore.togglePostCollect(postId)
}

async function handleShare(postId) {
  if (!auth.isLoggedIn) { toast.info('请先登录'); return }
  // 乐观更新
  const post = postsStore.list.find(p => p.id === postId)
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

function handlePageChange(page) {
  postsStore.pagination.page = page
  postsStore.loadPosts({ category_id: route.params.id })
}
</script>

<template>
    <header class="toolbar">
      <div>
        <h1>{{ categoryName }}</h1>
        <p>共 {{ postsStore.pagination.total }} 篇帖子</p>
      </div>
    </header>

    <Loading v-if="postsStore.loading" variant="skeleton" :rows="3" />
    <EmptyState
      v-else-if="!postsStore.list.length"
      icon="📝"
      title="暂无帖子"
      action-label="发布帖子"
      @action="$router.push('/posts/new')"
    />
    <div v-else class="post-list">
      <PostCard
        v-for="post in postsStore.list"
        :key="post.id"
        :post="post"
        @like="handleLike"
        @collect="handleCollect"
        @share="handleShare"
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

<style scoped>
.toolbar { margin-bottom: 24px; }
.toolbar h1 { font-size: 28px; margin: 0 0 8px; }
.toolbar p { color: var(--color-text-secondary); margin: 0; }

.post-list { display: grid; gap: 14px; }
</style>
