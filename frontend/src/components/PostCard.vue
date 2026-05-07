<script setup>
defineProps({
  post: {
    type: Object,
    required: true,
  },
})
</script>

<template>
  <article class="post-card">
    <div class="post-card__meta">
      <span>{{ post.category }}</span>
      <span>{{ post.author }}</span>
    </div>
    <h3>{{ post.title }}</h3>
    <p>{{ post.summary }}</p>
    <div class="post-card__stats">
      <span>{{ post.likes }} 点赞</span>
      <span>{{ post.comments }} 评论</span>
    </div>
  </article>
</template>
