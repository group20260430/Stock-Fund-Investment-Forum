<script setup>
import { ref } from 'vue'
import { useRouter } from 'vue-router'
import { useToastStore } from '../stores/toast'
import { createGroup } from '../api/groups'
import AppLayout from '../components/layout/AppLayout.vue'

const router = useRouter()
const toast = useToastStore()

const form = ref({
  name: '',
  description: '',
  visibility: 'public',
  need_approval: false,
})
const submitting = ref(false)

async function handleSubmit() {
  if (!form.value.name.trim()) {
    toast.warning('请输入群组名称')
    return
  }
  submitting.value = true
  try {
    const result = await createGroup(form.value)
    toast.success('群组创建成功')
    router.push('/groups/' + result.id)
  } catch (err) {
    toast.error(err.message || '创建失败')
  } finally {
    submitting.value = false
  }
}
</script>

<template>
  <AppLayout>
    <header class="toolbar">
      <button class="back-btn" @click="router.back()">&larr; 返回</button>
      <h1>创建群组</h1>
      <p>创建一个投资交流群组</p>
    </header>

    <div class="create-card">
      <div class="form-field">
        <label>群组名称 <span class="required">*</span></label>
        <input v-model="form.name" class="form-input" placeholder="例如：价值投资交流群" maxlength="50" />
      </div>
      <div class="form-field">
        <label>群组简介</label>
        <textarea v-model="form.description" class="form-input" rows="3" placeholder="介绍一下这个群组的主题和规则" maxlength="500" />
      </div>
      <div class="form-field">
        <label>可见性</label>
        <select v-model="form.visibility" class="form-input">
          <option value="public">公开 - 任何人都可看到</option>
          <option value="private">私密 - 仅成员可见</option>
        </select>
      </div>
      <div class="form-field">
        <label class="checkbox-label">
          <input v-model="form.need_approval" type="checkbox" />
          <span>需要管理员审批加入申请</span>
        </label>
      </div>
      <button class="submit-btn" :disabled="submitting || !form.name.trim()" @click="handleSubmit">
        {{ submitting ? '创建中...' : '创建群组' }}
      </button>
    </div>
  </AppLayout>
</template>

<style scoped>
.toolbar { margin-bottom: 24px; }
.toolbar h1 { font-size: 28px; margin: 8px 0 8px; }
.toolbar p { color: var(--color-text-secondary); margin: 0; }
.back-btn { background: none; border: 0; color: var(--color-text-secondary); cursor: pointer; font: inherit; font-size: 14px; padding: 4px 0; }
.back-btn:hover { color: var(--color-primary); }
.create-card {
  background: var(--color-bg-card);
  border: 1px solid var(--color-border);
  border-radius: 10px;
  max-width: 520px;
  padding: 24px;
}
.form-field { display: grid; gap: 6px; margin-bottom: 16px; }
.form-field label { color: var(--color-text-body); font-size: 14px; font-weight: 500; }
.required { color: var(--color-danger); }
.form-input {
  border: 1px solid var(--color-border-input);
  border-radius: 8px;
  font: inherit;
  font-size: 15px;
  padding: 10px 14px;
  width: 100%;
  box-sizing: border-box;
}
.form-input:focus { border-color: var(--color-primary); outline: none; box-shadow: 0 0 0 3px var(--color-primary-ring); }
.checkbox-label { align-items: center; display: flex; gap: 8px; cursor: pointer; font-weight: 400 !important; }
.checkbox-label input { accent-color: var(--color-primary); }
.submit-btn {
  background: var(--color-primary);
  border: 0;
  border-radius: 8px;
  color: #fff;
  cursor: pointer;
  font: inherit;
  font-size: 15px;
  padding: 12px 24px;
  width: 100%;
}
.submit-btn:hover { background: var(--color-primary-hover); }
.submit-btn:disabled { opacity: 0.6; cursor: not-allowed; }
</style>
