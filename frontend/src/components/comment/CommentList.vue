<script setup>
import { useAutoAnimate } from '@formkit/auto-animate/vue'
import CommentItem from './CommentItem.vue'

defineProps({
  comments: { type: Array, default: () => [] },
  loading: { type: Boolean, default: false },
})

const emit = defineEmits(['reply', 'like'])

const [listRef] = useAutoAnimate({ duration: 250, easing: 'ease-out' })
</script>

<template>
  <div class="comment-list">
    <div v-if="loading" class="comment-list__loading">加载评论中...</div>

    <div v-else-if="comments.length" ref="listRef">
      <CommentItem
        v-for="comment in comments"
        :key="comment.id"
        :comment="comment"
        @reply="emit('reply', $event)"
        @like="emit('like', $event)"
      />
    </div>

    <p v-else class="comment-list__empty">暂无评论，来发表第一条评论吧</p>
  </div>
</template>

<style scoped>
.comment-list {
  padding: 0;
}

.comment-list__loading,
.comment-list__empty {
  color: var(--color-text-muted);
  font-size: var(--font-size-base);
  padding: 32px 0;
  text-align: center;
}
</style>
