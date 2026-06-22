<script setup>
/**
 * AppIcon — 统一图标组件
 *
 * 基于 @iconify/vue 的运行时 SVG 加载。
 * 用法：<AppIcon name="like" :size="20" />
 *       <AppIcon name="like" :size="20" solid />
 *
 * @param {string}  name  - 语义图标名，对应 utils/icons.js 中的 key
 * @param {number}  size  - 图标尺寸（px），默认 20
 * @param {boolean} solid - 是否使用实心变体，默认 false
 */
import { computed } from 'vue'
import { Icon } from '@iconify/vue'
import { iconMap } from '../../utils/icons'

const props = defineProps({
  name: { type: String, required: true },
  size: { type: [Number, String], default: 20 },
  solid: { type: Boolean, default: false },
})

const iconId = computed(() => {
  const key = props.solid ? `${props.name}Solid` : props.name
  return iconMap[key] || iconMap[props.name]
})
</script>

<template>
  <span
    class="app-icon"
    :style="{ width: `${size}px`, height: `${size}px` }"
    :aria-label="name"
    role="img"
  >
    <Icon :icon="iconId" :width="size" :height="size" />
  </span>
</template>

<style scoped>
.app-icon {
  display: inline-flex;
  align-items: center;
  justify-content: center;
  flex-shrink: 0;
}

.app-icon :deep(svg) {
  display: block;
}
</style>
