<script setup>
import { onMounted, ref } from 'vue'

import { fetchPosts } from '../api/posts'
import PostCard from '../components/PostCard.vue'

const posts = ref([])
const loading = ref(true)
const error = ref('')

onMounted(async () => {
  try {
    posts.value = await fetchPosts()
  } catch (err) {
    error.value = err.message
  } finally {
    loading.value = false
  }
})
</script>

<template>
  <main class="app-shell">
    <aside class="sidebar">
      <div class="brand">
        <strong>股票基金投资论坛</strong>
        <span>Stock & Fund Forum</span>
      </div>
      <nav class="nav-list" aria-label="论坛板块">
        <a class="active" href="#">综合讨论</a>
        <a href="#">股票市场</a>
        <a href="#">基金投资</a>
        <a href="#">问答求助</a>
        <a href="#">投资策略</a>
      </nav>
    </aside>

    <section class="content">
      <header class="toolbar">
        <div>
          <h1>投资社区讨论</h1>
          <p>关注市场观点、基金配置与投资问答。</p>
        </div>
        <button type="button">发布帖子</button>
      </header>

      <section class="market-strip" aria-label="市场概览">
        <div>
          <span>上证指数</span>
          <strong>3,128.42</strong>
          <em>+0.82%</em>
        </div>
        <div>
          <span>沪深300</span>
          <strong>3,568.91</strong>
          <em>+0.43%</em>
        </div>
        <div>
          <span>中证基金</span>
          <strong>7,241.05</strong>
          <em>-0.16%</em>
        </div>
      </section>

      <p v-if="loading" class="state-text">正在加载帖子...</p>
      <p v-else-if="error" class="state-text state-text--error">{{ error }}</p>
      <div v-else class="post-list">
        <PostCard v-for="post in posts" :key="post.id" :post="post" />
      </div>
    </section>
  </main>
</template>
