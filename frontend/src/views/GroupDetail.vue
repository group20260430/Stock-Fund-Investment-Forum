<script setup>
import { ref, onMounted } from 'vue'
import { useRoute } from 'vue-router'
import AppLayout from '../components/layout/AppLayout.vue'
import PostCard from '../components/post/PostCard.vue'
import Loading from '../components/common/Loading.vue'
import EmptyState from '../components/common/EmptyState.vue'
import { fetchGroups, joinGroup } from '../api/groups'
import { usePostsStore } from '../stores/posts'

const route = useRoute()
const postsStore = usePostsStore()
const group = ref(null)
const loading = ref(true)
const joining = ref(false)

onMounted(async () => {
  try {
    const data = await fetchGroups({ type: 'my' })
    const list = Array.isArray(data) ? data : (data?.items || [])
    group.value = list.find(g => String(g.id) === String(route.params.id))
  } catch (err) {
    console.error('加载群组详情失败:', err.message)
  } finally {
    loading.value = false
  }
})

async function handleJoin() {
  joining.value = true
  try {
    await joinGroup(route.params.id)
    if (group.value) group.value.is_member = true
  } catch (err) {
    console.error('加入群组失败:', err.message)
  } finally {
    joining.value = false
  }
}

function handleLike(postId) { postsStore.togglePostLike(postId) }
</script>

<template>
  <AppLayout>
    <Loading v-if="loading" variant="skeleton" :rows="1" />

    <template v-else-if="group">
      <header class="group-header">
        <h1>{{ group.name }}</h1>
        <p>{{ group.description }}</p>
        <div class="group-header__meta">
          <span>{{ group.member_count || 0 }} 成员</span>
          <span>{{ group.visibility === 'public' ? '公开' : '私密' }}</span>
        </div>
        <button
          v-if="!group.is_member"
          class="join-btn"
          :disabled="joining"
          @click="handleJoin"
        >
          {{ joining ? '加入中...' : '+ 加入群组' }}
        </button>
      </header>

      <EmptyState icon="💬" title="群组讨论" description="暂无讨论内容" />
    </template>

    <EmptyState v-else icon="🔍" title="群组不存在" />
  </AppLayout>
</template>

<style scoped>
.group-header {
  background: var(--color-bg-card);
  border: 1px solid var(--color-border);
  border-radius: 10px;
  margin-bottom: 24px;
  padding: 24px;
}

.group-header h1 { font-size: 24px; margin: 0 0 8px; }
.group-header p { color: var(--color-text-secondary); font-size: 14px; margin: 0 0 12px; }

.group-header__meta {
  color: var(--color-text-muted);
  display: flex;
  font-size: 13px;
  gap: 16px;
  margin-bottom: 16px;
}

.join-btn {
  background: var(--color-primary);
  border: 0;
  border-radius: 8px;
  color: var(--color-bg-card);
  cursor: pointer;
  font: inherit;
  font-size: 14px;
  padding: 10px 24px;
}

.join-btn:hover:not(:disabled) { background: var(--color-primary-hover); }
.join-btn:disabled { opacity: 0.7; cursor: not-allowed; }
</style>
