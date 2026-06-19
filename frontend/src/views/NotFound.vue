<script setup>
import { useRouter } from 'vue-router'
</script>

<template>
  <div class="not-found">
    <span class="not-found__icon">🔮</span>
    <h1>404</h1>
    <p>页面未找到</p>
    <button class="not-found__btn" @click="$router.push('/')">返回首页</button>
  </div>
</template>

<style scoped>
.not-found {
  align-items: center;
  background: var(--color-bg-page);
  display: flex;
  flex-direction: column;
  gap: 8px;
  justify-content: center;
  min-height: 100vh;
  text-align: center;
}

.not-found__icon { font-size: 64px; }
.not-found h1 { font-size: 72px; color: var(--color-border-input); margin: 0; }
.not-found p { color: var(--color-text-secondary); font-size: 18px; margin: 0; }

.not-found__btn {
  background: var(--color-primary);
  border: 0;
  border-radius: 8px;
  color: var(--color-bg-card);
  cursor: pointer;
  font: inherit;
  font-size: 15px;
  margin-top: 16px;
  padding: 12px 28px;
}

.not-found__btn:hover { background: var(--color-primary-hover); }
</style>
