<script setup>
import { ref, onMounted } from 'vue'
import { useRoute } from 'vue-router'
import AppLayout from '../components/layout/AppLayout.vue'
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
  <AppLayout>
    <header class="toolbar">
      <div>
        <h1>{{ route.params.id === '1' ? '综合讨论' : route.params.id === '2' ? '股票市场' : route.params.id === '3' ? '基金投资' : route.params.id === '4' ? '问答求助' : route.params.id === '5' ? '投资策略' : '板块' }}</h1>
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
  </AppLayout>
</template>

<style scoped>
.toolbar { margin-bottom: 24px; }
.toolbar h1 { font-size: 28px; margin: 0 0 8px; }
.toolbar p { color: var(--color-text-secondary); margin: 0; }

.post-list { display: grid; gap: 14px; }
</style>
