<script setup>
import AppIcon from './AppIcon.vue'

defineProps({
  icon: { type: String, default: 'empty' },
  title: { type: String, default: '暂无内容' },
  description: { type: String, default: '' },
  actionLabel: { type: String, default: '' },
})

defineEmits(['action'])
</script>

<template>
  <div class="empty-state">
    <AppIcon :name="icon" :size="48" />
    <h3>{{ title }}</h3>
    <p v-if="description">{{ description }}</p>
    <button v-if="actionLabel" class="empty-state__btn" @click="$emit('action')">
      {{ actionLabel }}
    </button>
  </div>
</template>

<style scoped>
.empty-state {
  align-items: center;
  display: flex;
  flex-direction: column;
  gap: 8px;
  justify-content: center;
  padding: 64px 24px;
  text-align: center;
}

.empty-state__icon {
  font-size: 48px;
  margin-bottom: 8px;
}

.empty-state h3 {
  color: var(--color-text-body);
  font-size: 18px;
  font-weight: 600;
  margin: 0;
}

.empty-state p {
  color: var(--color-text-muted);
  font-size: 14px;
  margin: 0;
  max-width: 320px;
}

.empty-state__btn {
  background: var(--color-primary);
  border: 0;
  border-radius: 6px;
  color: var(--color-bg-card);
  cursor: pointer;
  font: inherit;
  font-size: 14px;
  margin-top: 8px;
  padding: 10px 20px;
}

.empty-state__btn:hover {
  background: var(--color-primary-hover);
}
</style>
