<script setup>
import { onMounted } from 'vue'
import { useAuthStore } from './stores/auth'

// 应用初始化：如果有 token 但没有缓存的用户信息，自动拉取
const auth = useAuthStore()
onMounted(() => {
  if (auth.isLoggedIn && !auth.user) {
    auth.fetchUser()
  }
})
</script>

<template>
  <router-view v-slot="{ Component, route }">
    <transition
      name="page"
      mode="out-in"
      appear
    >
      <component :is="Component" :key="route.path" />
    </transition>
  </router-view>
</template>
