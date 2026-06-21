<script setup>
import { ref, onMounted, computed } from 'vue'
import { useRoute } from 'vue-router'
import { useAuthStore } from '../stores/auth'
import { useUserStore } from '../stores/user'
import { usePostsStore } from '../stores/posts'
import { toggleFollow } from '../api/users'
import AppLayout from '../components/layout/AppLayout.vue'
import UserProfileComponent from '../components/user/UserProfile.vue'
import PostCard from '../components/post/PostCard.vue'
import Loading from '../components/common/Loading.vue'
import ErrorState from '../components/common/ErrorState.vue'
import EmptyState from '../components/common/EmptyState.vue'
import Pagination from '../components/common/Pagination.vue'

const route = useRoute()
const auth = useAuthStore()
const userStore = useUserStore()
const postsStore = usePostsStore()

const activeTab = ref('posts') // posts | collections | achievements

const isOwnProfile = computed(() => {
  return auth.user && (route.params.id === 'me' || String(auth.user.id) === String(route.params.id))
})

onMounted(async () => {
  const userId = route.params.id === 'me' && auth.user ? auth.user.id : route.params.id
  await userStore.loadUserProfile(userId)
  if (userStore.profile) {
    await postsStore.loadPosts({ /* 可按用户筛选 */ })
  }
})

async function handleFollow(userId) {
  if (!auth.isLoggedIn) return
  try {
    const result = await toggleFollow(userId)
    if (userStore.profile) {
      userStore.profile.is_followed = result.is_followed
      userStore.profile.followers_count = result.followers_count
    }
  } catch (err) {
    console.error('关注失败:', err.message)
  }
}

async function handleLike(postId) {
  if (!auth.isLoggedIn) return
  await postsStore.togglePostLike(postId)
}

function handlePageChange(page) {
  postsStore.pagination.page = page
  postsStore.loadPosts()
}

const user = computed(() => userStore.profile)
</script>

<template>
  <AppLayout>
    <Loading v-if="userStore.loading" variant="skeleton" :rows="1" />
    <ErrorState
      v-else-if="userStore.error"
      :message="userStore.error"
      @retry="userStore.loadUserProfile(route.params.id)"
    />
    <template v-else-if="user">
      <UserProfileComponent
        :user="user"
        :is-own="isOwnProfile"
        @follow="handleFollow"
        @edit="$router.push('/me/settings')"
      />

      <!-- 标签页 -->
      <div class="tabs">
        <button :class="['tab', { 'tab--active': activeTab === 'posts' }]" @click="activeTab = 'posts'">
          帖子
        </button>
        <button :class="['tab', { 'tab--active': activeTab === 'collections' }]" @click="activeTab = 'collections'">
          收藏
        </button>
        <button :class="['tab', { 'tab--active': activeTab === 'achievements' }]" @click="activeTab = 'achievements'">
          成就
        </button>
      </div>

      <!-- 帖子列表 -->
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
          <PostCard
            v-for="post in postsStore.list"
            :key="post.id"
            :post="post"
            @like="handleLike"
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

      <!-- 收藏 (TODO) -->
      <EmptyState v-else-if="activeTab === 'collections'" icon="⭐" title="收藏列表" description="功能开发中" />

      <!-- 成就 -->
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
