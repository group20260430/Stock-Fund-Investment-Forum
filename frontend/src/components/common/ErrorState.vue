<script setup>
import AppIcon from './AppIcon.vue'

defineProps({
  message: { type: String, default: '加载失败，请稍后重试' },
})

defineEmits(['retry'])
</script>

<template>
  <div class="error-state">
    <AppIcon name="error" :size="48" />
    <h3>出错了</h3>
    <p>{{ message }}</p>
    <button class="error-state__btn" @click="$emit('retry')">
      重试
    </button>
  </div>
</template>

<style scoped>
.error-state {
  align-items: center;
  display: flex;
  flex-direction: column;
  gap: 8px;
  justify-content: center;
  padding: 64px 24px;
  text-align: center;
}

.error-state__icon {
  font-size: 48px;
  margin-bottom: 8px;
}

.error-state h3 {
  color: var(--color-danger-hover);
  font-size: 18px;
  font-weight: 600;
  margin: 0;
}

.error-state p {
  color: var(--color-text-secondary);
  font-size: 14px;
  margin: 0;
  max-width: 360px;
}

.error-state__btn {
  background: var(--color-bg-card);
  border: 1px solid var(--color-border-input);
  border-radius: 6px;
  color: var(--color-text-body);
  cursor: pointer;
  font: inherit;
  font-size: 14px;
  margin-top: 8px;
  padding: 10px 20px;
}

.error-state__btn:hover {
  border-color: var(--color-text-muted);
}
</style>
