<script setup>
import { ref, onMounted, computed } from "vue"
import VChart from "vue-echarts"
import { use } from "echarts/core"
import { CanvasRenderer } from "echarts/renderers"
import { LineChart, PieChart } from "echarts/charts"
import { GridComponent, TooltipComponent, LegendComponent } from "echarts/components"
import Loading from "../../components/common/Loading.vue"
import { fetchEngagementReport } from "../../api/admin"
import { useToastStore } from "../../stores/toast"

use([CanvasRenderer, LineChart, PieChart, GridComponent, TooltipComponent, LegendComponent])

const toast = useToastStore()
const data = ref(null)
const loading = ref(true)
const period = ref("weekly")

onMounted(() => loadData())

async function loadData() {
  loading.value = true
  try {
    data.value = await fetchEngagementReport({ period: period.value })
  } catch (err) {
    toast.error("加载参与度报告失败")
    console.error("加载参与度报告失败:", err.message)
  } finally {
    loading.value = false
  }
}

const trendChartOption = computed(() => {
  const breakdown = data.value?.daily_breakdown || []
  return {
    tooltip: { trigger: "axis" },
    legend: { data: ["活跃用户", "新增帖子", "新增评论", "新增点赞"], bottom: 0, textStyle: { fontSize: 12 } },
    grid: { left: 12, right: 12, top: 40, bottom: 36 },
    xAxis: { type: "category", data: breakdown.map(d => d.date) || ["--"], axisLabel: { fontSize: 11 } },
    yAxis: { type: "value", axisLabel: { fontSize: 11 } },
    series: [
      { name: "活跃用户", type: "line", data: breakdown.map(d => d.active_users), smooth: true, lineStyle: { color: "#0f766e", width: 2 }, itemStyle: { color: "#0f766e" }, symbol: "circle", symbolSize: 6 },
      { name: "新增帖子", type: "line", data: breakdown.map(d => d.new_posts), smooth: true, lineStyle: { color: "#3b82f6", width: 2 }, itemStyle: { color: "#3b82f6" }, symbol: "circle", symbolSize: 6 },
      { name: "新增评论", type: "line", data: breakdown.map(d => d.new_comments), smooth: true, lineStyle: { color: "#d97706", width: 2 }, itemStyle: { color: "#d97706" }, symbol: "circle", symbolSize: 6 },
      { name: "新增点赞", type: "line", data: breakdown.map(d => d.new_likes), smooth: true, lineStyle: { color: "#8b5cf6", width: 2 }, itemStyle: { color: "#8b5cf6" }, symbol: "circle", symbolSize: 6 },
    ],
  }
})

const distributionChartOption = computed(() => {
  const dist = data.value?.engagement_distribution || { high: { count: 0 }, medium: { count: 0 }, low: { count: 0 } }
  return {
    tooltip: {
      trigger: "item",
      formatter: "{b}: {c} 人 ({d}%)",
    },
    legend: { bottom: 0, textStyle: { fontSize: 12 } },
    series: [{
      type: "pie",
      radius: ["55%", "78%"],
      center: ["50%", "45%"],
      avoidLabelOverlap: false,
      itemStyle: { borderRadius: 4, borderColor: "var(--color-bg-card)", borderWidth: 3 },
      label: { show: false },
      emphasis: { label: { show: true, fontSize: 14, fontWeight: "bold" } },
      data: [
        { value: dist.high?.count || 0, name: "高活跃 (>20次)", itemStyle: { color: "#16a34a" } },
        { value: dist.medium?.count || 0, name: "中活跃 (5-20次)", itemStyle: { color: "#d97706" } },
        { value: dist.low?.count || 0, name: "低活跃 (1-4次)", itemStyle: { color: "#9ca3af" } },
      ],
    }],
  }
})
</script>

<template>
    <header class="toolbar">
      <h1>管理后台 / 用户参与度报告</h1>
    </header>

    <div class="admin-nav">
      <router-link to="/admin" class="admin-nav__item">总览</router-link>
      <router-link to="/admin/review" class="admin-nav__item">审核队列</router-link>
      <router-link to="/admin/users" class="admin-nav__item">用户管理</router-link>
      <router-link to="/admin/certifications" class="admin-nav__item">认证审核</router-link>
      <router-link to="/admin/sensitive-words" class="admin-nav__item">敏感词</router-link>
      <router-link to="/admin/compliance" class="admin-nav__item">合规检查</router-link>
      <router-link to="/admin/logs" class="admin-nav__item">操作日志</router-link>
      <router-link to="/admin/hot-topics" class="admin-nav__item">热门话题分析</router-link>
      <router-link to="/admin/engagement" class="admin-nav__item admin-nav__item--active">用户参与度</router-link>
      <router-link to="/admin/categories" class="admin-nav__item">板块管理</router-link>
    </div>

    <div class="filter-bar">
      <label>时间范围：
        <select v-model="period" @change="loadData" class="filter-select">
          <option value="daily">每日</option>
          <option value="weekly">每周</option>
          <option value="monthly">每月</option>
        </select>
      </label>
    </div>

    <Loading v-if="loading" variant="skeleton" :rows="3" />

    <template v-else-if="data">
      <!-- Overview stat cards -->
      <div class="stats-grid">
        <div class="stat-card">
          <span class="stat-card__label">总用户</span>
          <strong class="stat-card__value">{{ data.overview?.total_users?.toLocaleString() || 0 }}</strong>
        </div>
        <div class="stat-card">
          <span class="stat-card__label">活跃用户</span>
          <strong class="stat-card__value">{{ data.overview?.active_users?.toLocaleString() || 0 }}</strong>
        </div>
        <div class="stat-card">
          <span class="stat-card__label">新增用户</span>
          <strong class="stat-card__value">{{ data.overview?.new_users || 0 }}</strong>
        </div>
        <div class="stat-card">
          <span class="stat-card__label">参与率</span>
          <strong class="stat-card__value">{{ data.overview?.engagement_rate || 0 }}%</strong>
        </div>
        <div class="stat-card">
          <span class="stat-card__label">人均发帖</span>
          <strong class="stat-card__value">{{ data.overview?.avg_posts_per_user || 0 }}</strong>
        </div>
        <div class="stat-card">
          <span class="stat-card__label">人均评论</span>
          <strong class="stat-card__value">{{ data.overview?.avg_comments_per_user || 0 }}</strong>
        </div>
      </div>

      <!-- Daily trend chart -->
      <div class="chart-card">
        <h3 class="chart-card__title">📈 每日参与趋势</h3>
        <VChart :option="trendChartOption" autoresize class="chart" />
      </div>

      <!-- Two-column: distribution pie + contributor table -->
      <div class="dual-charts">
        <div class="chart-card">
          <h3 class="chart-card__title">🎯 参与度分布</h3>
          <VChart v-if="data.engagement_distribution" :option="distributionChartOption" autoresize class="chart chart--pie" />
          <p v-else class="chart-empty">暂无数据</p>
        </div>
        <div class="chart-card">
          <h3 class="chart-card__title">🏆 贡献者排行 Top 20</h3>
          <table v-if="data.top_contributors?.length" class="contributor-table">
            <thead>
              <tr>
                <th>#</th>
                <th>用户</th>
                <th>帖子</th>
                <th>评论</th>
                <th>获赞</th>
                <th>总计</th>
              </tr>
            </thead>
            <tbody>
              <tr v-for="c in data.top_contributors" :key="c.rank">
                <td class="cell-rank">{{ c.rank }}</td>
                <td class="contributor-user">
                  <img
                    v-if="c.avatar_url"
                    :src="c.avatar_url"
                    :alt="c.nickname"
                    class="avatar-mini"
                  />
                  <span v-else class="avatar-placeholder">{{ c.nickname?.charAt(0) }}</span>
                  <span class="contributor-name">{{ c.nickname }}</span>
                </td>
                <td>{{ c.posts_count }}</td>
                <td>{{ c.comments_count }}</td>
                <td>{{ c.likes_received }}</td>
                <td><strong>{{ c.total_contributions }}</strong></td>
              </tr>
            </tbody>
          </table>
          <p v-else class="chart-empty">暂无贡献者数据</p>
        </div>
      </div>
    </template>

    <div v-else class="empty-state">
      <p>无法加载用户参与度数据，请检查后端服务</p>
    </div>
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
  flex-wrap: wrap;
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

.filter-bar {
  align-items: center;
  display: flex;
  gap: 16px;
  margin-bottom: 16px;
  font-size: 14px;
  color: var(--color-text-secondary);
}

.filter-select {
  border: 1px solid var(--color-border);
  border-radius: 6px;
  font: inherit;
  font-size: 14px;
  padding: 6px 10px;
  background: var(--color-bg-card);
  color: var(--color-text-primary);
}

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

.chart { width: 100%; height: 280px; }
.chart--pie { height: 260px; }
.chart-empty { color: var(--color-text-muted); font-size: 13px; padding: 60px 0; text-align: center; }

.dual-charts {
  display: grid;
  gap: 16px;
  grid-template-columns: 1fr 1fr;
}

/* Contributor table */
.contributor-table {
  width: 100%;
  border-collapse: collapse;
}

.contributor-table th, .contributor-table td {
  padding: 8px 12px;
  text-align: left;
  border-bottom: 1px solid var(--color-border);
  font-size: 13px;
}

.contributor-table th {
  background: var(--color-bg-hover);
  font-weight: 600;
  font-size: 12px;
  color: var(--color-text-muted);
}

.contributor-table tbody tr:hover {
  background: var(--color-bg-hover);
}

.cell-rank {
  font-weight: 700;
  color: var(--color-primary);
  width: 32px;
}

.contributor-user {
  align-items: center;
  display: flex;
  gap: 8px;
  max-width: 160px;
}

.avatar-mini {
  border-radius: 50%;
  flex-shrink: 0;
  height: 28px;
  object-fit: cover;
  width: 28px;
}

.avatar-placeholder {
  align-items: center;
  background: var(--color-primary);
  border-radius: 50%;
  color: #fff;
  display: flex;
  flex-shrink: 0;
  font-size: 12px;
  font-weight: 600;
  height: 28px;
  justify-content: center;
  width: 28px;
}

.contributor-name {
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
}

.empty-state {
  background: var(--color-bg-card);
  border: 1px solid var(--color-border);
  border-radius: 8px;
  padding: 60px 0;
  text-align: center;
  color: var(--color-text-muted);
}

@media (max-width: 780px) {
  .stats-grid { grid-template-columns: 1fr 1fr; }
  .dual-charts { grid-template-columns: 1fr; }
  .admin-nav__item { padding: 10px 16px; font-size: 13px; }
  .chart { height: 220px; }
  .chart--pie { height: 240px; }
  .filter-bar { flex-direction: column; align-items: flex-start; }
}
</style>
