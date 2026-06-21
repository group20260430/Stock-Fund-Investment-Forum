<script setup>
import { ref, onMounted, watch } from "vue"
import { useRoute, useRouter } from "vue-router"
import AppLayout from "../components/layout/AppLayout.vue"
import UserCard from "../components/user/UserCard.vue"
import Loading from "../components/common/Loading.vue"
import EmptyState from "../components/common/EmptyState.vue"
import Pagination from "../components/common/Pagination.vue"
import { fetchFollowing, fetchFollowers } from "../api/users"

const route = useRoute()
const router = useRouter()

const activeTab = ref(route.query.tab === "followers" ? "followers" : "following")
const userId = ref(route.params.id)
const users = ref([])
const loading = ref(true)
const total = ref(0)
const page = ref(1)
const pageSize = 20

onMounted(() => loadData())

watch(() => route.params.id, (val) => { userId.value = val; loadData() })

function switchTab(tab) {
  activeTab.value = tab
  router.replace({ query: { tab } })
  page.value = 1
  loadData()
}

async function loadData(p = 1) {
  loading.value = true
  page.value = p
  try {
    const params = { page: p, size: pageSize }
    const data = activeTab.value === "following"
      ? await fetchFollowing(userId.value, params)
      : await fetchFollowers(userId.value, params)
    users.value = data.items || data || []
    total.value = data.total || users.value.length
  } catch (err) {
    console.error("加载失败:", err.message)
  } finally {
    loading.value = false
  }
}

function handlePageChange(p) { loadData(p) }
</script>

<template>
  <AppLayout>
    <div class="follow-tabs">
      <button
        :class="['follow-tab', { 'follow-tab--active': activeTab === 'following' }]"
        @click="switchTab('following')"
      >关注</button>
      <button
        :class="['follow-tab', { 'follow-tab--active': activeTab === 'followers' }]"
        @click="switchTab('followers')"
      >粉丝</button>
    </div>

    <Loading v-if="loading" variant="skeleton" :rows="3" />

    <EmptyState
      v-else-if="!users.length"
      :icon="activeTab === 'following' ? '👥' : '👤'"
      :title="activeTab === 'following' ? '还没有关注任何人' : '还没有粉丝'"
      :description="activeTab === 'following' ? '去发现有趣的投资人吧' : '多发布优质内容，吸引更多粉丝'"
    />

    <div v-else class="user-list">
      <UserCard
        v-for="user in users"
        :key="user.id"
        :user="user"
      />
    </div>

    <Pagination
      v-if="total > pageSize"
      :current="page"
      :total="total"
      :size="pageSize"
      @update:current="handlePageChange"
    />
  </AppLayout>
</template>

<style scoped>
.follow-tabs {
  display: flex;
  gap: 4px;
  margin-bottom: 24px;
  background: var(--color-bg-card);
  border: 1px solid var(--color-border);
  border-radius: var(--radius-xl);
  padding: 4px;
  width: fit-content;
}

.follow-tab {
  background: none;
  border: 0;
  border-radius: var(--radius-lg);
  color: var(--color-text-secondary);
  cursor: pointer;
  font: inherit;
  font-size: var(--font-size-base);
  font-weight: var(--font-weight-medium);
  padding: 8px 24px;
  transition: all var(--duration-fast) var(--ease-out);
}

.follow-tab:hover { color: var(--color-primary); }

.follow-tab--active {
  background: var(--color-primary);
  color: var(--color-bg-card);
}

.user-list {
  display: grid;
  gap: 12px;
  grid-template-columns: repeat(auto-fill, minmax(280px, 1fr));
}

@media (max-width: 780px) {
  .user-list { grid-template-columns: 1fr; }
  .follow-tab { padding: 8px 20px; }
}
</style>
