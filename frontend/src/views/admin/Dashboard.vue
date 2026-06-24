<script setup>
import { ref, onMounted, computed } from "vue"
import VChart from "vue-echarts"
import { use } from "echarts/core"
import { CanvasRenderer } from "echarts/renderers"
import { LineChart, BarChart } from "echarts/charts"
import { GridComponent, TooltipComponent, LegendComponent, TitleComponent } from "echarts/components"
import Loading from "../../components/common/Loading.vue"
import { fetchStatsOverview } from "../../api/admin"

use([CanvasRenderer, LineChart, BarChart, GridComponent, TooltipComponent, LegendComponent, TitleComponent])

const stats = ref(null)
const loading = ref(true)

onMounted(async () => {
  try {
    stats.value = await fetchStatsOverview()
  } catch (err) {
    console.error("加载统计数据失败:", err.message)
  } finally {
    loading.value = false
  }
})

// 活跃用户趋势图配置（近7天）
const trendOption = computed(() => {
  const data = stats.value?.trend || { dates: [], active_users: [], new_posts: [], new_comments: [] }
  return {
    tooltip: { trigger: "axis" },
    legend: { data: ["活跃用户", "新增帖子", "新增评论"], bottom: 0, textStyle: { fontSize: 12 } },
    grid: { left: 50, right: 16, top: 40, bottom: 36, containLabel: true },
    xAxis: { type: "category", data: data.dates || ["--"], axisLabel: { fontSize: 11 } },
    yAxis: { type: "value", axisLabel: { fontSize: 11 } },
    series: [
      { name: "活跃用户", type: "line", data: data.active_users || [], smooth: true, lineStyle: { color: "#0f766e", width: 2 }, itemStyle: { color: "#0f766e" }, symbol: "circle", symbolSize: 6 },
      { name: "新增帖子", type: "line", data: data.new_posts || [], smooth: true, lineStyle: { color: "#3b82f6", width: 2 }, itemStyle: { color: "#3b82f6" }, symbol: "circle", symbolSize: 6 },
      { name: "新增评论", type: "line", data: data.new_comments || [], smooth: true, lineStyle: { color: "#d97706", width: 2 }, itemStyle: { color: "#d97706" }, symbol: "circle", symbolSize: 6 },
    ],
  }
})

// 热门话题
const topicsOption = computed(() => {
  const data = stats.value?.hot_topics || []
  return {
    tooltip: { trigger: "axis", axisPointer: { type: "shadow" } },
    grid: { left: 10, right: 10, top: 10, bottom: 24, containLabel: true },
    xAxis: { type: "value", axisLabel: { fontSize: 11 } },
    yAxis: { type: "category", data: data.map(d => d.name || d).reverse(), axisLabel: { fontSize: 11 }, inverse: true },
    series: [{ type: "bar", data: data.map(d => d.count || d.value || 0).reverse(), barMaxWidth: 20, itemStyle: { color: "#14b8a6", borderRadius: [0, 4, 4, 0] } }],
  }
})

// 活跃股票
const stocksOption = computed(() => {
  const data = stats.value?.hot_stocks || []
  return {
    tooltip: { trigger: "axis", axisPointer: { type: "shadow" } },
    grid: { left: 10, right: 10, top: 10, bottom: 24, containLabel: true },
    xAxis: { type: "value", axisLabel: { fontSize: 11 } },
    yAxis: { type: "category", data: data.map(d => d.name || d.code || d).reverse(), axisLabel: { fontSize: 11 }, inverse: true },
    series: [{ type: "bar", data: data.map(d => d.count || d.value || 0).reverse(), barMaxWidth: 20, itemStyle: { color: "#3b82f6", borderRadius: [0, 4, 4, 0] } }],
  }
})
</script>

<template>
    <header class="toolbar">
      <h1>管理后台 / 数据总览</h1>
    </header>

    <div class="admin-nav">
      <router-link to="/admin" class="admin-nav__item admin-nav__item--active">总览</router-link>
      <router-link to="/admin/review" class="admin-nav__item">审核队列</router-link>
      <router-link to="/admin/users" class="admin-nav__item">用户管理</router-link>
      <router-link to="/admin/certifications" class="admin-nav__item">认证审核</router-link>
      <router-link to="/admin/sensitive-words" class="admin-nav__item">敏感词</router-link>
      <router-link to="/admin/compliance" class="admin-nav__item">合规检查</router-link>
      <router-link to="/admin/duplicate-content" class="admin-nav__item">重复检测</router-link>
      <router-link to="/admin/behavior" class="admin-nav__item">行为监控</router-link>
      <router-link to="/admin/logs" class="admin-nav__item">操作日志</router-link>
      <router-link to="/admin/hot-topics" class="admin-nav__item">热门话题分析</router-link>
      <router-link to="/admin/engagement" class="admin-nav__item">用户参与度</router-link>
      <router-link to="/admin/categories" class="admin-nav__item">板块管理</router-link>
    </div>

    <Loading v-if="loading" variant="skeleton" :rows="2" />

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
        <div class="stat-card stat-card--danger">
          <span class="stat-card__label">今日举报</span>
          <strong class="stat-card__value">{{ stats.reports_today || 0 }}</strong>
        </div>
        <div class="stat-card stat-card--danger" v-if="stats.unread_alerts > 0">
          <span class="stat-card__label">未读告警</span>
          <strong class="stat-card__value">{{ stats.unread_alerts || 0 }}</strong>
        </div>
        <div class="stat-card stat-card--warn" v-if="stats.suspicious_today > 0">
          <span class="stat-card__label">今日可疑行为</span>
          <strong class="stat-card__value">{{ stats.suspicious_today || 0 }}</strong>
        </div>
      </div>

      <!-- 活跃趋势图 -->
      <div class="chart-card">
        <h3 class="chart-card__title">📈 活跃趋势（近7天）</h3>
        <VChart :option="trendOption" autoresize class="chart" />
      </div>

      <!-- 热门排行 -->
      <div class="dual-charts">
        <div class="chart-card">
          <h3 class="chart-card__title">🔥 热门话题 Top10</h3>
          <VChart v-if="stats.hot_topics?.length" :option="topicsOption" autoresize class="chart chart--bar" />
          <p v-else class="chart-empty">暂无数据</p>
        </div>
        <div class="chart-card">
          <h3 class="chart-card__title">📊 最活跃股票 Top10</h3>
          <VChart v-if="stats.hot_stocks?.length" :option="stocksOption" autoresize class="chart chart--bar" />
          <p v-else class="chart-empty">暂无数据</p>
        </div>
      </div>
    </template>

    <div v-else class="empty-state">
      <p>无法加载统计数据，请检查后端服务</p>
    </div>
</template>

<style scoped>
.toolbar { margin-bottom: 24px; }
.toolbar h1 { font-size: 24px; margin: 0; }




.stat-card {
  background: var(--color-bg-card);
  border: 1px solid var(--color-border);
  border-radius: 8px;
  display: grid;
  gap: 8px;
  padding: 20px;
}

.stat-card--warn { border-left: 3px solid var(--color-warning); }
.stat-card--danger { border-left: 3px solid var(--color-danger); }

.stat-card__label { color: var(--color-text-muted); font-size: 13px; }
.stat-card__value { color: var(--color-text-primary); font-size: 28px; font-weight: 700; }

.chart-card {
  background: var(--color-bg-card);
  border: 1px solid var(--color-border);
  border-radius: 8px;
  margin-bottom: 16px;
  padding: 20px;
}

.chart-card__title {
  font-size: 15px;
  font-weight: 600;
  margin: 0 0 16px;
}

.stats-grid {
  display: grid;
  gap: 16px;
  grid-template-columns: repeat(3, 1fr);
  margin-bottom: 16px;
}

.chart { width: 100%; height: 280px; }
.chart--bar { height: 260px; }
.chart-empty { color: var(--color-text-muted); font-size: 13px; padding: 60px 0; text-align: center; }

.dual-charts {
  display: grid;
  gap: 16px;
  grid-template-columns: 1fr 1fr;
}

.empty-state { color: var(--color-text-muted); padding: 60px 0; text-align: center; }

@media (max-width: 780px) {
  .stats-grid { grid-template-columns: 1fr 1fr; }
  .dual-charts { grid-template-columns: 1fr; }
}
.admin-nav { background: var(--color-bg-card); border: 1px solid var(--color-border); border-radius: 8px; display: flex; gap: 0; margin-bottom: 24px; overflow: hidden; flex-wrap: wrap; }
.admin-nav__item { border-bottom: 2px solid transparent; color: var(--color-text-secondary); font-size: 14px; font-weight: 500; padding: 14px 24px; text-decoration: none; }
.admin-nav__item:hover { color: var(--color-text-body); }
.admin-nav__item--active { border-bottom-color: var(--color-primary); color: var(--color-primary); }
    </style>
