<script setup>
import { ref, onMounted } from 'vue'
import AppLayout from '../components/layout/AppLayout.vue'
import PostCard from '../components/post/PostCard.vue'
import Loading from '../components/common/Loading.vue'
import EmptyState from '../components/common/EmptyState.vue'
import Pagination from '../components/common/Pagination.vue'
import { fetchCollections } from '../api/posts'

const collections = ref([])
const loading = ref(true)
const pagination = ref({ page: 1, size: 20, total: 0 })

onMounted(async () => {
  await loadCollections()
})

async function loadCollections(page = 1) {
  loading.value = true
  try {
    const data = await fetchCollections({ page, size: 20 })
    collections.value = data.items || []
    pagination.value.total = data.total || 0
    pagination.value.page = page
  } catch (err) {
    console.error('加载收藏失败:', err.message)
  } finally {
    loading.value = false
  }
}

function handlePageChange(page) { loadCollections(page) }
</script>

<template>
  <AppLayout>
    <header class="toolbar">
      <div>
        <h1>我的收藏</h1>
        <p>共 {{ pagination.total }} 篇</p>
      </div>
    </header>

    <Loading v-if="loading" variant="skeleton" :rows="3" />
    <EmptyState
      v-else-if="!collections.length"
      icon="⭐"
      title="暂无收藏"
      description="浏览帖子时点击收藏即可保存到这里"
    />
    <div v-else class="post-list">
      <PostCard
        v-for="item in collections"
        :key="item.id"
        :post="item"
      />
    </div>

    <Pagination
      v-if="pagination.total > 20"
      :current="pagination.page"
      :total="pagination.total"
      :size="20"
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
