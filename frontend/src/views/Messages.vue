<script setup>
import { ref } from 'vue'
import AppLayout from '../components/layout/AppLayout.vue'
import EmptyState from '../components/common/EmptyState.vue'
</script>

<template>
  <AppLayout>
    <header class="toolbar">
      <div>
        <h1>私信</h1>
        <p>与其他投资者交流</p>
      </div>
    </header>

    <EmptyState icon="✉️" title="私信功能" description="私信系统将在后续版本中完善" />
  </AppLayout>
</template>

<style scoped>
.toolbar { margin-bottom: 24px; }
.toolbar h1 { font-size: 28px; margin: 0 0 8px; }
.toolbar p { color: var(--color-text-secondary); margin: 0; }
</style>
