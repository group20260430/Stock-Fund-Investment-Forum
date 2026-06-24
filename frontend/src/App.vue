<script setup>
import { onMounted } from 'vue'
import { useRoute } from 'vue-router'
import { useAuthStore } from './stores/auth'
import AppLayout from './components/layout/AppLayout.vue'

const auth = useAuthStore()
const route = useRoute()

// 应用初始化：如果有 token 则拉取最新用户信息
onMounted(() => {
  if (auth.isLoggedIn) {
    auth.fetchUser()
  }
})
</script>

<template>
  <component :is="route.meta.layout === false ? 'div' : AppLayout">
    <router-view v-slot="{ Component, route: resolvedRoute }">
      <transition
        name="page"
        mode="out-in"
        appear
      >
        <div :key="resolvedRoute.path" class="route-page-wrapper">
          <component :is="Component" />
        </div>
      </transition>
    </router-view>
  </component>
</template>
