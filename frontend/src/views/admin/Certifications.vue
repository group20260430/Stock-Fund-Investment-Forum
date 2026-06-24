<script setup>
import { ref, onMounted } from 'vue'
import { useToastStore } from '../../stores/toast'
import {
  fetchCertifications, reviewCertification,
  fetchProfessionalCertifications, reviewProfessionalCertification,
} from '../../api/admin'
import Loading from '../../components/common/Loading.vue'

const toast = useToastStore()

const activeTab = ref('identity') // identity | professional
const items = ref([])
const loading = ref(true)
const filter = ref({ status: 'pending' })
const reviewComment = ref({})

const certTypeLabels = { identity: '实名认证', professional: '专业认证' }

async function load() {
  loading.value = true
  try {
    if (activeTab.value === 'identity') {
      items.value = await fetchCertifications({ status: filter.value.status }) || []
    } else {
      items.value = await fetchProfessionalCertifications({ status: filter.value.status }) || []
    }
  } catch (err) {
    toast.error('加载失败: ' + err.message)
    items.value = []
  } finally {
    loading.value = false
  }
}

async function handleReview(item, action) {
  if (action === 'reject' && !(reviewComment.value[item.id] || '').trim()) {
    toast.warning('拒绝时必须填写审核意见')
    return
  }
  try {
    const comment = reviewComment.value[item.id] || ''
    if (activeTab.value === 'identity') {
      await reviewCertification(item.id, action, comment)
    } else {
      await reviewProfessionalCertification(item.id, action, comment)
    }
    toast.success(action === 'approve' ? '认证已通过' : '认证已拒绝')
    items.value = items.value.filter(i => i.id !== item.id)
  } catch (err) {
    toast.error(err.message || '操作失败')
  }
}

function switchTab(tab) {
  activeTab.value = tab
  load()
}

onMounted(load)
</script>

<template>
    <header class="toolbar"><h1>管理后台 / 认证审核</h1></header>
    <div class="admin-nav">
      <router-link to="/admin" class="admin-nav__item">总览</router-link>
      <router-link to="/admin/review" class="admin-nav__item">审核队列</router-link>
      <router-link to="/admin/users" class="admin-nav__item">用户管理</router-link>
      <router-link to="/admin/certifications" class="admin-nav__item admin-nav__item--active">认证审核</router-link>
      <router-link to="/admin/sensitive-words" class="admin-nav__item">敏感词</router-link>
      <router-link to="/admin/logs" class="admin-nav__item">操作日志</router-link>
      <router-link to="/admin/hot-topics" class="admin-nav__item">热门话题分析</router-link>
      <router-link to="/admin/engagement" class="admin-nav__item">用户参与度</router-link>
      <router-link to="/admin/categories" class="admin-nav__item">板块管理</router-link>
    </div>

    <!-- 类型切换 -->
    <div class="tab-bar">
      <button :class="['tab', { 'tab--active': activeTab === 'identity' }]" @click="switchTab('identity')">实名认证</button>
      <button :class="['tab', { 'tab--active': activeTab === 'professional' }]" @click="switchTab('professional')">专业认证</button>
    </div>

    <div class="filter-bar">
      <label>状态：
        <select v-model="filter.status" @change="load()" class="filter-select">
          <option value="pending">待审核</option>
          <option value="approved">已通过</option>
          <option value="rejected">已拒绝</option>
        </select>
      </label>
    </div>

    <Loading v-if="loading" variant="skeleton" :rows="3" />

    <div v-else-if="items.length === 0" class="empty-state"><p>暂无{{ certTypeLabels[activeTab] }}申请</p></div>

    <div v-else class="list">
      <div v-for="item in items" :key="item.id" class="review-card">
        <div class="review-card__header">
          <span class="review-card__type-badge">{{ certTypeLabels[activeTab] }}</span>
          <strong>用户 #{{ item.user_id }}</strong>
          <span :class="['status-badge', 'status-badge--' + item.status]">{{ item.status }}</span>
        </div>

        <!-- 实名认证详情 -->
        <template v-if="activeTab === 'identity'">
          <p class="review-card__info">真实姓名：{{ item.real_name || '未提供' }}</p>
          <p class="review-card__info">身份证号：{{ item.id_number || '未提供' }}</p>
        </template>

        <!-- 专业认证详情 -->
        <template v-else>
          <p class="review-card__info" v-if="item.description">申请说明：{{ item.description }}</p>
          <div class="review-card__docs" v-if="item.qualification_docs?.length">
            <p class="review-card__info">资质证明文件：</p>
            <div v-for="(doc, idx) in item.qualification_docs" :key="idx" class="doc-link">
              <a :href="doc.url" target="_blank" rel="noopener">{{ doc.name || doc.url }}</a>
            </div>
          </div>
        </template>

        <p class="review-card__info">提交时间：{{ item.created_at || '未知' }}</p>

        <div v-if="item.status === 'pending'" class="review-card__actions">
          <button class="btn-approve" @click="handleReview(item, 'approve')">通过</button>
          <div class="reject-group">
            <input v-model="reviewComment[item.id]" class="reject-input" placeholder="拒绝原因（必填）" />
            <button class="btn-reject" @click="handleReview(item, 'reject')">拒绝</button>
          </div>
        </div>
      </div>
    </div>
</template>

<style scoped>
.toolbar { margin-bottom: 24px; }
.toolbar h1 { font-size: 24px; margin: 0; }
.admin-nav { background: var(--color-bg-card); border: 1px solid var(--color-border); border-radius: 8px; display: flex; gap: 0; margin-bottom: 24px; overflow: hidden; }
.admin-nav__item { border-bottom: 2px solid transparent; color: var(--color-text-secondary); font-size: 14px; font-weight: 500; padding: 14px 24px; text-decoration: none; }
.admin-nav__item:hover { color: var(--color-text-body); }
.admin-nav__item--active { border-bottom-color: var(--color-primary); color: var(--color-primary); }

.tab-bar { display: flex; gap: 0; margin-bottom: 16px; }
.tab {
  background: var(--color-bg-hover);
  border: 0;
  border-radius: 8px 8px 0 0;
  color: var(--color-text-secondary);
  cursor: pointer;
  font: inherit;
  font-size: 14px;
  font-weight: 500;
  padding: 10px 24px;
  transition: all 0.15s;
}
.tab--active {
  background: var(--color-bg-card);
  border: 1px solid var(--color-border);
  border-bottom-color: var(--color-bg-card);
  color: var(--color-primary);
  margin-bottom: -1px;
}

.filter-bar { margin-bottom: 16px; }
.filter-select { border: 1px solid var(--color-border-input); border-radius: 6px; font: inherit; padding: 6px 10px; }
.list { display: grid; gap: 12px; }
.review-card { background: var(--color-bg-card); border: 1px solid var(--color-border); border-radius: 8px; padding: 16px; }
.review-card__header { align-items: center; display: flex; gap: 8px; margin-bottom: 8px; flex-wrap: wrap; }
.review-card__type-badge { background: var(--color-primary-light); border-radius: 4px; color: var(--color-primary); font-size: 11px; font-weight: 600; padding: 2px 6px; }
.review-card__info { color: var(--color-text-secondary); font-size: 13px; margin: 4px 0; }
.review-card__docs { margin: 8px 0; }
.doc-link { margin: 4px 0 4px 16px; }
.doc-link a { color: var(--color-primary); font-size: 13px; text-decoration: none; }
.doc-link a:hover { text-decoration: underline; }
.status-badge { border-radius: 4px; font-size: 12px; font-weight: 600; padding: 2px 8px; }
.status-badge--pending { background: var(--color-warning-light); color: var(--color-warning); }
.status-badge--approved { background: var(--color-success-light); color: var(--color-success); }
.status-badge--rejected { background: var(--color-danger-light); color: var(--color-danger); }
.review-card__actions { display: flex; gap: 8px; margin-top: 12px; }
.btn-approve { background: var(--color-success); border: 0; border-radius: 6px; color: #fff; cursor: pointer; font: inherit; font-size: 13px; padding: 8px 16px; }
.reject-group { display: flex; flex: 1; gap: 6px; }
.reject-input { border: 1px solid var(--color-border-input); border-radius: 6px; flex: 1; font: inherit; font-size: 13px; padding: 8px 10px; min-width: 0; }
.btn-reject { background: var(--color-danger); border: 0; border-radius: 6px; color: #fff; cursor: pointer; font: inherit; font-size: 13px; padding: 8px 16px; }
.empty-state { background: var(--color-bg-card); border: 1px solid var(--color-border); border-radius: 8px; padding: 40px; text-align: center; color: var(--color-text-muted); }
</style>
