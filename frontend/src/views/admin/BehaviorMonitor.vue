<script setup>
import { ref, onMounted } from 'vue'
import { useToastStore } from '../../stores/toast'
import {
  fetchActivityLogs, fetchBehaviorUserSummary,
  fetchUserTimeline, fetchSuspiciousUsers,
} from '../../api/admin'
import Loading from '../../components/common/Loading.vue'
import Pagination from '../../components/common/Pagination.vue'

const toast = useToastStore()

const activeTab = ref('logs')  // logs | summary | suspicious

// ── Tab 1: Activity Logs ──
const logs = ref([])
const loadingLogs = ref(true)
const logPagination = ref({ page: 1, total: 0, size: 20 })
const logFilters = ref({ userKeyword: '', activityType: '', startDate: '', endDate: '' })

const activityLabelMap = {
  login: '登录', post: '发帖', comment: '评论', like: '点赞',
  follow: '关注', unfollow: '取消关注', share: '转发', vote: '投票',
}

async function loadLogs(page = 1) {
  loadingLogs.value = true
  try {
    const params = { page, size: logPagination.value.size }
    if (logFilters.value.activityType) params.activity_type = logFilters.value.activityType
    if (logFilters.value.startDate) params.start_date = logFilters.value.startDate
    if (logFilters.value.endDate) params.end_date = logFilters.value.endDate
    const data = await fetchActivityLogs(params)
    logs.value = data?.items || []
    logPagination.value.total = data?.total || 0
    logPagination.value.page = page
  } catch (err) {
    toast.error('加载日志失败: ' + err.message)
  } finally {
    loadingLogs.value = false
  }
}

function applyLogFilters() {
  loadLogs(1)
}

// ── Tab 2: User Activity Summary ──
const summary = ref([])
const loadingSummary = ref(true)
const summaryPagination = ref({ page: 1, total: 0, size: 20 })
const summarySort = ref({ by: 'total_actions', order: 'desc' })

// ── Timeline Modal ──
const showTimeline = ref(false)
const timelineUser = ref(null)
const timelineData = ref([])
const recentActivities = ref([])
const qualityData = ref(null)
const loadingTimeline = ref(false)

async function loadSummary(page = 1) {
  loadingSummary.value = true
  try {
    const data = await fetchBehaviorUserSummary({
      page, size: summaryPagination.value.size,
      sort_by: summarySort.value.by,
      sort_order: summarySort.value.order,
    })
    summary.value = data?.items || []
    summaryPagination.value.total = data?.total || 0
    summaryPagination.value.page = page
  } catch (err) {
    toast.error('加载用户汇总失败: ' + err.message)
  } finally {
    loadingSummary.value = false
  }
}

function changeSummarySort(by) {
  if (summarySort.value.by === by) {
    summarySort.value.order = summarySort.value.order === 'desc' ? 'asc' : 'desc'
  } else {
    summarySort.value.by = by
    summarySort.value.order = 'desc'
  }
  loadSummary(1)
}

function sortIndicator(by) {
  if (summarySort.value.by !== by) return ''
  return summarySort.value.order === 'desc' ? ' ↓' : ' ↑'
}

async function viewTimeline(userId) {
  showTimeline.value = true
  loadingTimeline.value = true
  timelineData.value = []
  recentActivities.value = []
  try {
    const data = await fetchUserTimeline(userId, { days: 14 })
    timelineUser.value = data?.user || null
    timelineData.value = data?.timeline || []
    recentActivities.value = data?.recent_activities || []
    qualityData.value = data?.quality || null
  } catch (err) {
    toast.error('加载时间线失败: ' + err.message)
    showTimeline.value = false
  } finally {
    loadingTimeline.value = false
  }
}

function closeTimeline() {
  showTimeline.value = false
  timelineUser.value = null
}

// ── Tab 3: Suspicious ──
const suspicious = ref([])
const loadingSuspicious = ref(true)

const patternLabelMap = {
  high_frequency_posting: '高频发帖',
  new_account_high_activity: '新账号高活跃',
  multiple_bans: '多次封禁',
}

function severityLabel(sev) { return sev === 'high' ? '高风险' : '中风险' }

async function loadSuspicious() {
  loadingSuspicious.value = true
  try {
    const data = await fetchSuspiciousUsers()
    suspicious.value = data?.items || []
  } catch (err) {
    toast.error('加载异常检测失败: ' + err.message)
  } finally {
    loadingSuspicious.value = false
  }
}

// ── Lifecycle ──
onMounted(() => {
  loadLogs()
  loadSummary()
  loadSuspicious()
})
</script>

<template>
    <header class="toolbar"><h1>管理后台 / 行为监控</h1></header>
    <div class="admin-nav">
      <router-link to="/admin" class="admin-nav__item">总览</router-link>
      <router-link to="/admin/review" class="admin-nav__item">审核队列</router-link>
      <router-link to="/admin/users" class="admin-nav__item">用户管理</router-link>
      <router-link to="/admin/certifications" class="admin-nav__item">认证审核</router-link>
      <router-link to="/admin/sensitive-words" class="admin-nav__item">敏感词</router-link>
      <router-link to="/admin/compliance" class="admin-nav__item">合规检查</router-link>
      <router-link to="/admin/duplicate-content" class="admin-nav__item">重复检测</router-link>
      <router-link to="/admin/behavior" class="admin-nav__item admin-nav__item--active">行为监控</router-link>
      <router-link to="/admin/logs" class="admin-nav__item">操作日志</router-link>
      <router-link to="/admin/hot-topics" class="admin-nav__item">热门话题分析</router-link>
      <router-link to="/admin/engagement" class="admin-nav__item">用户参与度</router-link>
      <router-link to="/admin/categories" class="admin-nav__item">板块管理</router-link>
    </div>

    <div class="tab-bar">
      <button :class="['tab', { 'tab--active': activeTab === 'logs' }]" @click="activeTab = 'logs'">活动日志</button>
      <button :class="['tab', { 'tab--active': activeTab === 'summary' }]" @click="activeTab = 'summary'">用户行为汇总</button>
      <button :class="['tab', { 'tab--active': activeTab === 'suspicious' }]" @click="activeTab = 'suspicious'">异常检测</button>
    </div>

    <!-- ============== Tab 1: Activity Logs ============== -->
    <div v-if="activeTab === 'logs'">
      <div class="filter-bar">
        <select v-model="logFilters.activityType" class="filter-select" @change="applyLogFilters">
          <option value="">全部类型</option>
          <option value="login">登录</option>
          <option value="post">发帖</option>
          <option value="comment">评论</option>
          <option value="like">点赞</option>
          <option value="follow">关注</option>
          <option value="share">转发</option>
          <option value="vote">投票</option>
        </select>
        <label class="filter-label">开始：
          <input v-model="logFilters.startDate" type="date" class="filter-input" @change="applyLogFilters" />
        </label>
        <label class="filter-label">结束：
          <input v-model="logFilters.endDate" type="date" class="filter-input" @change="applyLogFilters" />
        </label>
        <button class="filter-btn" @click="applyLogFilters">筛选</button>
      </div>

      <Loading v-if="loadingLogs" variant="skeleton" :rows="3" />
      <div v-else-if="logs.length === 0" class="empty-state"><p>暂无活动日志</p></div>
      <table v-else class="log-table">
        <thead>
          <tr><th>时间</th><th>用户ID</th><th>昵称</th><th>操作类型</th><th>目标</th></tr>
        </thead>
        <tbody>
          <tr v-for="item in logs" :key="item.id">
            <td class="log-time">{{ item.created_at?.slice(0, 19) || '--' }}</td>
            <td>{{ item.user_id }}</td>
            <td>{{ item.user_nickname || '--' }}</td>
            <td><span class="action-tag">{{ activityLabelMap[item.activity_type] || item.activity_type }}</span></td>
            <td class="log-target">{{ item.target_type ? item.target_type + ' #' + item.target_id : '--' }}</td>
          </tr>
        </tbody>
      </table>
      <Pagination v-if="logPagination.total > logPagination.size" :current="logPagination.page" :total="logPagination.total" :size="logPagination.size" @update:current="loadLogs" />
    </div>

    <!-- ============== Tab 2: User Activity Summary ============== -->
    <div v-if="activeTab === 'summary'">
      <div class="filter-bar">
        <label class="filter-label">排序：
          <select v-model="summarySort.by" class="filter-select" @change="changeSummarySort(summarySort.by)">
            <option value="total_actions">总操作数</option>
            <option value="posts_count">发帖数</option>
            <option value="comments_count">评论数</option>
            <option value="last_active">最后活跃</option>
            <option value="account_age">注册天数</option>
          </select>
          {{ summarySort.order === 'desc' ? '↓' : '↑' }}
        </label>
      </div>

      <Loading v-if="loadingSummary" variant="skeleton" :rows="3" />
      <div v-else-if="summary.length === 0" class="empty-state"><p>暂无用户数据</p></div>
      <table v-else class="summary-table">
        <thead>
          <tr>
            <th>用户</th>
            <th class="sortable" @click="changeSummarySort('total_actions')">总操作{{ sortIndicator('total_actions') }}</th>
            <th class="sortable" @click="changeSummarySort('posts_count')">发帖{{ sortIndicator('posts_count') }}</th>
            <th class="sortable" @click="changeSummarySort('comments_count')">评论{{ sortIndicator('comments_count') }}</th>
            <th>点赞</th>
            <th class="sortable" @click="changeSummarySort('last_active')">最后活跃{{ sortIndicator('last_active') }}</th>
            <th>发帖频率(/周)</th>
            <th class="sortable" @click="changeSummarySort('account_age')">注册天数{{ sortIndicator('account_age') }}</th>
            <th>状态</th>
            <th>操作</th>
          </tr>
        </thead>
        <tbody>
          <tr v-for="user in summary" :key="user.user_id" :class="{ 'row--high-freq': user.posts_count > 10 }">
            <td class="user-cell">
              <img v-if="user.avatar_url" :src="user.avatar_url" class="avatar-mini" />
              <span v-else class="avatar-placeholder">{{ user.nickname?.charAt(0) }}</span>
              <span class="user-name">{{ user.nickname }}</span>
            </td>
            <td>{{ user.total_actions }}</td>
            <td>{{ user.posts_count }}</td>
            <td>{{ user.comments_count }}</td>
            <td>{{ user.likes_count }}</td>
            <td class="log-time">{{ user.last_active_at?.slice(0, 10) || '--' }}</td>
            <td>{{ user.posting_frequency }}</td>
            <td>{{ user.account_age_days }}</td>
            <td><span :class="user.status === 'disabled' ? 'status--banned' : 'status--active'">{{ user.status === 'disabled' ? '封禁' : '正常' }}</span></td>
            <td><button class="view-btn" @click="viewTimeline(user.user_id)">查看详情</button></td>
          </tr>
        </tbody>
      </table>
      <Pagination v-if="summaryPagination.total > summaryPagination.size" :current="summaryPagination.page" :total="summaryPagination.total" :size="summaryPagination.size" @update:current="loadSummary" />

      <!-- Timeline Modal -->
      <div v-if="showTimeline" class="modal-overlay" @click.self="closeTimeline">
        <div class="modal">
          <header class="modal-header">
            <h3 v-if="timelineUser">{{ timelineUser.nickname }} 的活动时间线</h3>
            <button class="modal-close" @click="closeTimeline">✕</button>
          </header>
          <Loading v-if="loadingTimeline" variant="spinner" text="加载中..." />
          <div v-else>
            <div class="modal-user-info" v-if="timelineUser">
              <span>ID: {{ timelineUser.id }}</span>
              <span>状态: {{ timelineUser.status }}</span>
              <span>注册: {{ timelineUser.created_at?.slice(0, 10) }}</span>
            </div>
            <table v-if="timelineData.length" class="timeline-table">
              <thead>
                <tr><th>日期</th><th>登录</th><th>发帖</th><th>评论</th><th>点赞</th><th>其他</th></tr>
              </thead>
              <tbody>
                <tr v-for="day in timelineData" :key="day.date">
                  <td>{{ day.date }}</td>
                  <td>{{ day.login || 0 }}</td>
                  <td>{{ day.post || 0 }}</td>
                  <td>{{ day.comment || 0 }}</td>
                  <td>{{ day.like || 0 }}</td>
                  <td>{{ day.other || 0 }}</td>
                </tr>
              </tbody>
            </table>
            <p v-else class="empty-state">该时间段内无活动记录</p>
            <!-- 内容质量评分 -->
            <div v-if="qualityData" style="margin-top:16px">
              <h4>内容质量评分</h4>
              <p style="font-size:13px;color:var(--color-text-secondary);margin:4px 0">
                平均质量分：<strong :style="{color: qualityData.avg_score >= 60 ? 'var(--color-success)' : qualityData.avg_score >= 30 ? 'var(--color-warning)' : 'var(--color-danger)'}">{{ qualityData.avg_score }}/100</strong>
                （最近 {{ qualityData.posts_scored }} 篇帖子）
              </p>
              <div v-if="qualityData.details?.length" style="margin-top:8px">
                <div v-for="qs in qualityData.details.slice(0, 5)" :key="qs.post_id" class="activity-item" style="justify-content:space-between">
                  <span style="font-size:12px;max-width:300px;overflow:hidden;text-overflow:ellipsis;white-space:nowrap">{{ qs.title }}</span>
                  <span :class="['level-badge', 'level-badge--' + qs.level]">{{ qs.score }}/100 ({{ qs.level }})</span>
                </div>
              </div>
            </div>

            <h4 v-if="recentActivities.length" style="margin-top:16px">最近活动</h4>
            <div v-for="act in recentActivities.slice(0, 10)" :key="act.id" class="activity-item">
              <span class="action-tag" style="margin-right:8px">{{ activityLabelMap[act.activity_type] || act.activity_type }}</span>
              <span class="log-time">{{ act.created_at?.slice(0, 19) }}</span>
              <span class="log-target" style="margin-left:8px" v-if="act.target_type">{{ act.target_type }} #{{ act.target_id }}</span>
            </div>
          </div>
        </div>
      </div>
    </div>

    <!-- ============== Tab 3: Suspicious ============== -->
    <div v-if="activeTab === 'suspicious'">
      <Loading v-if="loadingSuspicious" variant="skeleton" :rows="3" />
      <div v-else-if="suspicious.length === 0" class="empty-state"><p>✅ 暂无异常用户</p></div>
      <div v-else>
        <div class="suspicious-grid">
          <div v-for="item in suspicious" :key="item.user_id + '-' + item.pattern" :class="['suspicious-card', 'severity--' + item.severity]">
            <div class="suspicious-card__header">
              <span class="suspicious-card__user">
                <img v-if="item.avatar_url" :src="item.avatar_url" class="avatar-mini" />
                <span>{{ item.nickname }}</span>
                <span class="suspicious-card__uid">#{{ item.user_id }}</span>
              </span>
              <span :class="['severity-badge', 'severity--' + item.severity]">{{ severityLabel(item.severity) }}</span>
            </div>
            <p class="suspicious-card__pattern">{{ patternLabelMap[item.pattern] || item.pattern }}</p>
            <p class="suspicious-card__detail">{{ item.detail }}</p>
            <div class="suspicious-card__actions">
              <button class="view-btn" @click="viewTimeline(item.user_id)">查看活动</button>
            </div>
          </div>
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

/* ── Filter Bar ── */
.filter-bar { display: flex; align-items: center; gap: 12px; margin-bottom: 16px; flex-wrap: wrap; background: var(--color-bg-card); border: 1px solid var(--color-border); border-radius: 8px; padding: 12px 16px; }
.filter-select, .filter-input { border: 1px solid var(--color-border-input); border-radius: 6px; font: inherit; font-size: 13px; padding: 6px 8px; }
.filter-select:focus, .filter-input:focus { border-color: var(--color-primary); outline: none; }
.filter-label { font-size: 13px; color: var(--color-text-secondary); display: flex; align-items: center; gap: 4px; }
.filter-btn {
  background: var(--color-primary); border: 0; border-radius: 6px; color: #fff;
  cursor: pointer; font: inherit; font-size: 13px; padding: 7px 16px;
}

.empty-state { background: var(--color-bg-card); border: 1px solid var(--color-border); border-radius: 8px; padding: 40px; text-align: center; color: var(--color-text-muted); }

/* ── Tables ── */
.log-table, .summary-table, .timeline-table {
  background: var(--color-bg-card); border: 1px solid var(--color-border);
  border-radius: 8px; width: 100%; border-collapse: collapse; overflow: hidden; margin-bottom: 16px;
}
.log-table th, .log-table td, .summary-table th, .summary-table td, .timeline-table th, .timeline-table td {
  padding: 10px 14px; text-align: left; border-bottom: 1px solid var(--color-border-light); font-size: 13px;
}
.log-table th, .summary-table th, .timeline-table th { background: var(--color-bg-hover); font-weight: 600; }
.sortable { cursor: pointer; user-select: none; }
.sortable:hover { color: var(--color-primary); }
.log-time { color: var(--color-text-muted); font-size: 12px; white-space: nowrap; }
.log-target { color: var(--color-text-muted); font-size: 12px; }

.action-tag {
  background: var(--color-bg-hover); border-radius: 4px; font-size: 12px;
  font-weight: 500; padding: 2px 8px; white-space: nowrap;
}

.user-cell { display: flex; align-items: center; gap: 8px; }
.avatar-mini { width: 28px; height: 28px; border-radius: 50%; object-fit: cover; }
.avatar-placeholder {
  width: 28px; height: 28px; border-radius: 50%; background: var(--color-primary-light);
  color: var(--color-primary); display: flex; align-items: center; justify-content: center;
  font-size: 12px; font-weight: 600;
}
.user-name { font-weight: 500; }
.row--high-freq { background: #fffbeb; }

.status--active { color: var(--color-success); font-size: 12px; font-weight: 600; }
.status--banned { color: var(--color-danger); font-size: 12px; font-weight: 600; }

.view-btn {
  background: none; border: 1px solid var(--color-primary); border-radius: 4px;
  color: var(--color-primary); cursor: pointer; font: inherit; font-size: 12px; padding: 4px 10px;
}
.view-btn:hover { background: var(--color-primary); color: #fff; }

/* ── Modal ── */
.modal-overlay {
  position: fixed; inset: 0; background: rgba(0,0,0,0.4);
  display: flex; align-items: center; justify-content: center; z-index: var(--z-modal, 50);
}
.modal {
  background: var(--color-bg-card); border-radius: 12px; max-height: 80vh; overflow-y: auto;
  padding: 24px; width: min(700px, 90vw);
}
.modal-header { display: flex; align-items: center; justify-content: space-between; margin-bottom: 16px; }
.modal-header h3 { font-size: 18px; margin: 0; }
.modal-close { background: none; border: 0; cursor: pointer; font-size: 18px; padding: 4px 8px; color: var(--color-text-muted); }
.modal-user-info { display: flex; gap: 16px; margin-bottom: 12px; font-size: 13px; color: var(--color-text-secondary); }
.activity-item { display: flex; align-items: center; padding: 6px 0; border-bottom: 1px solid var(--color-border-light); font-size: 13px; }

/* ── Suspicious Cards ── */
.suspicious-grid { display: grid; gap: 12px; }
.suspicious-card {
  background: var(--color-bg-card); border: 1px solid var(--color-border);
  border-radius: 8px; padding: 16px;
}
.suspicious-card.severity--high { border-left: 4px solid var(--color-danger); }
.suspicious-card.severity--medium { border-left: 4px solid var(--color-warning); }
.suspicious-card__header { display: flex; align-items: center; justify-content: space-between; margin-bottom: 8px; flex-wrap: wrap; gap: 8px; }
.suspicious-card__user { display: flex; align-items: center; gap: 8px; font-weight: 600; }
.suspicious-card__uid { color: var(--color-text-muted); font-size: 12px; font-weight: 400; }
.severity-badge { border-radius: 4px; font-size: 12px; font-weight: 600; padding: 2px 8px; }
.severity--high { background: var(--color-danger-light); color: var(--color-danger); }
.severity--medium { background: var(--color-warning-light); color: var(--color-warning); }
.suspicious-card__pattern { color: var(--color-text-primary); font-size: 14px; margin: 0 0 4px; }
.suspicious-card__detail { color: var(--color-text-secondary); font-size: 13px; margin: 0 0 12px; }
.suspicious-card__actions { display: flex; gap: 8px; }

.level-badge { border-radius: 4px; font-size: 11px; font-weight: 600; padding: 2px 8px; }
.level-badge--good { background: var(--color-success-light); color: var(--color-success); }
.level-badge--medium { background: var(--color-warning-light); color: var(--color-warning); }
.level-badge--low { background: var(--color-danger-light); color: var(--color-danger); }

@media (max-width: 780px) {
  .admin-nav__item { padding: 10px 14px; font-size: 13px; }
  .filter-bar { flex-direction: column; align-items: flex-start; }
  .log-table th, .log-table td, .summary-table th, .summary-table td { padding: 8px 10px; font-size: 12px; }
  .modal { width: 95vw; padding: 16px; }
}
</style>
