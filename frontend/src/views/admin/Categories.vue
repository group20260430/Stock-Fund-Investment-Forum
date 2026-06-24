<script setup>
import { ref, onMounted } from 'vue'
import { useToastStore } from '../../stores/toast'
import { createCategory, updateCategory, deleteCategory } from '../../api/admin'
import Loading from '../../components/common/Loading.vue'
import { api } from '../../utils/request'

const toast = useToastStore()
const categories = ref([])
const loading = ref(true)
const editing = ref(null) // 正在编辑的分类
const showForm = ref(false)
const form = ref({ name: '', description: '', sort_order: 0 })

onMounted(async () => {
  await loadCategories()
})

async function loadCategories() {
  loading.value = true
  try {
    const data = await api.get('/categories')
    categories.value = Array.isArray(data) ? data : []
  } catch {
    categories.value = []
  } finally {
    loading.value = false
  }
}

function openCreate() {
  editing.value = null
  form.value = { name: '', description: '', sort_order: categories.value.length + 1 }
  showForm.value = true
}

function openEdit(cat) {
  editing.value = cat
  form.value = { name: cat.name, description: cat.description || '', sort_order: cat.sort_order }
  showForm.value = true
}

async function handleSave() {
  if (!form.value.name.trim()) { toast.warning('请输入板块名称'); return }
  try {
    if (editing.value) {
      await updateCategory(editing.value.id, form.value)
      toast.success('板块已更新')
    } else {
      await createCategory(form.value)
      toast.success('板块已创建')
    }
    showForm.value = false
    await loadCategories()
  } catch (err) {
    toast.error(err.message || '操作失败')
  }
}

async function handleDelete(cat) {
  if (cat.post_count > 0) {
    toast.info('该板块下有帖子，将隐藏而非删除')
  }
  try {
    await deleteCategory(cat.id)
    toast.success('板块已移除')
    await loadCategories()
  } catch (err) {
    toast.error(err.message || '删除失败')
  }
}

function cancelForm() {
  showForm.value = false
  editing.value = null
}
</script>

<template>
    <header class="toolbar">
      <h1>管理后台 / 板块管理</h1>
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
      <router-link to="/admin/engagement" class="admin-nav__item">用户参与度</router-link>
      <router-link to="/admin/categories" class="admin-nav__item admin-nav__item--active">板块管理</router-link>
    </div>

    <!-- 表单 -->
    <div v-if="showForm" class="admin-card form-card">
      <h3>{{ editing ? '编辑板块' : '新建板块' }}</h3>
      <div class="form-group">
        <label>板块名称</label>
        <input v-model="form.name" class="form-input" placeholder="输入板块名称" maxlength="50" />
      </div>
      <div class="form-group">
        <label>描述</label>
        <input v-model="form.description" class="form-input" placeholder="板块描述（可选）" maxlength="255" />
      </div>
      <div class="form-group">
        <label>排序</label>
        <input v-model.number="form.sort_order" type="number" class="form-input form-input--short" min="0" />
      </div>
      <div class="form-actions">
        <button class="admin-btn admin-btn--secondary" @click="cancelForm">取消</button>
        <button class="admin-btn admin-btn--primary" @click="handleSave">{{ editing ? '保存' : '创建' }}</button>
      </div>
    </div>

    <!-- 列表 -->
    <Loading v-if="loading" variant="skeleton" :rows="5" />
    <div v-else class="cat-list">
      <div class="cat-list__header">
        <span>排序</span>
        <span>名称</span>
        <span>描述</span>
        <span>帖子数</span>
        <span>状态</span>
        <span>操作</span>
      </div>
      <div
        v-for="cat in categories"
        :key="cat.id"
        :class="['cat-list__row', { 'cat-list__row--inactive': !cat.is_active }]"
      >
        <span>{{ cat.sort_order }}</span>
        <span><strong>{{ cat.name }}</strong></span>
        <span class="cat-desc">{{ cat.description || '-' }}</span>
        <span>{{ cat.post_count }}</span>
        <span :class="cat.is_active ? 'tag-green' : 'tag-gray'">{{ cat.is_active ? '启用' : '隐藏' }}</span>
        <span class="cat-actions">
          <button class="admin-btn admin-btn--sm" @click="openEdit(cat)">编辑</button>
          <button class="admin-btn admin-btn--sm admin-btn--danger" @click="handleDelete(cat)">删除</button>
        </span>
      </div>
    </div>

    <button v-if="!showForm" class="admin-btn admin-btn--primary add-btn" @click="openCreate">+ 新建板块</button>
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

.form-card { padding: 20px; margin-bottom: 24px; background: var(--color-bg-card); border-radius: 8px; border: 1px solid var(--color-border); }
.form-group { margin-bottom: 12px; }
.form-group label { display: block; margin-bottom: 4px; font-size: 0.85rem; font-weight: 500; }
.form-input { width: 100%; padding: 8px 12px; border: 1px solid var(--color-border); border-radius: 6px; font-size: 0.9rem; box-sizing: border-box; }
.form-input--short { width: 100px; }
.form-actions { display: flex; gap: 8px; justify-content: flex-end; margin-top: 16px; }
.cat-list { background: var(--color-bg-card); border-radius: 8px; border: 1px solid var(--color-border); overflow: hidden; }
.cat-list__header, .cat-list__row { display: grid; grid-template-columns: 50px 1fr 2fr 70px 60px 100px; gap: 8px; padding: 10px 16px; align-items: center; font-size: 0.85rem; }
.cat-list__header { background: var(--color-bg-hover); font-weight: 600; color: var(--color-text-muted); }
.cat-list__row { border-top: 1px solid var(--color-border); }
.cat-list__row--inactive { opacity: 0.5; }
.cat-desc { overflow: hidden; text-overflow: ellipsis; white-space: nowrap; color: var(--color-text-muted); }
.cat-actions { display: flex; gap: 4px; }
.tag-green { color: #059669; font-size: 0.8rem; }
.tag-gray { color: #9ca3af; font-size: 0.8rem; }
.add-btn { margin-top: 16px; }
.admin-btn { padding: 6px 14px; border-radius: 6px; border: 1px solid #d1d5db; background: #fff; cursor: pointer; font-size: 0.85rem; }
.admin-btn--primary { background: var(--color-primary); color: #fff; border-color: var(--color-primary); }
.admin-btn--secondary { background: #f3f4f6; color: #374151; }
.admin-btn--danger { color: #ef4444; border-color: #fca5a5; }
.admin-btn--sm { padding: 4px 10px; font-size: 0.8rem; }
.admin-btn:hover { opacity: 0.9; }
</style>
