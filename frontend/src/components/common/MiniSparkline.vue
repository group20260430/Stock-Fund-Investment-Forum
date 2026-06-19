<script setup>
/**
 * MiniSparkline — 迷你 SVG 走势图
 *
 * Props:
 *   points: 收盘价数组 [{ close: number }]
 *   color:  上涨色（默认红色 A股惯例）
 *   width / height: SVG 尺寸
 */
import { computed } from 'vue'

const props = defineProps({
  points: { type: Array, default: () => [] },
  color: { type: String, default: '#dc2626' },
  width: { type: Number, default: 80 },
  height: { type: Number, default: 32 },
})

const path = computed(() => {
  const data = props.points
  if (!data.length) return ''

  const w = props.width
  const h = props.height
  const pad = 2

  const values = data.map(d => d.close ?? d)
  const min = Math.min(...values)
  const max = Math.max(...values)
  const range = max - min || 1

  const xStep = (w - pad * 2) / Math.max(data.length - 1, 1)

  const points = values.map((v, i) => {
    const x = pad + i * xStep
    const y = h - pad - ((v - min) / range) * (h - pad * 2)
    return `${x.toFixed(1)},${y.toFixed(1)}`
  })

  // 曲线 + 底部填充
  const polyline = points.join(' ')
  const fillPath = `${pad.toFixed(1)},${h - pad} ${polyline} ${(w - pad).toFixed(1)},${h - pad}`

  return { polyline, fillPath }
})

const up = computed(() => {
  if (props.points.length < 2) return true
  const first = props.points[0].close ?? props.points[0]
  const last = props.points[props.points.length - 1].close ?? props.points[props.points.length - 1]
  return last >= first
})
</script>

<template>
  <svg
    v-if="points.length"
    :width="width"
    :height="height"
    viewBox="0 0 {{ width }} {{ height }}"
    class="sparkline"
    :class="{ 'sparkline--up': up, 'sparkline--down': !up }"
    aria-label="走势图"
  >
    <!-- 底部填充区域 -->
    <polygon
      :points="path.fillPath"
      :fill="up ? 'rgba(220,38,38,0.08)' : 'rgba(22,163,74,0.08)'"
    />
    <!-- 走势线 -->
    <polyline
      :points="path.polyline"
      fill="none"
      :stroke="up ? '#dc2626' : '#16a34a'"
      stroke-width="1.5"
      stroke-linecap="round"
      stroke-linejoin="round"
    />
  </svg>
</template>

<style scoped>
.sparkline {
  display: block;
  flex-shrink: 0;
}
</style>
