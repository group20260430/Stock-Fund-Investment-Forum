<script setup>
import { ref, onMounted } from 'vue'
import { useToastStore } from '../../stores/toast'
import { fetchDuplicateContentStats, scanDuplicateContent } from '../../api/admin'
import Loading from '../../components/common/Loading.vue'
import EmptyState from '../../components/common/EmptyState.vue'

const toast = useToastStore()

const activeTab = ref('scan')  // scan | stats

// ── Scan tab ──
const scanText = ref('')
const startDate = ref('')
const endDate = ref('')
const scanning = ref(false)
const scanResult = ref(null)

// ── Stats tab ──
const stats = ref(null)
const loadingStats = ref(true)

onMounted(loadStats)

async function loadStats() {
  loadingStats.value = true
  try {
    stats.value = await fetchDuplicateContentStats()
  } catch (err) {
    toast.error('加载统计数据失败: ' + err.message)
  } finally {
    loadingStats.value = false
  }
}

async function handleScan() {
  if (!scanText.value.trim() && !startDate.value && !endDate.value) {
    toast.warning('请输入文本或选择时间范围')
    return
  }
  scanning.value = true
  scanResult.value = null
  try {
    scanResult.value = await scanDuplicateContent({
      text: scanText.value,
      start_date: startDate.value || null,
      end_date: endDate.value || null,
    })
    toast.success(`扫描完成，发现 ${scanResult.value?.pairs?.length || 0} 条重复`)
  } catch (err) {
    toast.error('扫描失败: ' + err.message)
  } finally {
    scanning.value = false
  }
}

function similarityBadgeClass(sim) {
  if (sim >= 0.99) return 'sim--exact'
  if (sim >= 0.95) return 'sim--high'
  if (sim >= 0.92) return 'sim--medium'
  return 'sim--low'
}

function similarityLabel(sim) {
  return Math.round(sim * 100) + '%'
}

function statusLabel(status) {
  return status === 'exact_duplicate' ? '精确重复' : '高度相似'
}
</script>

<template>
    <header class="toolbar"><h1>管理后台 / 重复内容检测</h1></header>
    <div class="admin-nav">
      <router-link to="/admin" class="admin-nav__item">总览</router-link>
      <router-link to="/admin/review" class="admin-nav__item">审核队列</router-link>
      <router-link to="/admin/users" class="admin-nav__item">用户管理</router-link>
      <router-link to="/admin/certifications" class="admin-nav__item">认证审核</router-link>
      <router-link to="/admin/sensitive-words" class="admin-nav__item">敏感词</router-link>
      <router-link to="/admin/compliance" class="admin-nav__item">合规检查</router-link>
      <router-link to="/admin/duplicate-content" class="admin-nav__item admin-nav__item--active">重复检测</router-link>
      <router-link to="/admin/behavior" class="admin-nav__item">行为监控</router-link>
      <router-link to="/admin/logs" class="admin-nav__item">操作日志</router-link>
      <router-link to="/admin/hot-topics" class="admin-nav__item">热门话题分析</router-link>
      <router-link to="/admin/engagement" class="admin-nav__item">用户参与度</router-link>
      <router-link to="/admin/categories" class="admin-nav__item">板块管理</router-link>
    </div>

    <div class="tab-bar">
      <button :class="['tab', { 'tab--active': activeTab === 'scan' }]" @click="activeTab = 'scan'">扫描检测</button>
      <button :class="['tab', { 'tab--active': activeTab === 'stats' }]" @click="activeTab = 'stats'">统计数据</button>
    </div>

    <!-- Tab 1: Scan -->
    <div v-if="activeTab === 'scan'">
      <div class="scan-form">
        <textarea v-model="scanText" class="scan-textarea" rows="4" placeholder="输入要检测的文本内容（可选），留空则按时间范围扫描全部帖子" maxlength="10000"></textarea>
        <div class="scan-filters">
          <label class="filter-label">起始日期：
            <input v-model="startDate" type="date" class="filter-input" />
          </label>
          <label class="filter-label">结束日期：
            <input v-model="endDate" type="date" class="filter-input" />
          </label>
          <button class="scan-btn" :disabled="scanning" @click="handleScan">
            {{ scanning ? '扫描中...' : '开始扫描' }}
          </button>
        </div>
      </div>

      <Loading v-if="scanning" variant="skeleton" :rows="3" />
      <EmptyState v-else-if="!scanResult && !scanning" icon="search" title="输入文本或选择时间范围开始扫描" description="扫描将检测重复和高度相似的帖子内容" />

      <div v-else-if="scanResult && scanResult.pairs && scanResult.pairs.length === 0" class="empty-state">
        <p>未发现重复内容</p>
      </div>

      <div v-else-if="scanResult" class="scan-results">
        <div class="result-summary">
          <span class="result-stat">扫描帖子数：<strong>{{ scanResult.total_posts_scanned }}</strong></span>
          <span class="result-stat">发现重复：<strong>{{ scanResult.pairs?.length || 0 }}</strong></span>
          <span class="result-stat">扫描时间：{{ scanResult.scanned_at?.slice(0, 19) || '--' }}</span>
        </div>

        <div v-for="pair in scanResult.pairs" :key="(pair.source_post_id || 'input') + '-' + pair.matched_post_id" class="duplicate-card">
          <div class="dup-column">
            <span class="dup-label">来源</span>
            <h4 v-if="pair.source_post_id">
              <router-link :to="'/posts/' + pair.source_post_id" class="post-link">{{ pair.source_title }}</router-link>
            </h4>
            <p v-else class="dup-input-text">{{ pair.source_title }}</p>
            <span v-if="pair.source_author" class="dup-author">{{ pair.source_author.nickname }}</span>
          </div>
          <div class="dup-divider">
            <span :class="['sim-badge', similarityBadgeClass(pair.similarity)]">{{ similarityLabel(pair.similarity) }}</span>
            <span class="sim-label">{{ statusLabel(pair.status) }}</span>
          </div>
          <div class="dup-column">
            <span class="dup-label">匹配</span>
            <h4>
              <router-link :to="'/posts/' + pair.matched_post_id" class="post-link">{{ pair.matched_title }}</router-link>
            </h4>
            <span v-if="pair.matched_author" class="dup-author">{{ pair.matched_author.nickname }}</span>
          </div>
        </div>
      </div>
    </div>

    <!-- Tab 2: Statistics -->
    <div v-if="activeTab === 'stats'">
      <Loading v-if="loadingStats" variant="skeleton" :rows="2" />
      <div v-else-if="stats">
        <div class="stats-grid">
          <div class="stat-card stat-card--danger">
            <span class="stat-card__label">总拦截数</span>
            <strong class="stat-card__value">{{ stats.total_blocked }}</strong>
          </div>
          <div class="stat-card stat-card--warn">
            <span class="stat-card__label">总标记数</span>
            <strong class="stat-card__value">{{ stats.total_flagged }}</strong>
          </div>
          <div class="stat-card">
            <span class="stat-card__label">精确重复</span>
            <strong class="stat-card__value">{{ stats.by_similarity?.exact_duplicates || 0 }}</strong>
          </div>
          <div class="stat-card stat-card--warn">
            <span class="stat-card__label">高度相似 (95-100%)</span>
            <strong class="stat-card__value">{{ stats.by_similarity?.near_duplicates_95_100 || 0 }}</strong>
          </div>
          <div class="stat-card">
            <span class="stat-card__label">中度相似 (92-95%)</span>
            <strong class="stat-card__value">{{ stats.by_similarity?.near_duplicates_92_95 || 0 }}</strong>
          </div>
          <div class="stat-card">
            <span class="stat-card__label">近期扫描帖子数</span>
            <strong class="stat-card__value">{{ stats.recent_posts_scanned }}</strong>
          </div>
        </div>

        <div class="chart-card">
          <h3>相似度分布说明</h3>
          <table class="info-table">
            <thead>
              <tr><th>相似度范围</th><th>处理方式</th><th>说明</th></tr>
            </thead>
            <tbody>
              <tr>
                <td><span class="sim-badge sim--exact">≥99%</span></td>
                <td>直接拦截</td>
                <td>内容几乎完全相同，拒绝发布</td>
              </tr>
              <tr>
                <td><span class="sim-badge sim--high">95-99%</span></td>
                <td>送审 + 标记</td>
                <td>高度相似，进入审核队列人工判断</td>
              </tr>
              <tr>
                <td><span class="sim-badge sim--medium">92-95%</span></td>
                <td>送审</td>
                <td>存在相似嫌疑，审核员酌情处理</td>
              </tr>
              <tr>
                <td><span class="sim-badge sim--low">&lt;92%</span></td>
                <td>放行</td>
                <td>相似度不构成重复，正常发布</td>
              </tr>
            </tbody>
          </table>
        </div>
      </div>
    </div>
</template>

<style scoped>
.toolbar { margin-bottom: 24px; }
.toolbar h1 { font-size: 24px; margin: 0; }
.admin-nav { background: var(--color-bg-card); border: 1px solid var(--color-border); border-radius: 8px; display: flex; gap: 0; margin-bottom: 24px; overflow: hidden; flex-wrap: wrap; }
.admin-nav__item { border-bottom: 2px solid transparent; color: var(--color-text-secondary); font-size: 14px; font-weight: 500; padding: 14px 24px; text-decoration: none; }
.admin-nav__item:hover { color: var(--color-text-body); }
.admin-nav__item--active { border-bottom-color: var(--color-primary); color: var(--color-primary); }

.tab-bar { display: flex; gap: 0; margin-bottom: 16px; }
.tab {
  background: var(--color-bg-hover); border: 0; border-radius: 8px 8px 0 0;
  color: var(--color-text-secondary); cursor: pointer; font: inherit;
  font-size: 14px; font-weight: 500; padding: 10px 24px; transition: all 0.15s;
}
.tab--active {
  background: var(--color-bg-card); border: 1px solid var(--color-border);
  border-bottom-color: var(--color-bg-card); color: var(--color-primary); margin-bottom: -1px;
}

/* ── Scan Tab ── */
.scan-form { background: var(--color-bg-card); border: 1px solid var(--color-border); border-radius: 8px; margin-bottom: 24px; padding: 20px; }
.scan-textarea {
  border: 1px solid var(--color-border-input); border-radius: 6px; font: inherit;
  font-size: 14px; line-height: 1.6; padding: 12px; width: 100%; box-sizing: border-box;
  resize: vertical; margin-bottom: 12px;
}
.scan-textarea:focus { border-color: var(--color-primary); outline: none; }
.scan-filters { display: flex; align-items: flex-end; gap: 12px; flex-wrap: wrap; }
.filter-label { font-size: 13px; color: var(--color-text-secondary); }
.filter-input { border: 1px solid var(--color-border-input); border-radius: 6px; font: inherit; font-size: 13px; padding: 6px 8px; margin-left: 4px; }
.scan-btn {
  background: var(--color-primary); border: 0; border-radius: 6px; color: #fff;
  cursor: pointer; font: inherit; font-size: 14px; padding: 8px 24px;
}
.scan-btn:disabled { opacity: 0.6; cursor: not-allowed; }

.empty-state { background: var(--color-bg-card); border: 1px solid var(--color-border); border-radius: 8px; padding: 40px; text-align: center; color: var(--color-text-muted); }

.scan-results { background: var(--color-bg-card); border: 1px solid var(--color-border); border-radius: 8px; padding: 20px; }
.result-summary { display: flex; gap: 20px; margin-bottom: 16px; padding-bottom: 12px; border-bottom: 1px solid var(--color-border-light); flex-wrap: wrap; }
.result-stat { font-size: 14px; color: var(--color-text-secondary); }
.result-stat strong { color: var(--color-text-primary); }

.duplicate-card { display: flex; gap: 20px; padding: 16px 0; border-bottom: 1px solid var(--color-border-light); align-items: flex-start; }
.dup-column { flex: 1; min-width: 0; }
.dup-label { font-size: 11px; font-weight: 600; color: var(--color-text-muted); text-transform: uppercase; display: block; margin-bottom: 4px; }
.dup-column h4 { font-size: 14px; margin: 0 0 4px; line-height: 1.4; }
.post-link { color: var(--color-primary); text-decoration: none; }
.post-link:hover { text-decoration: underline; }
.dup-input-text { color: var(--color-text-secondary); font-size: 13px; margin: 0; white-space: pre-wrap; word-break: break-all; }
.dup-author { font-size: 12px; color: var(--color-text-muted); }
.dup-divider { display: flex; flex-direction: column; align-items: center; gap: 4px; padding: 0 12px; flex-shrink: 0; }
.sim-badge { border-radius: 4px; font-size: 13px; font-weight: 700; padding: 4px 10px; white-space: nowrap; }
.sim--exact { background: #fef2f2; color: #dc2626; }
.sim--high { background: #fff7ed; color: #ea580c; }
.sim--medium { background: #fefce8; color: #ca8a04; }
.sim--low { background: var(--color-bg-hover); color: var(--color-text-muted); }
.sim-label { font-size: 11px; color: var(--color-text-muted); white-space: nowrap; }

/* ── Stats Tab ── */
.stats-grid { display: grid; gap: 16px; grid-template-columns: repeat(3, 1fr); margin-bottom: 24px; }
.stat-card {
  background: var(--color-bg-card); border: 1px solid var(--color-border);
  border-radius: 8px; display: grid; gap: 8px; padding: 20px;
}
.stat-card__label { color: var(--color-text-muted); font-size: 13px; }
.stat-card__value { color: var(--color-text-primary); font-size: 28px; font-weight: 700; }
.stat-card--warn { border-left: 3px solid var(--color-warning); }
.stat-card--danger { border-left: 3px solid var(--color-danger); }

.chart-card { background: var(--color-bg-card); border: 1px solid var(--color-border); border-radius: 8px; padding: 20px; }
.chart-card h3 { font-size: 16px; margin: 0 0 12px; }

.info-table { width: 100%; border-collapse: collapse; font-size: 14px; }
.info-table th { background: var(--color-bg-hover); padding: 10px 16px; text-align: left; font-weight: 600; border-bottom: 2px solid var(--color-border); }
.info-table td { padding: 10px 16px; border-bottom: 1px solid var(--color-border-light); }

@media (max-width: 780px) {
  .admin-nav__item { padding: 10px 14px; font-size: 13px; }
  .stats-grid { grid-template-columns: 1fr; }
  .duplicate-card { flex-direction: column; }
  .scan-filters { flex-direction: column; }
}
</style>
