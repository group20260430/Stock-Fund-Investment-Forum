<script setup>
import { ref, onMounted } from "vue"
import { useRoute } from "vue-router"
import AppLayout from "../components/layout/AppLayout.vue"
import PostCard from "../components/post/PostCard.vue"
import Loading from "../components/common/Loading.vue"
import EmptyState from "../components/common/EmptyState.vue"
import Pagination from "../components/common/Pagination.vue"
import { usePostsStore } from "../stores/posts"
import { useToastStore } from "../stores/toast"
import { fetchGroups, joinGroup, createGroupPost } from "../api/groups"
import { fetchPosts } from "../api/posts"

const route = useRoute()
const postsStore = usePostsStore()
const toast = useToastStore()

const group = ref(null)
const loading = ref(true)
const joining = ref(false)

const posts = ref([])
const postsLoading = ref(false)
const postsPage = ref(1)
const postsTotal = ref(0)

// 发帖
const showEditor = ref(false)
const postTitle = ref("")
const postContent = ref("")
const posting = ref(false)

onMounted(async () => {
  loading.value = true
  try {
    const data = await fetchGroups({ type: "my" })
    const list = Array.isArray(data) ? data : (data?.items || [])
    group.value = list.find(g => String(g.id) === String(route.params.id))
    if (group.value) await loadPosts()
  } catch (err) {
    console.error("加载群组详情失败:", err.message)
  } finally {
    loading.value = false
  }
})

async function loadPosts(p = 1) {
  postsLoading.value = true
  try {
    const data = await fetchPosts({ group_id: route.params.id, page: p, size: 20 })
    posts.value = data.items || []
    postsTotal.value = data.total || 0
    postsPage.value = p
  } catch (err) {
    console.error("加载群组帖子失败:", err.message)
  } finally {
    postsLoading.value = false
  }
}

async function handleJoin() {
  joining.value = true
  try {
    await joinGroup(route.params.id)
    if (group.value) group.value.is_member = true
    toast.success("已加入群组")
  } catch (err) {
    toast.error(err.message || "加入失败")
  } finally {
    joining.value = false
  }
}

async function handleCreatePost() {
  if (!postTitle.value.trim() || !postContent.value.trim() || posting.value) return
  posting.value = true
  try {
    await createGroupPost(route.params.id, {
      title: postTitle.value.trim(),
      content: postContent.value.trim(),
    })
    toast.success("发布成功")
    postTitle.value = ""
    postContent.value = ""
    showEditor.value = false
    await loadPosts(1)
  } catch (err) {
    toast.error(err.message || "发布失败")
  } finally {
    posting.value = false
  }
}

function handleLike(postId) { postsStore.togglePostLike(postId) }
function handlePostsPageChange(p) { loadPosts(p); window.scrollTo({ top: 400, behavior: "smooth" }) }
</script>

<template>
  <AppLayout>
    <Loading v-if="loading" variant="skeleton" :rows="1" />

    <template v-else-if="group">
      <header class="group-header">
        <div class="group-header__info">
          <h1>{{ group.name }}</h1>
          <p>{{ group.description }}</p>
          <div class="group-header__meta">
            <span>👥 {{ group.member_count || 0 }} 成员</span>
            <span :class="['group-header__visibility', { 'group-header__visibility--private': group.visibility === 'private' }]">
              {{ group.visibility === "public" ? "公开" : "私密" }}
            </span>
          </div>
        </div>
        <button
          v-if="!group.is_member"
          class="join-btn"
          :disabled="joining"
          @click="handleJoin"
        >{{ joining ? "加入中..." : "+ 加入群组" }}</button>
      </header>

      <!-- 发帖区 -->
      <div v-if="group.is_member" class="group-post-form">
        <template v-if="showEditor">
          <input
            v-model="postTitle"
            type="text"
            placeholder="帖子标题..."
            class="group-post-form__title"
            maxlength="120"
          >
          <textarea
            v-model="postContent"
            placeholder="分享你的投资观点..."
            class="group-post-form__content"
            rows="4"
            maxlength="5000"
          />
          <div class="group-post-form__actions">
            <button class="group-post-form__cancel" @click="showEditor = false; postTitle = ''; postContent = ''">取消</button>
            <button
              class="group-post-form__submit"
              :disabled="!postTitle.trim() || !postContent.trim() || posting"
              @click="handleCreatePost"
            >{{ posting ? "发布中..." : "发布" }}</button>
          </div>
        </template>
        <button v-else class="group-post-form__trigger" @click="showEditor = true">
          ✏️ 在群组中发帖...
        </button>
      </div>

      <!-- 群组帖子列表 -->
      <div class="group-posts">
        <h3 class="group-posts__title">群组讨论 ({{ postsTotal }})</h3>

        <Loading v-if="postsLoading" variant="skeleton" :rows="2" />

        <EmptyState
          v-else-if="!posts.length"
          icon="💬"
          title="暂无讨论"
          :description="group.is_member ? '来发表第一条帖子吧' : '加入群组后可参与讨论'"
        />

        <div v-else class="post-list">
          <PostCard
            v-for="post in posts"
            :key="post.id"
            :post="post"
            @like="handleLike"
          />
        </div>

        <Pagination
          v-if="postsTotal > 20"
          :current="postsPage"
          :total="postsTotal"
          :size="20"
          @update:current="handlePostsPageChange"
        />
      </div>
    </template>

    <EmptyState v-else icon="🔍" title="群组不存在" />
  </AppLayout>
</template>

<style scoped>
.group-header {
  align-items: flex-start;
  background: var(--color-bg-card);
  border: 1px solid var(--color-border);
  border-radius: var(--radius-xl);
  display: flex;
  gap: 20px;
  justify-content: space-between;
  margin-bottom: 24px;
  padding: 24px;
}

.group-header__info h1 { font-size: var(--font-size-2xl); margin: 0 0 8px; }
.group-header__info p { color: var(--color-text-secondary); font-size: var(--font-size-base); margin: 0 0 12px; line-height: var(--line-height-normal); }

.group-header__meta {
  color: var(--color-text-muted);
  display: flex;
  font-size: var(--font-size-sm);
  gap: 16px;
}

.group-header__visibility {
  background: var(--color-primary-light);
  border-radius: var(--radius-pill);
  color: var(--color-primary);
  font-weight: var(--font-weight-medium);
  padding: 2px 10px;
}

.group-header__visibility--private {
  background: var(--color-warning-light);
  color: var(--color-warning);
}

.join-btn {
  background: var(--color-primary);
  border: 0;
  border-radius: var(--radius-lg);
  color: var(--color-bg-card);
  cursor: pointer;
  flex-shrink: 0;
  font: inherit;
  font-size: var(--font-size-base);
  font-weight: var(--font-weight-medium);
  padding: 10px 24px;
  transition: background var(--duration-fast) var(--ease-out);
}

.join-btn:hover:not(:disabled) { background: var(--color-primary-hover); }
.join-btn:disabled { opacity: 0.6; cursor: not-allowed; }

/* 发帖表单 */
.group-post-form {
  background: var(--color-bg-card);
  border: 1px solid var(--color-border);
  border-radius: var(--radius-xl);
  margin-bottom: 24px;
  padding: 20px;
}

.group-post-form__trigger {
  background: var(--color-bg-hover);
  border: 1px dashed var(--color-border-input);
  border-radius: var(--radius-lg);
  color: var(--color-text-muted);
  cursor: pointer;
  font: inherit;
  font-size: var(--font-size-base);
  padding: 14px 18px;
  text-align: left;
  transition: border-color var(--duration-fast) var(--ease-out), color var(--duration-fast) var(--ease-out);
  width: 100%;
}

.group-post-form__trigger:hover { border-color: var(--color-primary); color: var(--color-primary); }

.group-post-form__title {
  border: 1px solid var(--color-border-input);
  border-radius: var(--radius-lg);
  font: inherit;
  font-size: var(--font-size-lg);
  font-weight: var(--font-weight-semibold);
  margin-bottom: 12px;
  padding: 12px 14px;
  width: 100%;
}

.group-post-form__title:focus {
  border-color: var(--color-primary);
  box-shadow: 0 0 0 3px var(--color-primary-ring);
  outline: none;
}

.group-post-form__content {
  border: 1px solid var(--color-border-input);
  border-radius: var(--radius-lg);
  font: inherit;
  font-size: var(--font-size-base);
  margin-bottom: 12px;
  padding: 12px 14px;
  resize: vertical;
  width: 100%;
}

.group-post-form__content:focus {
  border-color: var(--color-primary);
  box-shadow: 0 0 0 3px var(--color-primary-ring);
  outline: none;
}

.group-post-form__actions {
  display: flex;
  gap: 8px;
  justify-content: flex-end;
}

.group-post-form__cancel {
  background: var(--color-bg-card);
  border: 1px solid var(--color-border-input);
  border-radius: var(--radius-lg);
  color: var(--color-text-secondary);
  cursor: pointer;
  font: inherit;
  font-size: var(--font-size-sm);
  padding: 8px 20px;
}

.group-post-form__cancel:hover { background: var(--color-bg-hover); }

.group-post-form__submit {
  background: var(--color-primary);
  border: 0;
  border-radius: var(--radius-lg);
  color: var(--color-bg-card);
  cursor: pointer;
  font: inherit;
  font-size: var(--font-size-sm);
  font-weight: var(--font-weight-medium);
  padding: 8px 24px;
}

.group-post-form__submit:hover:not(:disabled) { background: var(--color-primary-hover); }
.group-post-form__submit:disabled { opacity: 0.5; cursor: not-allowed; }

/* 帖子列表 */
.group-posts__title {
  font-size: var(--font-size-lg);
  margin: 0 0 16px;
}

.post-list { display: grid; gap: 14px; }

@media (max-width: 780px) {
  .group-header { flex-direction: column; }
  .join-btn { width: 100%; }
}
</style>
