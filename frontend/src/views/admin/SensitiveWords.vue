<script setup>
import { ref, onMounted } from 'vue'
import { useToastStore } from '../../stores/toast'
import { fetchSensitiveWords, addSensitiveWord, deleteSensitiveWord } from '../../api/admin'
import Loading from '../../components/common/Loading.vue'

const toast = useToastStore()

const items = ref([])
const loading = ref(true)
const newWord = ref('')
const newLevel = ref('medium')
const adding = ref(false)

async function load() {
  loading.value = true
  try {
    const data = await fetchSensitiveWords()
    items.value = data?.items || data || []
  } catch (err) {
    toast.error('加载失败: ' + err.message)
  } finally {
    loading.value = false
  }
}

async function handleAdd() {
  if (!newWord.value.trim()) return
  adding.value = true
  try {
    await addSensitiveWord(newWord.value.trim(), newLevel.value)
    toast.success('敏感词已添加')
    newWord.value = ''
    await load()
  } catch (err) {
    toast.error(err.message || '添加失败')
  } finally {
    adding.value = false
  }
}

async function handleDelete(id) {
  try {
    await deleteSensitiveWord(id)
    toast.success('已删除')
    items.value = items.value.filter(item => item.id !== id)
  } catch (err) {
    toast.error(err.message || '删除失败')
  }
}

onMounted(load)
</script>

<template>
    <header class="toolbar"><h1>管理后台 / 敏感词管理</h1></header>
    <div class="admin-nav">
      <router-link to="/admin" class="admin-nav__item">总览</router-link>
      <router-link to="/admin/review" class="admin-nav__item">审核队列</router-link>
      <router-link to="/admin/users" class="admin-nav__item">用户管理</router-link>
      <router-link to="/admin/certifications" class="admin-nav__item">认证审核</router-link>
      <router-link to="/admin/sensitive-words" class="admin-nav__item admin-nav__item--active">敏感词</router-link>
      <router-link to="/admin/compliance" class="admin-nav__item">合规检查</router-link>
      <router-link to="/admin/duplicate-content" class="admin-nav__item">重复检测</router-link>
      <router-link to="/admin/behavior" class="admin-nav__item">行为监控</router-link>
      <router-link to="/admin/logs" class="admin-nav__item">操作日志</router-link>
      <router-link to="/admin/hot-topics" class="admin-nav__item">热门话题分析</router-link>
      <router-link to="/admin/engagement" class="admin-nav__item">用户参与度</router-link>
      <router-link to="/admin/categories" class="admin-nav__item">板块管理</router-link>
    </div>

    <div class="add-form">
      <input v-model="newWord" class="form-input" placeholder="输入敏感词" maxlength="100" @keyup.enter="handleAdd" />
      <select v-model="newLevel" class="form-select">
        <option value="low">低</option>
        <option value="medium">中</option>
        <option value="high">高</option>
      </select>
      <button class="add-btn" :disabled="adding || !newWord.trim()" @click="handleAdd">
        {{ adding ? '添加中...' : '添加' }}
      </button>
    </div>

    <Loading v-if="loading" variant="skeleton" :rows="2" />

    <div v-else-if="items.length === 0" class="empty-state"><p>暂无敏感词</p></div>

    <table v-else class="word-table">
      <thead>
        <tr><th>词语</th><th>级别</th><th>操作</th></tr>
      </thead>
      <tbody>
        <tr v-for="item in items" :key="item.id">
          <td>{{ item.word }}</td>
          <td><span :class="['level-badge', 'level-badge--' + (item.level || 'medium')]">{{ item.level || 'medium' }}</span></td>
          <td><button class="del-btn" @click="handleDelete(item.id)">删除</button></td>
        </tr>
      </tbody>
    </table>
</template>

<style scoped>
.toolbar { margin-bottom: 24px; }
.toolbar h1 { font-size: 24px; margin: 0; }
.admin-nav { background: var(--color-bg-card); border: 1px solid var(--color-border); border-radius: 8px; display: flex; gap: 0; margin-bottom: 24px; overflow: hidden; flex-wrap: wrap; }
.admin-nav__item { border-bottom: 2px solid transparent; color: var(--color-text-secondary); font-size: 14px; font-weight: 500; padding: 14px 24px; text-decoration: none; }
.admin-nav__item:hover { color: var(--color-text-body); }
.admin-nav__item--active { border-bottom-color: var(--color-primary); color: var(--color-primary); }
.add-form { display: flex; gap: 8px; margin-bottom: 16px; max-width: 500px; }
.form-input { border: 1px solid var(--color-border-input); border-radius: 6px; flex: 1; font: inherit; font-size: 14px; padding: 8px 12px; }
.form-input:focus { border-color: var(--color-primary); outline: none; }
.form-select { border: 1px solid var(--color-border-input); border-radius: 6px; font: inherit; padding: 8px; }
.add-btn { background: var(--color-primary); border: 0; border-radius: 6px; color: #fff; cursor: pointer; font: inherit; padding: 8px 20px; white-space: nowrap; }
.add-btn:disabled { opacity: 0.6; }
.word-table { background: var(--color-bg-card); border: 1px solid var(--color-border); border-radius: 8px; width: 100%; border-collapse: collapse; overflow: hidden; }
.word-table th, .word-table td { padding: 12px 16px; text-align: left; border-bottom: 1px solid var(--color-border-light); font-size: 14px; }
.word-table th { background: var(--color-bg-hover); font-weight: 600; }
.level-badge { border-radius: 4px; font-size: 12px; font-weight: 600; padding: 2px 8px; }
.level-badge--low { background: var(--color-success-light); color: var(--color-success); }
.level-badge--medium { background: var(--color-warning-light); color: var(--color-warning); }
.level-badge--high { background: var(--color-danger-light); color: var(--color-danger); }
.del-btn { background: none; border: 1px solid var(--color-danger); border-radius: 4px; color: var(--color-danger); cursor: pointer; font: inherit; font-size: 13px; padding: 4px 12px; }
.del-btn:hover { background: var(--color-danger); color: #fff; }
.empty-state { background: var(--color-bg-card); border: 1px solid var(--color-border); border-radius: 8px; padding: 40px; text-align: center; color: var(--color-text-muted); }
</style>
