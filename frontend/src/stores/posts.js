import { defineStore } from 'pinia'
import { ref, reactive } from 'vue'
import { fetchPosts as fetchPostsApi, fetchPostDetail, createPost, toggleLike, toggleCollect } from '../api/posts'

export const usePostsStore = defineStore('posts', () => {
  // State
  const list = ref([])
  const currentPost = ref(null)
  const loading = ref(false)
  const error = ref('')
  const pagination = reactive({ page: 1, size: 20, total: 0 })

  // Actions
  async function loadPosts(params = {}) {
    loading.value = true
    error.value = ''
    try {
      const data = await fetchPostsApi({ page: pagination.page, size: pagination.size, ...params })
      list.value = data.items || []
      pagination.total = data.total || 0
    } catch (err) {
      error.value = err.message
      list.value = []
    } finally {
      loading.value = false
    }
  }

  async function loadPostDetail(id) {
    loading.value = true
    error.value = ''
    try {
      currentPost.value = await fetchPostDetail(id)
      return currentPost.value
    } catch (err) {
      error.value = err.message
      currentPost.value = null
      return null
    } finally {
      loading.value = false
    }
  }

  async function publishPost(data) {
    const result = await createPost(data)
    return result
  }

  async function togglePostLike(postId) {
    // 乐观更新
    const post = list.value.find(p => p.id === postId)
    if (post) {
      post.is_liked = !post.is_liked
      post.like_count += post.is_liked ? 1 : -1
    }
    if (currentPost.value && currentPost.value.id === postId) {
      currentPost.value.is_liked = !currentPost.value.is_liked
      currentPost.value.like_count += currentPost.value.is_liked ? 1 : -1
    }

    try {
      const data = await toggleLike(postId)
      // 用服务端数据修正
      if (post) {
        post.is_liked = data.is_liked
        post.like_count = data.like_count
      }
      if (currentPost.value && currentPost.value.id === postId) {
        currentPost.value.is_liked = data.is_liked
        currentPost.value.like_count = data.like_count
      }
    } catch (_err) {
      // 失败回滚
      if (post) {
        post.is_liked = !post.is_liked
        post.like_count += post.is_liked ? 1 : -1
      }
      if (currentPost.value && currentPost.value.id === postId) {
        currentPost.value.is_liked = !currentPost.value.is_liked
        currentPost.value.like_count += currentPost.value.is_liked ? 1 : -1
      }
    }
  }

  async function togglePostCollect(postId, folderName = '默认') {
    const post = list.value.find(p => p.id === postId)
    if (post) {
      post.is_collected = !post.is_collected
      post.collect_count += post.is_collected ? 1 : -1
    }
    if (currentPost.value && currentPost.value.id === postId) {
      currentPost.value.is_collected = !currentPost.value.is_collected
      currentPost.value.collect_count += currentPost.value.is_collected ? 1 : -1
    }

    try {
      const data = await toggleCollect(postId, folderName)
      if (post) {
        post.is_collected = data.is_collected
        post.collect_count = data.collect_count
      }
    } catch (_err) {
      if (post) {
        post.is_collected = !post.is_collected
        post.collect_count += post.is_collected ? 1 : -1
      }
    }
  }

  return {
    list,
    currentPost,
    loading,
    error,
    pagination,
    loadPosts,
    loadPostDetail,
    publishPost,
    togglePostLike,
    togglePostCollect,
  }
})
