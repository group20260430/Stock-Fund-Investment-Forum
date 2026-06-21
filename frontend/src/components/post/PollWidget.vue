<script setup>
import { ref, computed } from "vue"
import { useAuthStore } from "../../stores/auth"
import { useToastStore } from "../../stores/toast"
import { voteOnPost } from "../../api/posts"
import { timeAgo } from "../../utils/format"

const props = defineProps({
  postId: { type: [String, Number], required: true },
  poll: { type: Object, required: true },
})

const emit = defineEmits(["voted"])

const auth = useAuthStore()
const toast = useToastStore()

const selectedIds = ref([])
const voting = ref(false)
const localPoll = ref(null)

// 使用本地副本以支持乐观更新
const p = computed(() => localPoll.value || props.poll)

const totalVotes = computed(() => p.value?.total_votes || 0)

const hasVoted = computed(() => {
  const pollData = p.value
  if (!pollData) return false
  if (pollData.user_voted_option_ids && pollData.user_voted_option_ids.length > 0) return true
  if (pollData.user_voted) return true
  return false
})

const isExpired = computed(() => {
  const pollData = p.value
  if (pollData?.is_expired) return true
  if (pollData?.deadline) {
    return new Date(pollData.deadline) < new Date()
  }
  return false
})

const isSingle = computed(() => p.value?.vote_type !== "multiple")

const showResults = computed(() => hasVoted.value || isExpired.value)

const userVotedIds = computed(() => {
  const pollData = p.value
  return pollData?.user_voted_option_ids || []
})

function getPercentage(count) {
  if (!totalVotes.value) return 0
  return Math.round((count / totalVotes.value) * 100)
}

function toggleOption(optionId) {
  if (showResults.value || voting.value) return

  if (isSingle.value) {
    selectedIds.value = [optionId]
    submitVote()
    return
  }

  // 多选
  const idx = selectedIds.value.indexOf(optionId)
  if (idx >= 0) {
    selectedIds.value.splice(idx, 1)
  } else {
    if (selectedIds.value.length >= 5) {
      toast.warning("最多选择5个选项")
      return
    }
    selectedIds.value.push(optionId)
  }
}

async function submitVote() {
  if (!auth.isLoggedIn) {
    toast.info("请先登录再投票")
    return
  }
  if (selectedIds.value.length === 0) {
    toast.warning("请至少选择一个选项")
    return
  }
  voting.value = true
  try {
    await voteOnPost(props.postId, selectedIds.value)
    // 乐观更新
    const options = (p.value.options || []).map(opt => {
      const count = (opt.vote_count || 0)
      return {
        ...opt,
        vote_count: selectedIds.value.includes(opt.id) ? count + 1 : count,
      }
    })
    localPoll.value = {
      ...p.value,
      options,
      total_votes: totalVotes.value + selectedIds.value.length,
      user_voted_option_ids: [...selectedIds.value],
      user_voted: true,
    }
    toast.success("投票成功")
    emit("voted", { optionIds: [...selectedIds.value] })
  } catch (err) {
    toast.error(err.message || "投票失败")
  } finally {
    voting.value = false
    selectedIds.value = []
  }
}

function isSelected(optionId) {
  if (showResults.value) {
    return userVotedIds.value.includes(optionId)
  }
  return selectedIds.value.includes(optionId)
}
</script>

<template>
  <div class="poll-widget">
    <!-- 投票图标 + 标题 -->
    <div class="poll-widget__header">
      <span class="poll-widget__icon">📊</span>
      <span class="poll-widget__label">投票</span>
      <span v-if="isExpired" class="poll-widget__expired">已结束</span>
      <span v-else-if="p.deadline" class="poll-widget__deadline">
        截止 {{ timeAgo(p.deadline) }}
      </span>
    </div>

    <!-- 问题 -->
    <h3 class="poll-widget__question">{{ p.question }}</h3>

    <!-- 选项列表 -->
    <div class="poll-widget__options">
      <div
        v-for="option in p.options"
        :key="option.id"
        :class="[
          'poll-option',
          {
            'poll-option--selected': isSelected(option.id),
            'poll-option--result': showResults,
            'poll-option--clickable': !showResults && !voting,
          }
        ]"
        @click="toggleOption(option.id)"
      >
        <!-- 结果模式：进度条 -->
        <div v-if="showResults" class="poll-option__bar-wrapper">
          <div class="poll-option__info">
            <span class="poll-option__text">{{ option.text || option.label }}</span>
            <span class="poll-option__percent">{{ getPercentage(option.vote_count) }}%</span>
          </div>
          <div class="poll-option__track">
            <div
              :class="['poll-option__fill', { 'poll-option__fill--voted': isSelected(option.id) }]"
              :style="{ width: getPercentage(option.vote_count) + '%' }"
            />
          </div>
          <span class="poll-option__count">{{ option.vote_count || 0 }} 票</span>
        </div>

        <!-- 投票模式 -->
        <div v-else class="poll-option__vote">
          <span :class="['poll-option__radio', { 'poll-option__radio--checked': isSelected(option.id) }]">
            <span v-if="isSelected(option.id)" class="poll-option__dot" />
          </span>
          <span class="poll-option__text">{{ option.text || option.label }}</span>
        </div>
      </div>
    </div>

    <!-- 多选提交按钮 -->
    <div v-if="!isSingle && !showResults && selectedIds.length > 0" class="poll-widget__submit">
      <button
        class="poll-widget__submit-btn"
        :disabled="voting"
        @click="submitVote"
      >{{ voting ? "投票中..." : "提交投票 (" + selectedIds.length + " 项)" }}</button>
    </div>

    <!-- 底部信息 -->
    <div class="poll-widget__footer">
      <span>{{ totalVotes }} 人参与投票</span>
      <span v-if="!isSingle && !showResults" class="poll-widget__hint">可多选</span>
    </div>
  </div>
</template>

<style scoped>
.poll-widget {
  background: var(--color-bg-card);
  border: 1px solid var(--color-border);
  border-radius: var(--radius-xl);
  margin-bottom: 24px;
  padding: 24px;
}

.poll-widget__header {
  align-items: center;
  display: flex;
  gap: 8px;
  margin-bottom: 16px;
}

.poll-widget__icon {
  font-size: 18px;
}

.poll-widget__label {
  color: var(--color-text-secondary);
  font-size: var(--font-size-sm);
  font-weight: var(--font-weight-medium);
}

.poll-widget__expired {
  background: var(--color-danger-light);
  border-radius: var(--radius-sm);
  color: var(--color-danger);
  font-size: var(--font-size-xs);
  font-weight: var(--font-weight-semibold);
  margin-left: auto;
  padding: 2px 8px;
}

.poll-widget__deadline {
  color: var(--color-text-muted);
  font-size: var(--font-size-xs);
  margin-left: auto;
}

.poll-widget__question {
  color: var(--color-text-primary);
  font-size: var(--font-size-lg);
  font-weight: var(--font-weight-semibold);
  line-height: var(--line-height-normal);
  margin: 0 0 20px;
}

.poll-widget__options {
  display: flex;
  flex-direction: column;
  gap: 10px;
}

.poll-option {
  border: 1px solid var(--color-border);
  border-radius: var(--radius-lg);
  padding: 12px 16px;
  transition: border-color var(--duration-fast) var(--ease-out),
              background var(--duration-fast) var(--ease-out);
}

.poll-option--clickable {
  cursor: pointer;
}

.poll-option--clickable:hover {
  border-color: var(--color-primary);
  background: var(--color-primary-light);
}

.poll-option--selected {
  border-color: var(--color-primary);
  background: var(--color-primary-light);
}

.poll-option--result {
  padding: 10px 12px;
}

.poll-option__vote {
  align-items: center;
  display: flex;
  gap: 12px;
}

.poll-option__radio {
  align-items: center;
  border: 2px solid var(--color-border-input);
  border-radius: var(--radius-full);
  display: inline-flex;
  flex-shrink: 0;
  height: 20px;
  justify-content: center;
  transition: border-color var(--duration-fast) var(--ease-out);
  width: 20px;
}

.poll-option__radio--checked {
  border-color: var(--color-primary);
}

.poll-option__dot {
  background: var(--color-primary);
  border-radius: var(--radius-full);
  height: 10px;
  width: 10px;
}

.poll-option__text {
  color: var(--color-text-body);
  font-size: var(--font-size-base);
  line-height: var(--line-height-normal);
}

/* 结果模式 */
.poll-option__bar-wrapper {
  display: flex;
  flex-direction: column;
  gap: 6px;
}

.poll-option__info {
  display: flex;
  justify-content: space-between;
}

.poll-option__percent {
  color: var(--color-text-secondary);
  font-size: var(--font-size-sm);
  font-weight: var(--font-weight-semibold);
}

.poll-option__track {
  background: var(--color-bg-hover);
  border-radius: var(--radius-pill);
  height: 8px;
  overflow: hidden;
}

.poll-option__fill {
  background: var(--color-border-input);
  border-radius: var(--radius-pill);
  height: 100%;
  min-width: 4px;
  transition: width 0.6s var(--ease-out-expo);
}

.poll-option__fill--voted {
  background: var(--color-primary);
}

.poll-option__count {
  color: var(--color-text-muted);
  font-size: var(--font-size-xs);
}

.poll-widget__submit {
  margin-top: 16px;
  text-align: center;
}

.poll-widget__submit-btn {
  background: var(--color-primary);
  border: 0;
  border-radius: var(--radius-lg);
  color: var(--color-bg-card);
  cursor: pointer;
  font: inherit;
  font-size: var(--font-size-base);
  font-weight: var(--font-weight-medium);
  padding: 10px 28px;
  transition: background var(--duration-fast) var(--ease-out);
}

.poll-widget__submit-btn:hover:not(:disabled) {
  background: var(--color-primary-hover);
}

.poll-widget__submit-btn:disabled {
  opacity: 0.6;
  cursor: not-allowed;
}

.poll-widget__footer {
  align-items: center;
  border-top: 1px solid var(--color-border-light);
  color: var(--color-text-muted);
  display: flex;
  font-size: var(--font-size-xs);
  justify-content: space-between;
  margin-top: 16px;
  padding-top: 12px;
}

.poll-widget__hint {
  background: var(--color-primary-light);
  border-radius: var(--radius-sm);
  color: var(--color-primary);
  font-weight: var(--font-weight-medium);
  padding: 2px 8px;
}
</style>
