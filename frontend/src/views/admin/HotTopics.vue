<script setup>
import { ref, onMounted, computed } from "vue"
import VChart from "vue-echarts"
import { use } from "echarts/core"
import { CanvasRenderer } from "echarts/renderers"
import { BarChart } from "echarts/charts"
import { GridComponent, TooltipComponent } from "echarts/components"
import Loading from "../../components/common/Loading.vue"
import EmptyState from "../../components/common/EmptyState.vue"
import { fetchHotTopics } from "../../api/admin"
import { useToastStore } from "../../stores/toast"

use([CanvasRenderer, BarChart, GridComponent, TooltipComponent])

const toast = useToastStore()
const data = ref(null)
const loading = ref(true)
const period = ref("daily")

onMounted(() => loadData())

async function loadData() {
  loading.value = true
  try {
    data.value = await fetchHotTopics({ period: period.value })
  } catch (err) {
    toast.error("加载热门话题数据失败")
    console.error("加载热门话题数据失败:", err.message)
  } finally {
    loading.value = false
  }
}

const trendLabel = (t) => ({ rising: "↑ 上升", falling: "↓ 下降", stable: "— 稳定" }[t] || t)

const barChartOption = computed(() => {
  const items = data.value?.items || []
  const top10 = [...items].slice(0, 10).reverse()
  return {
    tooltip: {
      trigger: "axis",
      axisPointer: { type: "shadow" },
      formatter: (params) => {
        const d = params[0]
        if (!d) return ""
        const item = items.find(i => i.name === d.name)
        if (!item) return `${d.name}<br/>热度: ${d.value}`
        return `<strong>${item.name}</strong><br/>
          热度值: ${item.heat_score}<br/>
          帖子: ${item.post_count} · 浏览: ${item.total_views}<br/>
          点赞: ${item.total_likes} · 评论: ${item.total_comments} · 收藏: ${item.total_collects}<br/>
          趋势: ${trendLabel(item.trend)} (${item.trend_change > 0 ? '+' : ''}${item.trend_change}%)`
      },
    },
    grid: { left: 12, right: 40, top: 10, bottom: 24 },
    xAxis: { type: "value", axisLabel: { fontSize: 11 } },
    yAxis: {
      type: "category",
      data: top10.map(d => d.name),
      axisLabel: { fontSize: 11, width: 80, overflow: "truncate" },
      inverse: true,
    },
    series: [{
      type: "bar",
      data: top10.map(d => d.heat_score),
      barMaxWidth: 20,
      itemStyle: {
        color: "#14b8a6",
        borderRadius: [0, 4, 4, 0],
      },
    }],
  }
})
</script>

<template>
    <header class="toolbar">
      <h1>管理后台 / 热门话题分析</h1>
    </header>

    <div class="admin-nav">
      <router-link to="/admin" class="admin-nav__item">总览</router-link>
      <router-link to="/admin/review" class="admin-nav__item">审核队列</router-link>
      <router-link to="/admin/users" class="admin-nav__item">用户管理</router-link>
      <router-link to="/admin/certifications" class="admin-nav__item">认证审核</router-link>
      <router-link to="/admin/sensitive-words" class="admin-nav__item">敏感词</router-link>
      <router-link to="/admin/compliance" class="admin-nav__item">合规检查</router-link>
      <router-link to="/admin/duplicate-content" class="admin-nav__item">重复检测</router-link>
      <router-link to="/admin/behavior" class="admin-nav__item">行为监控</router-link>
      <router-link to="/admin/logs" class="admin-nav__item">操作日志</router-link>
      <router-link to="/admin/hot-topics" class="admin-nav__item admin-nav__item--active">热门话题分析</router-link>
      <router-link to="/admin/engagement" class="admin-nav__item">用户参与度</router-link>
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
      <span v-if="data" class="filter-hint">数据生成时间：{{ data.generated_at?.slice(0, 16).replace('T', ' ') }}</span>
    </div>

    <Loading v-if="loading" variant="skeleton" :rows="3" />

    <template v-else-if="data">
      <div class="stats-grid">
        <div class="stat-card">
          <span class="stat-card__label">总话题数</span>
          <strong class="stat-card__value">{{ data.summary?.total_topics || 0 }}</strong>
        </div>
        <div class="stat-card">
          <span class="stat-card__label">相关帖子</span>
          <strong class="stat-card__value">{{ data.summary?.total_posts || 0 }}</strong>
        </div>
        <div class="stat-card">
          <span class="stat-card__label">平均热度</span>
          <strong class="stat-card__value">{{ data.summary?.avg_heat_score || 0 }}</strong>
        </div>
      </div>

      <div class="chart-card" v-if="data.items?.length">
        <h3 class="chart-card__title">🔥 话题热度排行 Top10</h3>
        <VChart :option="barChartOption" autoresize class="chart chart--bar" />
      </div>

      <EmptyState
        v-if="!data.items?.length"
        icon="📭"
        title="暂无话题数据"
        description="当前时段内没有发布带标签的帖子"
      />

      <div v-else class="table-wrapper">
        <table class="topic-table">
          <thead>
            <tr>
              <th>排名</th>
              <th>话题</th>
              <th>帖子数</th>
              <th>热度值</th>
              <th>浏览</th>
              <th>点赞</th>
              <th>评论</th>
              <th>收藏</th>
              <th>趋势</th>
              <th>变化率</th>
            </tr>
          </thead>
          <tbody>
            <tr v-for="item in data.items" :key="item.rank">
              <td class="cell-rank">{{ item.rank }}</td>
              <td class="cell-name">{{ item.name }}</td>
              <td>{{ item.post_count.toLocaleString() }}</td>
              <td class="cell-heat">{{ item.heat_score.toLocaleString() }}</td>
              <td>{{ item.total_views.toLocaleString() }}</td>
              <td>{{ item.total_likes.toLocaleString() }}</td>
              <td>{{ item.total_comments.toLocaleString() }}</td>
              <td>{{ item.total_collects.toLocaleString() }}</td>
              <td>
                <span :class="['trend-badge', 'trend--' + item.trend]">
                  {{ trendLabel(item.trend) }}
                </span>
              </td>
              <td :class="item.trend_change >= 0 ? 'change-up' : 'change-down'">
                {{ item.trend_change > 0 ? '+' : '' }}{{ item.trend_change }}%
              </td>
            </tr>
          </tbody>
        </table>
      </div>
    </template>

    <div v-else class="empty-state">
      <p>无法加载热门话题数据，请检查后端服务</p>
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

.filter-hint {
  color: var(--color-text-muted);
  font-size: 12px;
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
.chart--bar { height: 260px; }

.table-wrapper {
  background: var(--color-bg-card);
  border: 1px solid var(--color-border);
  border-radius: 8px;
  overflow: hidden;
}

.topic-table { width: 100%; border-collapse: collapse; }
.topic-table th, .topic-table td { padding: 10px 14px; text-align: left; border-bottom: 1px solid var(--color-border); font-size: 13px; }
.topic-table th { background: var(--color-bg-hover); font-weight: 600; font-size: 12px; color: var(--color-text-muted); text-transform: uppercase; }
.topic-table tbody tr:hover { background: var(--color-bg-hover); }

.cell-rank { font-weight: 700; color: var(--color-primary); width: 50px; }
.cell-name { font-weight: 600; max-width: 160px; overflow: hidden; text-overflow: ellipsis; white-space: nowrap; }
.cell-heat { font-weight: 600; color: var(--color-primary); }

.trend-badge { border-radius: 4px; font-size: 12px; font-weight: 600; padding: 2px 8px; white-space: nowrap; }
.trend--rising { background: #dcfce7; color: #16a34a; }
.trend--falling { background: #fee2e2; color: #dc2626; }
.trend--stable { background: var(--color-bg-hover); color: var(--color-text-muted); }

.change-up { color: #16a34a; font-weight: 600; }
.change-down { color: #dc2626; font-weight: 600; }

.empty-state { background: var(--color-bg-card); border: 1px solid var(--color-border); border-radius: 8px; padding: 60px 0; text-align: center; color: var(--color-text-muted); }

@media (max-width: 780px) {
  .stats-grid { grid-template-columns: 1fr 1fr; }
  .admin-nav__item { padding: 10px 16px; font-size: 13px; }
  .chart { height: 220px; }
  .filter-bar { flex-direction: column; align-items: flex-start; }
  .topic-table { font-size: 12px; }
  .topic-table th, .topic-table td { padding: 8px 10px; }
}
</style>
