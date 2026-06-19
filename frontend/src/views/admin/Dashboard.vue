<script setup>
import { ref, onMounted } from 'vue'
import AppLayout from '../../components/layout/AppLayout.vue'
import Loading from '../../components/common/Loading.vue'
import { fetchStatsOverview } from '../../api/admin'

const stats = ref(null)
const loading = ref(true)

onMounted(async () => {
  try {
    stats.value = await fetchStatsOverview()
  } catch (err) {
    console.error('加载统计数据失败:', err.message)
  } finally {
    loading.value = false
  }
})
</script>

<template>
  <AppLayout>
    <header class="toolbar">
      <h1>管理后台 / 数据总览</h1>
    </header>

    <!-- 管理导航 -->
    <div class="admin-nav">
      <router-link to="/admin" class="admin-nav__item admin-nav__item--active">总览</router-link>
      <router-link to="/admin/review" class="admin-nav__item">审核队列</router-link>
      <router-link to="/admin/users" class="admin-nav__item">用户管理</router-link>
    </div>

    <Loading v-if="loading" variant="skeleton" :rows="1" />

    <template v-else-if="stats">
      <!-- 统计卡片 -->
      <div class="stats-grid">
        <div class="stat-card">
          <span class="stat-card__label">日活用户</span>
          <strong class="stat-card__value">{{ stats.daily_active_users || 0 }}</strong>
        </div>
        <div class="stat-card">
          <span class="stat-card__label">今日新增</span>
          <strong class="stat-card__value">{{ stats.new_users_today || 0 }}</strong>
        </div>
        <div class="stat-card">
          <span class="stat-card__label">总帖子</span>
          <strong class="stat-card__value">{{ stats.total_posts || 0 }}</strong>
        </div>
        <div class="stat-card">
          <span class="stat-card__label">总评论</span>
          <strong class="stat-card__value">{{ stats.total_comments || 0 }}</strong>
        </div>
        <div class="stat-card stat-card--warn">
          <span class="stat-card__label">待审核</span>
          <strong class="stat-card__value">{{ stats.pending_review || 0 }}</strong>
        </div>
        <div class="stat-card stat-card--warn">
          <span class="stat-card__label">今日举报</span>
          <strong class="stat-card__value">{{ stats.reports_today || 0 }}</strong>
        </div>
      </div>

      <!-- 图表占位 -->
      <div class="chart-placeholder">
        <p>📊 活跃用户趋势图（近7天）— 待集成图表库</p>
      </div>

      <div class="dual-charts">
        <div class="chart-placeholder"><p>🔥 热门话题 Top10</p></div>
        <div class="chart-placeholder"><p>📈 最活跃股票 Top10</p></div>
      </div>
    </template>
  </AppLayout>
</template>

<style scoped>
.toolbar { margin-bottom: 24px; }
.toolbar h1 { font-size: 24px; margin: 0; }

.admin-nav {
  background: var(--color-bg-card);
  border: 1px solid var(--color-border);
  border-radius: 8px;
  display: flex;
  gap: 0;
  margin-bottom: 24px;
  overflow: hidden;
}

.admin-nav__item {
  border-bottom: 2px solid transparent;
  color: var(--color-text-secondary);
  font-size: 14px;
  font-weight: 500;
  padding: 14px 24px;
  text-decoration: none;
}

.admin-nav__item:hover { color: var(--color-text-body); }
.admin-nav__item--active { border-bottom-color: var(--color-primary); color: var(--color-primary); }

.stats-grid {
  display: grid;
  gap: 12px;
  grid-template-columns: repeat(3, 1fr);
  margin-bottom: 24px;
}

.stat-card {
  background: var(--color-bg-card);
  border: 1px solid var(--color-border);
  border-radius: 8px;
  display: grid;
  gap: 8px;
  padding: 20px;
}

.stat-card--warn { border-left: 3px solid var(--color-warning); }

.stat-card__label { color: var(--color-text-muted); font-size: 13px; }
.stat-card__value { color: var(--color-text-primary); font-size: 28px; }

.chart-placeholder {
  align-items: center;
  background: var(--color-bg-card);
  border: 1px dashed var(--color-border-input);
  border-radius: 8px;
  color: var(--color-text-muted);
  display: flex;
  font-size: 14px;
  justify-content: center;
  margin-bottom: 16px;
  min-height: 200px;
  padding: 24px;
}

.dual-charts {
  display: grid;
  gap: 16px;
  grid-template-columns: 1fr 1fr;
}

@media (max-width: 780px) {
  .stats-grid { grid-template-columns: 1fr 1fr; }
  .dual-charts { grid-template-columns: 1fr; }
  .admin-nav__item { padding: 10px 16px; font-size: 13px; }
}
</style>
