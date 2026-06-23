<script setup>
import { ref, watch, onMounted, computed } from "vue"
import { useRoute, useRouter } from "vue-router"
import { useAuthStore } from "../stores/auth"
import { useUserStore } from "../stores/user"
import { usePostsStore } from "../stores/posts"
import { useToastStore } from "../stores/toast"
import { toggleFollow, setStarred } from "../api/users"
import AppLayout from "../components/layout/AppLayout.vue"
import UserProfileComponent from "../components/user/UserProfile.vue"
import PostCard from "../components/post/PostCard.vue"
import Loading from "../components/common/Loading.vue"
import ErrorState from "../components/common/ErrorState.vue"
import EmptyState from "../components/common/EmptyState.vue"
import Pagination from "../components/common/Pagination.vue"

const route = useRoute()
const router = useRouter()
const auth = useAuthStore()
const userStore = useUserStore()
const postsStore = usePostsStore()
const toast = useToastStore()

const activeTab = ref("posts")
const starring = ref(false)
const loadedUserId = ref(null) // 追踪当前已加载的用户 ID

const isOwnProfile = computed(() => {
  if (!auth.user) return false
  return route.params.id === 'me' || String(auth.user.id) === String(route.params.id)
})

/** 解析路由参数为数字用户 ID，供 API 调用使用 */
function resolveUserId() {
  if (route.params.id === 'me') {
    return auth.user?.id
  }
  const id = Number(route.params.id)
  return isNaN(id) ? null : id
}

async function loadProfileData(force = false) {
  const userId = resolveUserId()
  if (!userId) {
    if (route.params.id === 'me' && !auth.user) {
      router.push({ name: 'login', query: { redirect: route.fullPath } })
    }
    return
  }

  // 同一个用户 ID 已有缓存数据时跳过；force=true 时强制刷新
  if (!force && loadedUserId.value === userId && userStore.profile) return

  loadedUserId.value = userId
  // 先清空旧数据，确保 Loading 状态正常展示
  userStore.profile = null
  await userStore.loadUserProfile(userId)
  if (userStore.profile) {
    await postsStore.loadPosts({ user_id: userId })
  }
}

// 监听路由参数变化（切换账号或浏览不同用户时重新加载）
watch(
  () => route.params.id,
  () => { loadProfileData() }
)

// 监听登录用户变化（切换账号后 auth.user 更新时重新加载）
watch(
  () => auth.user?.id,
  (newUid, oldUid) => {
    if (newUid !== oldUid && route.params.id === 'me') {
      loadProfileData()
    }
  }
)

onMounted(() => { loadProfileData() })

async function handleFollow(userId) {
  if (!auth.isLoggedIn) return
  try {
    const result = await toggleFollow(Number(userId))
    if (userStore.profile) {
      userStore.profile.is_followed = result.is_followed
      userStore.profile.followers_count = result.followers_count
    }
  } catch (err) {
    console.error("关注失败:", err.message)
  }
}

async function handleStar(userId) {
  if (!auth.isLoggedIn || starring.value) return
  starring.value = true
  try {
    const isStarred = !userStore.profile.is_starred
    await setStarred(userId, isStarred)
    userStore.profile.is_starred = isStarred
    toast.success(isStarred ? "已设为星标用户" : "已取消星标")
  } catch (err) {
    toast.error(err.message || "操作失败")
  } finally {
    starring.value = false
  }
}

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
  const userId = resolveUserId()
  postsStore.loadPosts({ user_id: userId })
}

function handleAvatarUpdated(avatarUrl) {
  if (userStore.profile) {
    userStore.profile.avatar_url = avatarUrl
  }
}

function handleMessage(userId) {
  router.push({ name: 'messages-conversation', params: { userId } })
}

const user = computed(() => userStore.profile)
</script>

<template>
  <AppLayout>
    <Loading v-if="userStore.loading" variant="skeleton" :rows="1" />
    <ErrorState
      v-else-if="userStore.error"
      :message="userStore.error"
      @retry="loadProfileData(true)"
    />
    <template v-else-if="user">
      <UserProfileComponent
        :user="user"
        :is-own="isOwnProfile"
        @follow="handleFollow"
        @star="handleStar"
        @message="handleMessage"
        @edit="$router.push('/me/settings')"
        @avatar-updated="handleAvatarUpdated"
      />

      <!-- 标签页 -->
      <div class="tabs">
        <button :class="['tab', { 'tab--active': activeTab === 'posts' }]" @click="activeTab = 'posts'">帖子</button>
        <button :class="['tab', { 'tab--active': activeTab === 'collections' }]" @click="activeTab = 'collections'">收藏</button>
        <button :class="['tab', { 'tab--active': activeTab === 'achievements' }]" @click="activeTab = 'achievements'">成就</button>
      </div>

      <template v-if="activeTab === 'posts'">
        <Loading v-if="postsStore.loading" variant="skeleton" :rows="2" />
        <EmptyState
          v-else-if="!postsStore.list.length"
          icon="📝"
          :title="isOwnProfile ? '你还没有发布帖子' : '该用户暂无帖子'"
          :action-label="isOwnProfile ? '发布第一篇' : ''"
          @action="$router.push('/posts/new')"
        />
        <div v-else class="post-list">
          <PostCard v-for="post in postsStore.list" :key="post.id" :post="post" @like="handleLike" @collect="handleCollect" @share="handleShare" />
        </div>
        <Pagination
          v-if="postsStore.pagination.total > postsStore.pagination.size"
          :current="postsStore.pagination.page"
          :total="postsStore.pagination.total"
          :size="postsStore.pagination.size"
          @update:current="handlePageChange"
        />
      </template>

      <EmptyState v-else-if="activeTab === 'collections'" icon="⭐" title="收藏列表" description="功能开发中" />

      <div v-else class="achievements">
        <div v-if="user.achievements?.badges?.length" class="badges-grid">
          <div v-for="badge in user.achievements.badges" :key="badge" class="badge-card">
            <span class="badge-card__icon">🏅</span>
            <strong>{{ badge }}</strong>
          </div>
        </div>
        <EmptyState v-else icon="🏆" title="暂无成就徽章" />
      </div>
    </template>
  </AppLayout>
</template>

<style scoped>
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
}

.tab:hover { color: var(--color-text-body); }
.tab--active { border-bottom-color: var(--color-primary); color: var(--color-primary); }

.post-list { display: grid; gap: 14px; }

.achievements { padding: 24px 0; }

.badges-grid {
  display: grid;
  gap: 12px;
  grid-template-columns: repeat(auto-fill, minmax(140px, 1fr));
}

.badge-card {
  align-items: center;
  background: var(--color-bg-card);
  border: 1px solid var(--color-border);
  border-radius: 8px;
  display: flex;
  gap: 10px;
  padding: 16px;
}

.badge-card__icon { font-size: 24px; }
.badge-card strong { font-size: 14px; }
</style>
