<script setup>
/**
 * MarketCard — 单个指数行情卡片
 *
 * Props:
 *   data: { name, code, price, change, change_pct, up, high, low, open, prev_close }
 */
import { computed } from 'vue'
import MiniSparkline from './MiniSparkline.vue'
import AppIcon from './AppIcon.vue'

const props = defineProps({
  data: { type: Object, required: true },
  kline: { type: Array, default: () => [] },
  loading: { type: Boolean, default: false },
})

const sign = computed(() => props.data.change_pct >= 0 ? '+' : '')
</script>

<template>
  <div class="market-card" :class="{ 'market-card--up': data.up, 'market-card--down': !data.up }">
    <div class="market-card__header">
      <span class="market-card__name">{{ data.name }}</span>
      <span class="market-card__code">{{ data.code }}</span>
    </div>

    <div class="market-card__body">
      <div class="market-card__price-col">
        <strong class="market-card__price">
          {{ data.price != null ? data.price.toLocaleString() : '--' }}
        </strong>
        <span
          class="market-card__change"
          :class="data.up ? 'text-up' : 'text-down'"
        >
          <AppIcon :name="data.up ? 'arrowUp' : 'arrowDown'" :size="10" />
          {{ sign }}{{ data.change_pct != null ? data.change_pct.toFixed(2) : '--' }}%
        </span>
      </div>

      <div class="market-card__chart-col">
        <!-- 加载骨架 -->
        <div v-if="loading" class="sparkline-skeleton" />
        <MiniSparkline
          v-else-if="kline.length"
          :points="kline"
          :width="80"
          :height="32"
        />
      </div>
    </div>

    <div class="market-card__details">
      <div class="market-card__detail">
        <span>最高</span>
        <strong>{{ data.high != null ? data.high.toFixed(2) : '--' }}</strong>
      </div>
      <div class="market-card__detail">
        <span>最低</span>
        <strong>{{ data.low != null ? data.low.toFixed(2) : '--' }}</strong>
      </div>
      <div class="market-card__detail">
        <span>昨收</span>
        <strong>{{ data.prev_close != null ? data.prev_close.toFixed(2) : '--' }}</strong>
      </div>
      <div class="market-card__detail">
        <span>成交额</span>
        <strong>{{ data.amount != null ? (data.amount / 1e8).toFixed(1) + '亿' : '--' }}</strong>
      </div>
    </div>
  </div>
</template>

<style scoped>
.market-card {
  background: var(--color-bg-card);
  border: 1px solid var(--color-border);
  border-radius: var(--radius-lg);
  box-shadow: var(--shadow-card);
  display: grid;
  gap: 12px;
  padding: 16px;
  transition: box-shadow var(--duration-normal) var(--ease-out-expo);
}

.market-card:hover {
  box-shadow: var(--shadow-card-hover);
}

.market-card--up {
  background: linear-gradient(135deg, #fff 0%, #fef2f2 100%);
}

.market-card--down {
  background: linear-gradient(135deg, #fff 0%, #f0fdf4 100%);
}

.market-card__header {
  align-items: center;
  display: flex;
  gap: 8px;
}

.market-card__name {
  color: var(--color-text-secondary);
  font-size: var(--font-size-sm);
}

.market-card__code {
  background: var(--color-bg-hover);
  border-radius: var(--radius-sm);
  color: var(--color-text-muted);
  font-size: var(--font-size-xs);
  padding: 1px 6px;
}

.market-card__body {
  align-items: center;
  display: flex;
  justify-content: space-between;
}

.market-card__price-col {
  display: grid;
  gap: 4px;
}

.market-card__price {
  font-size: 22px;
  color: var(--color-text-primary);
}

.market-card__change {
  align-items: center;
  display: flex;
  font-size: var(--font-size-base);
  font-weight: var(--font-weight-medium);
  gap: 4px;
}

.text-up { color: var(--color-danger); }
.text-down { color: var(--color-success); }

.market-card__chart-col {
  flex-shrink: 0;
}

.sparkline-skeleton {
  animation: pulse 1.6s ease-in-out infinite;
  background: var(--color-border);
  border-radius: var(--radius-sm);
  height: 32px;
  width: 80px;
}

@keyframes pulse {
  0%, 100% { opacity: 1; }
  50% { opacity: 0.4; }
}

.market-card__details {
  border-top: 1px solid var(--color-border-light);
  display: grid;
  gap: 4px;
  grid-template-columns: repeat(4, 1fr);
  padding-top: 12px;
}

.market-card__detail {
  display: grid;
  gap: 2px;
}

.market-card__detail span {
  color: var(--color-text-muted);
  font-size: var(--font-size-xs);
}

.market-card__detail strong {
  color: var(--color-text-body);
  font-size: var(--font-size-sm);
}
</style>
