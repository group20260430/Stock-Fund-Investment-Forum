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

/** 当后端 API 返回 null / 0 时，用内置静态数据兜底 */
const FALLBACK = {
  '000001': { price: 4090.48, change_pct: -0.43, high: 4118.72, low: 4078.66, prev_close: 4108.15, amount: 311200000000 },
  '000300': { price: 4941.60, change_pct: 0.21,  high: 4965.33, low: 4928.47, prev_close: 4931.24, amount: 182500000000 },
  '399001': { price: 16030.70, change_pct: 0.94, high: 16086.25, low: 15964.10, prev_close: 15881.49, amount: 406800000000 },
}

/** 当 K 线数据获取失败时，用模拟走势数据兜底 */
const KL_FALLBACK = {
  '000001': [4101, 4098, 4103, 4107, 4105, 4110, 4112, 4108, 4106, 4103, 4096, 4092, 4095, 4100, 4098, 4094, 4091, 4093, 4090, 4088],
  '000300': [4931, 4933, 4935, 4938, 4936, 4940, 4942, 4939, 4937, 4934, 4932, 4928, 4930, 4933, 4931, 4929, 4927, 4928, 4930, 4931],
  '399001': [15880, 15890, 15900, 15910, 15920, 15935, 15950, 15960, 15955, 15940, 15930, 15950, 15970, 15990, 16010, 16020, 16030, 16025, 16028, 16030],
}

const sign = computed(() => (props.data.change_pct ?? 0) >= 0 ? '+' : '')

const display = computed(() => {
  const fb = FALLBACK[props.data.code]
  return {
    price:
      props.data.price != null
        ? props.data.price.toLocaleString()
        : fb
          ? fb.price.toLocaleString()
          : '--',
    changePct:
      props.data.change_pct != null
        ? props.data.change_pct.toFixed(2)
        : fb
          ? fb.change_pct.toFixed(2)
          : '--',
    high:
      props.data.high != null
        ? props.data.high.toFixed(2)
        : fb?.high != null
          ? fb.high.toFixed(2)
          : '--',
    low:
      props.data.low != null
        ? props.data.low.toFixed(2)
        : fb?.low != null
          ? fb.low.toFixed(2)
          : '--',
    prevClose:
      props.data.prev_close != null
        ? props.data.prev_close.toFixed(2)
        : fb?.prev_close != null
          ? fb.prev_close.toFixed(2)
          : '--',
    amount:
      props.data.amount != null
        ? (props.data.amount / 1e8).toFixed(1) + '亿'
        : fb?.amount != null
          ? (fb.amount / 1e8).toFixed(1) + '亿'
          : '--',
    up:
      props.data.price != null
        ? props.data.up
        : fb
          ? fb.change_pct >= 0
          : true,
  }
})

/** 用于走势图的数据：优先用真实 K 线，降级用兜底模拟数据 */
const chartPoints = computed(() => {
  if (props.kline.length) return props.kline
  const kl = KL_FALLBACK[props.data.code]
  if (!kl) return []
  return kl.map(v => ({ close: v }))
})
</script>

<template>
  <div class="market-card" :class="{ 'market-card--up': display.up, 'market-card--down': !display.up }">
    <div class="market-card__header">
      <span class="market-card__name">{{ data.name }}</span>
      <span class="market-card__code">{{ data.code }}</span>
    </div>

    <div class="market-card__body">
      <div class="market-card__price-col">
        <strong class="market-card__price">{{ display.price }}</strong>
        <span
          class="market-card__change"
          :class="display.up ? 'text-up' : 'text-down'"
        >
          <AppIcon :name="display.up ? 'arrowUp' : 'arrowDown'" :size="10" />
          {{ sign }}{{ display.changePct }}%
        </span>
      </div>

      <div class="market-card__chart-col">
        <!-- 加载骨架 -->
        <div v-if="loading" class="sparkline-skeleton" />
        <MiniSparkline
          v-else-if="chartPoints.length"
          :points="chartPoints"
          :width="80"
          :height="32"
        />
      </div>
    </div>

    <div class="market-card__details">
      <div class="market-card__detail">
        <span>最高</span>
        <strong>{{ display.high }}</strong>
      </div>
      <div class="market-card__detail">
        <span>最低</span>
        <strong>{{ display.low }}</strong>
      </div>
      <div class="market-card__detail">
        <span>昨收</span>
        <strong>{{ display.prevClose }}</strong>
      </div>
      <div class="market-card__detail">
        <span>成交额</span>
        <strong>{{ display.amount }}</strong>
      </div>
    </div>
  </div>
</template>

<style scoped>
.market-card {
  background: var(--color-bg-card);
  border: 1px solid var(--color-border);
  border-radius: var(--radius-xl);
  box-shadow: var(--shadow-card);
  display: grid;
  gap: 12px;
  padding: 18px 20px;
  transition: box-shadow var(--duration-normal) var(--ease-out);
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
  font-weight: var(--font-weight-medium);
}

.market-card__code {
  background: var(--color-bg-hover);
  border-radius: var(--radius-sm);
  color: var(--color-text-muted);
  font-family: "SF Mono", "Consolas", monospace;
  font-size: 11px;
  padding: 2px 7px;
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
  color: var(--color-text-primary);
  font-family: "Inter", "SF Mono", system-ui, sans-serif;
  font-size: 24px;
  font-weight: var(--font-weight-bold);
  letter-spacing: -0.02em;
  line-height: 1.2;
}

.market-card__change {
  align-items: center;
  display: flex;
  font-size: var(--font-size-base);
  font-weight: var(--font-weight-semibold);
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
  gap: 6px;
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
  font-weight: var(--font-weight-semibold);
}

@media (max-width: 780px) {
  .market-card {
    padding: 14px 16px;
  }

  .market-card__price {
    font-size: 20px;
  }

  .market-card__details {
    grid-template-columns: repeat(2, 1fr);
  }
}
</style>
