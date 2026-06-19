<script setup>
import { ref, onMounted } from 'vue'
import AppLayout from '../components/layout/AppLayout.vue'
import Loading from '../components/common/Loading.vue'
import EmptyState from '../components/common/EmptyState.vue'
import { fetchGroups } from '../api/groups'

const groups = ref([])
const loading = ref(true)

onMounted(async () => {
  try {
    const data = await fetchGroups({ type: 'explore' })
    groups.value = Array.isArray(data) ? data : (data?.items || [])
  } catch (err) {
    console.error('加载群组失败:', err.message)
  } finally {
    loading.value = false
  }
})
</script>

<template>
  <AppLayout>
    <header class="toolbar">
      <div>
        <h1>投资群组</h1>
        <p>发现和加入投资讨论群组</p>
      </div>
      <button class="create-btn" @click="$router.push('/groups/new')">+ 创建群组</button>
    </header>

    <Loading v-if="loading" variant="skeleton" :rows="3" />
    <EmptyState
      v-else-if="!groups.length"
      icon="🏘️"
      title="暂无群组"
      description="还没有人创建群组，来创建第一个吧"
      action-label="创建群组"
      @action="$router.push('/groups/new')"
    />
    <div v-else class="group-grid">
      <div
        v-for="group in groups"
        :key="group.id"
        class="group-card"
        @click="$router.push(`/groups/${group.id}`)"
      >
        <h3>{{ group.name }}</h3>
        <p>{{ group.description }}</p>
        <div class="group-card__footer">
          <span>{{ group.member_count || 0 }} 成员</span>
          <span class="group-card__visibility">{{ group.visibility === 'public' ? '公开' : '私密' }}</span>
        </div>
      </div>
    </div>
  </AppLayout>
</template>

<style scoped>
.toolbar { align-items: center; display: flex; gap: 20px; justify-content: space-between; margin-bottom: 24px; }
.toolbar h1 { font-size: 28px; margin: 0 0 8px; }
.toolbar p { color: var(--color-text-secondary); margin: 0; font-size: 14px; }

.create-btn {
  background: var(--color-primary);
  border: 0;
  border-radius: 8px;
  color: var(--color-bg-card);
  cursor: pointer;
  font: inherit;
  font-size: 14px;
  padding: 10px 20px;
}

.create-btn:hover { background: var(--color-primary-hover); }

.group-grid { display: grid; gap: 14px; }

.group-card {
  background: var(--color-bg-card);
  border: 1px solid var(--color-border);
  border-radius: 10px;
  cursor: pointer;
  padding: 20px;
  transition: box-shadow 0.15s;
}

.group-card:hover { box-shadow: 0 4px 12px rgba(15, 23, 42, 0.08); }
.group-card h3 { font-size: 18px; margin: 0 0 8px; }
.group-card p { color: var(--color-text-secondary); font-size: 14px; margin: 0 0 12px; }

.group-card__footer {
  align-items: center;
  color: var(--color-text-muted);
  display: flex;
  font-size: 13px;
  gap: 12px;
}

.group-card__visibility {
  background: var(--color-border-light);
  border-radius: 4px;
  padding: 2px 8px;
}
</style>
