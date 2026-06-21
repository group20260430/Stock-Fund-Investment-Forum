<script setup>
import { ref, onMounted } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { useAuthStore } from '../stores/auth'
import { fetchPostDetail } from '../api/posts'
import AppLayout from '../components/layout/AppLayout.vue'
import PostEditor from '../components/post/PostEditor.vue'
import Loading from '../components/common/Loading.vue'

const route = useRoute()
const router = useRouter()
const auth = useAuthStore()

const editingPost = ref(null)
const loadingPost = ref(false)
const isEdit = ref(!!route.params.id && route.name === 'edit-post')

onMounted(async () => {
  if (isEdit.value) {
    loadingPost.value = true
    try {
      editingPost.value = await fetchPostDetail(route.params.id)
    } catch (err) {
      console.error('加载帖子失败:', err.message)
    } finally {
      loadingPost.value = false
    }
  }
})

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

    <Loading v-else-if="isEdit && loadingPost" variant="skeleton" :rows="2" />

    <!-- 编辑器 -->
    <PostEditor v-else :post="editingPost" @close="closeEditor" @saved="closeEditor" />
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
