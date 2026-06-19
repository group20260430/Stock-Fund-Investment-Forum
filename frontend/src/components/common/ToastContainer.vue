<script setup>
import { useToastStore } from '../../stores/toast'
import AppIcon from './AppIcon.vue'

const toast = useToastStore()

const iconMap = {
  success: 'success',
  error: 'error',
  warning: 'error',
  info: 'info',
}

const labelMap = {
  success: '成功',
  error: '错误',
  warning: '警告',
  info: '提示',
}

function dismiss(id) {
  toast.remove(id)
}
</script>

<template>
  <TransitionGroup
    name="toast"
    tag="div"
    class="toast-container"
    aria-live="polite"
  >
    <div
      v-for="t in toast.toasts"
      :key="t.id"
      :class="['toast', `toast--${t.type}`]"
      role="alert"
    >
      <div class="toast__icon">
        <AppIcon :name="iconMap[t.type]" :size="18" />
      </div>
      <p class="toast__message">{{ t.message }}</p>
      <button
        class="toast__close"
        aria-label="关闭"
        @click="dismiss(t.id)"
      >
        <AppIcon name="close" :size="14" />
      </button>
      <!-- 进度条 -->
      <div
        class="toast__progress"
        :style="{ animationDuration: `${t.duration}ms` }"
      />
    </div>
  </TransitionGroup>
</template>

<style scoped>
.toast-container {
  bottom: 24px;
  display: grid;
  gap: 10px;
  position: fixed;
  right: 24px;
  z-index: var(--z-toast, 100);
  pointer-events: none;
}

.toast {
  align-items: center;
  background: rgba(255, 255, 255, 0.95);
  backdrop-filter: blur(12px);
  -webkit-backdrop-filter: blur(12px);
  border-radius: var(--radius-xl);
  box-shadow: var(--shadow-lg);
  display: flex;
  gap: 10px;
  max-width: 380px;
  min-width: 280px;
  overflow: hidden;
  padding: 14px 16px;
  pointer-events: auto;
  position: relative;
  transition: transform var(--duration-normal) var(--ease-out-expo),
              opacity var(--duration-normal) var(--ease-out-expo);
}

.toast--success {
  box-shadow: inset 3px 0 0 var(--color-success), var(--shadow-lg);
}

.toast--error {
  box-shadow: inset 3px 0 0 var(--color-danger), var(--shadow-lg);
}

.toast--warning {
  box-shadow: inset 3px 0 0 var(--color-warning), var(--shadow-lg);
}

.toast--info {
  box-shadow: inset 3px 0 0 var(--color-info), var(--shadow-lg);
}

.toast__icon {
  color: var(--color-primary);
  flex-shrink: 0;
}

.toast--success .toast__icon { color: var(--color-success); }
.toast--error .toast__icon { color: var(--color-danger); }
.toast--warning .toast__icon { color: var(--color-warning); }
.toast--info .toast__icon { color: var(--color-info); }

.toast__message {
  color: var(--color-text-body);
  flex: 1;
  font-size: var(--font-size-base);
  line-height: var(--line-height-normal);
  margin: 0;
  word-break: break-word;
}

.toast__close {
  align-items: center;
  background: none;
  border: 0;
  border-radius: var(--radius-sm);
  color: var(--color-text-muted);
  cursor: pointer;
  display: flex;
  flex-shrink: 0;
  padding: 4px;
}

.toast__close:hover {
  color: var(--color-text-body);
  background: var(--color-bg-hover);
}

.toast__progress {
  animation: toast-progress linear 1 forwards;
  background: var(--color-primary);
  bottom: 0;
  height: 2px;
  left: 0;
  opacity: 0.4;
  position: absolute;
}

.toast--success .toast__progress { background: var(--color-success); }
.toast--error .toast__progress { background: var(--color-danger); }
.toast--warning .toast__progress { background: var(--color-warning); }
.toast--info .toast__progress { background: var(--color-info); }

@keyframes toast-progress {
  from { width: 100%; }
  to { width: 0%; }
}

/* Toast 进出动画 */
.toast-enter-active {
  transition: all var(--duration-slow) var(--ease-out-expo);
}
.toast-leave-active {
  transition: all var(--duration-normal) var(--ease-in-out);
  position: absolute; /* 避免离开时占位 */
}
.toast-enter-from {
  opacity: 0;
  transform: translateX(100%);
}
.toast-leave-to {
  opacity: 0;
  transform: translateX(100%) scale(0.95);
}

@media (max-width: 780px) {
  .toast-container {
    bottom: 16px;
    left: 16px;
    right: 16px;
  }

  .toast {
    max-width: none;
    min-width: 0;
  }
}
</style>
