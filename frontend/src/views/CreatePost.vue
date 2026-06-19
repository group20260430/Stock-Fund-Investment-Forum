<script setup>
import { ref } from 'vue'
import { useRouter } from 'vue-router'
import { useAuthStore } from '../stores/auth'
import AppLayout from '../components/layout/AppLayout.vue'
import PostEditor from '../components/post/PostEditor.vue'

const router = useRouter()
const auth = useAuthStore()
const showEditor = ref(true)

function closeEditor() {
  router.back()
}
</script>

<template>
  <AppLayout>
    <!-- 未登录提示 -->
    <div v-if="!auth.isLoggedIn" class="no-auth">
      <h2>请先登录</h2>
      <p>发布帖子需要登录账户</p>
      <button class="no-auth__btn" @click="router.push('/login')">去登录</button>
    </div>

    <!-- 编辑器 -->
    <PostEditor v-else :post="null" @close="closeEditor" />
  </AppLayout>
</template>

<style scoped>
.no-auth {
  align-items: center;
  display: flex;
  flex-direction: column;
  gap: 8px;
  justify-content: center;
  padding: 80px 24px;
  text-align: center;
}

.no-auth h2 {
  margin: 0;
}

.no-auth p {
  color: var(--color-text-secondary);
  margin: 0;
}

.no-auth__btn {
  background: var(--color-primary);
  border: 0;
  border-radius: 8px;
  color: var(--color-bg-card);
  cursor: pointer;
  font: inherit;
  font-size: 15px;
  margin-top: 12px;
  padding: 10px 24px;
}
</style>
