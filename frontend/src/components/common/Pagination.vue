<script setup>
import { computed } from 'vue'

const props = defineProps({
  current: { type: Number, default: 1 },
  total: { type: Number, default: 0 },
  size: { type: Number, default: 20 },
})

const emit = defineEmits(['update:current'])

const totalPages = computed(() => Math.max(1, Math.ceil(props.total / props.size)))

const pages = computed(() => {
  const current = props.current
  const total = totalPages.value
  const result = []

  // 总是显示第一页
  result.push(1)

  // 计算中间范围
  const start = Math.max(2, current - 2)
  const end = Math.min(total - 1, current + 2)

  if (start > 2) result.push('...')

  for (let i = start; i <= end; i++) {
    result.push(i)
  }

  if (end < total - 1) result.push('...')

  // 总是显示最后一页
  if (total > 1) result.push(total)

  return result
})

function go(page) {
  if (page === '...' || page === props.current || page < 1 || page > totalPages.value) return
  emit('update:current', page)
}
</script>

<template>
  <nav v-if="totalPages > 1" class="pagination" aria-label="分页">
    <button
      class="pagination__btn"
      :disabled="current === 1"
      @click="go(current - 1)"
    >
      &lt; 上一页
    </button>

    <template v-for="page in pages" :key="page">
      <span v-if="page === '...'" class="pagination__ellipsis">...</span>
      <button
        v-else
        :class="['pagination__num', { 'pagination__num--active': page === current }]"
        @click="go(page)"
      >
        {{ page }}
      </button>
    </template>

    <button
      class="pagination__btn"
      :disabled="current === totalPages"
      @click="go(current + 1)"
    >
      下一页 &gt;
    </button>
  </nav>
</template>

<style scoped>
.pagination {
  align-items: center;
  display: flex;
  gap: 4px;
  justify-content: center;
  padding: 24px 0 8px;
}

.pagination__btn,
.pagination__num {
  background: var(--color-bg-card);
  border: 1px solid var(--color-border-input);
  border-radius: 6px;
  color: var(--color-text-body);
  cursor: pointer;
  font: inherit;
  font-size: 14px;
  min-width: 36px;
  padding: 8px 12px;
  text-align: center;
}

.pagination__btn:hover:not(:disabled),
.pagination__num:hover {
  background: var(--color-bg-hover);
  border-color: var(--color-primary);
}

.pagination__btn:disabled {
  color: var(--color-border-input);
  cursor: not-allowed;
}

.pagination__num--active {
  background: var(--color-primary);
  border-color: var(--color-primary);
  color: var(--color-bg-card);
}

.pagination__num--active:hover {
  background: var(--color-primary-hover);
  color: var(--color-bg-card);
}

.pagination__ellipsis {
  color: var(--color-text-muted);
  padding: 0 4px;
}
</style>
