﻿<script setup>
import { ref, watch, onMounted, computed } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { useAuthStore } from '../stores/auth'
import { useUserStore } from '../stores/user'
import { usePostsStore } from '../stores/posts'
import { useToastStore } from '../stores/toast'
import { fetchPointsHistory } from '../api/auth'
import { toggleFollow, setStarred } from '../api/users'
import AppLayout from '../components/layout/AppLayout.vue'
import UserProfileComponent from '../components/user/UserProfile.vue'
import PostCard from '../components/post/PostCard.vue'
import Loading from '../components/common/Loading.vue'
import ErrorState from '../components/common/ErrorState.vue'
import EmptyState from '../components/common/EmptyState.vue'
import Pagination from '../components/common/Pagination.vue'

const route = useRoute()
const router = useRouter()
const auth = useAuthStore()
const userStore = useUserStore()
const postsStore = usePostsStore()
const toast = useToastStore()

const activeTab = ref("posts")
const starring = ref(false)
const pointsHistory = ref([])
const pointsLoading = ref(false)
const loadedUserId = ref(null) // 追踪当前已加载的用户 ID

const levelThresholds = [
  { points: 0, level: 1 },
  { points: 100, level: 2 },
  { points: 300, level: 3 },
  { points: 600, level: 4 },
  { points: 1000, level: 5 },
  { points: 2000, level: 6 },
  { points: 5000, level: 7 },
  { points: 10000, level: 8 },
]

const isOwnProfile = computed(() => {
  if (!auth.user) return false
  return route.params.id === 'me' || String(auth.user.id) === String(route.params.id)
})

const levelProgress = computed(() => {
  const points = user.value?.points || 0
  const currentIndex = Math.max(0, levelThresholds.findIndex(item => item.level === (user.value?.level || 1)))
  const current = levelThresholds[currentIndex] || levelThresholds[0]
  const next = levelThresholds[currentIndex + 1]
  if (!next) return { percent: 100, nextLevel: null, remaining: 0 }
  return {
    percent: Math.min(100, Math.round(((points - current.points) / (next.points - current.points)) * 100)),
    nextLevel: next.level,
    remaining: Math.max(0, next.points - points),
  }
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
    if (isOwnProfile.value) loadPointsHistory()
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

async function loadPointsHistory() {
  pointsLoading.value = true
  try {
    const data = await fetchPointsHistory({ page: 1, size: 5 })
    pointsHistory.value = data.items || []
  } catch {
    pointsHistory.value = []
  } finally {
    pointsLoading.value = false
  }
}

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

function reasonText(reason) {
  return {
    daily_login: "每日登录",
    create_post: "发布帖子",
    create_comment: "发表评论",
    post_liked: "帖子被点赞",
    comment_liked: "评论被点赞",
    post_shared: "帖子被转发",
    gained_follower: "新增粉丝",
    delete_post: "删除帖子",
    delete_comment: "删除评论",
    post_unliked: "取消点赞",
    comment_unliked: "评论取消点赞",
    lost_follower: "失去粉丝",
  }[reason] || reason
}

function formatTime(t) {
  return t ? new Date(t).toLocaleString("zh-CN", { month: "2-digit", day: "2-digit", hour: "2-digit", minute: "2-digit" }) : ""
}
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
        <div class="points-card">
          <div>
            <span class="points-card__level">Lv.{{ user.level || 1 }}</span>
            <h2>{{ user.points || 0 }} 积分</h2>
            <p v-if="levelProgress.nextLevel">距离 Lv.{{ levelProgress.nextLevel }} 还差 {{ levelProgress.remaining }} 分</p>
            <p v-else>已达到当前最高等级</p>
          </div>
          <div class="points-card__bar">
            <span :style="{ width: levelProgress.percent + '%' }" />
          </div>
        </div>

        <div v-if="user.achievements?.badges?.length" class="badges-grid">
          <div v-for="badge in user.achievements.badges" :key="badge" class="badge-card">
            <span class="badge-card__icon">🏅</span>
            <strong>{{ badge }}</strong>
          </div>
        </div>
        <EmptyState v-else icon="🏆" title="暂无成就徽章" />

        <div v-if="isOwnProfile" class="points-history">
          <h3>最近积分记录</h3>
          <Loading v-if="pointsLoading" variant="skeleton" :rows="2" />
          <div v-else-if="pointsHistory.length" class="points-history__list">
            <div v-for="item in pointsHistory" :key="item.id" class="points-history__item">
              <span>{{ reasonText(item.reason) }}</span>
              <small>{{ formatTime(item.created_at) }}</small>
              <strong :class="{ 'points-history__negative': item.points_change < 0 }">
                {{ item.points_change > 0 ? '+' : '' }}{{ item.points_change }}
              </strong>
            </div>
          </div>
          <p v-else class="points-history__empty">暂无积分记录</p>
        </div>
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

.achievements { display: grid; gap: 16px; padding: 24px 0; }

.points-card {
  background: var(--color-bg-card);
  border: 1px solid var(--color-border);
  border-radius: 10px;
  display: grid;
  gap: 14px;
  padding: 20px;
}

.points-card h2 { font-size: 28px; margin: 6px 0; }
.points-card p { color: var(--color-text-secondary); margin: 0; }
.points-card__level {
  background: var(--color-primary-light);
  border-radius: var(--radius-pill);
  color: var(--color-primary);
  font-size: 13px;
  font-weight: 700;
  padding: 4px 10px;
}
.points-card__bar {
  background: var(--color-bg-hover);
  border-radius: var(--radius-pill);
  height: 8px;
  overflow: hidden;
}
.points-card__bar span {
  background: var(--color-primary);
  display: block;
  height: 100%;
}

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

.points-history {
  background: var(--color-bg-card);
  border: 1px solid var(--color-border);
  border-radius: 10px;
  padding: 20px;
}

.points-history h3 { font-size: 16px; margin: 0 0 12px; }
.points-history__list { display: grid; gap: 10px; }
.points-history__item {
  align-items: center;
  display: grid;
  gap: 8px;
  grid-template-columns: 1fr auto auto;
}
.points-history__item small,
.points-history__empty { color: var(--color-text-muted); }
.points-history__item strong { color: var(--color-success); }
.points-history__negative { color: var(--color-danger) !important; }
</style>
