<script setup>
defineProps({
  /** 'skeleton' | 'spinner' */
  variant: {
    type: String,
    default: 'spinner',
  },
  /** 骨架屏行数（variant=skeleton 时有效） */
  rows: {
    type: Number,
    default: 3,
  },
  text: {
    type: String,
    default: '加载中...',
  },
})
</script>

<template>
  <div v-if="variant === 'skeleton'" class="skeleton" role="status" aria-label="加载中">
    <div
      v-for="i in rows"
      :key="i"
      class="skeleton__row"
      :style="{ animationDelay: `${i * 0.1}s` }"
    >
      <div class="skeleton__line skeleton__line--short" />
      <div class="skeleton__line" />
      <div class="skeleton__line skeleton__line--medium" />
    </div>
  </div>

  <div v-else class="spinner" role="status" aria-label="加载中">
    <div class="spinner__icon" />
    <p v-if="text">{{ text }}</p>
  </div>
</template>

<style scoped>
.skeleton {
  display: grid;
  gap: 16px;
  padding: 8px 0;
}

.skeleton__row {
  animation: pulse 1.6s ease-in-out infinite;
  background: var(--color-bg-card);
  border: 1px solid var(--color-border);
  border-radius: 8px;
  display: grid;
  gap: 10px;
  padding: 20px;
}

.skeleton__line {
  background: var(--color-border);
  border-radius: 4px;
  height: 14px;
}

.skeleton__line--short {
  width: 30%;
}

.skeleton__line--medium {
  width: 60%;
}

@keyframes pulse {
  0%, 100% { opacity: 1; }
  50% { opacity: 0.5; }
}

.spinner {
  align-items: center;
  display: flex;
  flex-direction: column;
  gap: 12px;
  justify-content: center;
  padding: 48px 0;
}

.spinner__icon {
  animation: spin 0.7s linear infinite;
  border: 3px solid var(--color-border);
  border-radius: 50%;
  border-top-color: var(--color-primary);
  height: 32px;
  width: 32px;
}

@keyframes spin {
  to { transform: rotate(360deg); }
}

.spinner p {
  color: var(--color-text-secondary);
  font-size: 14px;
  margin: 0;
}
</style>
