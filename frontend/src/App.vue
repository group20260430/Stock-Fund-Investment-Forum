<script setup>
// App 根组件 — 页面过渡 + 路由出口
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
