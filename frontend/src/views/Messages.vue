<script setup>
import { ref, onMounted, computed } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { useAuthStore } from '../stores/auth'
import { useToastStore } from '../stores/toast'
import { fetchMessages, sendMessage } from '../api/admin'
import { fetchUserProfile } from '../api/users'
import AppLayout from '../components/layout/AppLayout.vue'
import Loading from '../components/common/Loading.vue'
import EmptyState from '../components/common/EmptyState.vue'

const route = useRoute()
const router = useRouter()
const auth = useAuthStore()
const toast = useToastStore()

const conversations = ref([])
const activeChat = ref(null)
const messages = ref([])
const messageText = ref('')
const loading = ref(true)
const sending = ref(false)
const chatUser = ref(null)

onMounted(async () => {
  try {
    const data = await fetchMessages()
    conversations.value = Array.isArray(data) ? data : data?.items || []
    // 如果路由有 userId 参数，自动打开该对话
    if (route.params.userId) {
      openChat(Number(route.params.userId))
    }
  } catch (err) {
    console.error('加载私信失败:', err.message)
  } finally {
    loading.value = false
  }
})

async function openChat(userId) {
  // 获取对方用户信息
  try {
    chatUser.value = await fetchUserProfile(userId)
  } catch {
    // 如果获取不到，用ID代替
  }
  activeChat.value = userId
  messages.value = []
  // 模拟：从对话中提取已有消息
  const conv = conversations.value.find(c =>
    c.participants?.includes(userId) || c.user_id === userId || c.other_user?.id === userId
  )
  if (conv?.messages) {
    messages.value = conv.messages
  }
}

async function handleSend() {
  if (!messageText.value.trim() || !activeChat.value || sending.value) return
  sending.value = true
  try {
    await sendMessage({
      receiver_id: activeChat.value,
      content: messageText.value.trim(),
    })
    messages.value.push({
      id: Date.now(),
      sender_id: auth.user?.id,
      content: messageText.value.trim(),
      created_at: new Date().toISOString(),
    })
    messageText.value = ''
    toast.success('已发送')
  } catch (err) {
    toast.error(err.message || '发送失败')
  } finally {
    sending.value = false
  }
}

function formatTime(t) {
  if (!t) return ''
  return new Date(t).toLocaleString('zh-CN', { month: '2-digit', day: '2-digit', hour: '2-digit', minute: '2-digit' })
}
</script>

<template>
  <AppLayout>
    <div class="messages-layout">
      <!-- 会话列表 -->
      <aside class="conv-list">
        <header class="conv-list__header">
          <h2>私信</h2>
        </header>
        <Loading v-if="loading" variant="skeleton" :rows="5" />
        <EmptyState v-else-if="conversations.length === 0" icon="✉️" title="暂无私信" description="去群组或用户页面开始交流" />
        <div v-else class="conv-items">
          <div
            v-for="conv in conversations"
            :key="conv.id || conv.other_user?.id"
            :class="['conv-item', { 'conv-item--active': activeChat === (conv.other_user?.id || conv.user_id) }]"
            @click="openChat(conv.other_user?.id || conv.user_id)"
          >
            <img :src="conv.other_user?.avatar_url || ''" class="conv-avatar" @error="$event.target.style.display='none'" />
            <div class="conv-info">
              <strong class="conv-name">{{ conv.other_user?.nickname || conv.other_user?.username || '用户' }}</strong>
              <span class="conv-preview">{{ conv.last_message || conv.content || '' }}</span>
            </div>
          </div>
        </div>
      </aside>

      <!-- 聊天区域 -->
      <main class="chat-area">
        <template v-if="activeChat">
          <div class="chat-header">
            <img :src="chatUser?.avatar_url || ''" class="chat-avatar" @error="$event.target.style.display='none'" />
            <strong>{{ chatUser?.nickname || chatUser?.username || '用户' }}</strong>
          </div>
          <div class="chat-messages">
            <div
              v-for="msg in messages"
              :key="msg.id"
              :class="['msg', { 'msg--own': msg.sender_id === auth.user?.id }]"
            >
              <div class="msg-bubble">{{ msg.content }}</div>
              <span class="msg-time">{{ formatTime(msg.created_at) }}</span>
            </div>
            <EmptyState v-if="messages.length === 0" icon="💬" title="开始对话" description="发送第一条消息" />
          </div>
          <div class="chat-input">
            <input
              v-model="messageText"
              class="chat-input__field"
              placeholder="输入消息..."
              maxlength="5000"
              @keyup.enter="handleSend"
            />
            <button class="chat-input__send" :disabled="!messageText.trim() || sending" @click="handleSend">
              {{ sending ? '...' : '发送' }}
            </button>
          </div>
        </template>
        <div v-else class="chat-empty">
          <EmptyState icon="✉️" title="选择一个对话" description="从左侧选择私信开始交流" />
        </div>
      </main>
    </div>
  </AppLayout>
</template>

<style scoped>
.messages-layout { display: flex; gap: 0; height: calc(100vh - 120px); background: var(--color-bg-card); border: 1px solid var(--color-border); border-radius: 10px; overflow: hidden; }
.conv-list { width: 300px; border-right: 1px solid var(--color-border); display: flex; flex-direction: column; flex-shrink: 0; }
.conv-list__header { padding: 16px 20px; border-bottom: 1px solid var(--color-border); }
.conv-list__header h2 { margin: 0; font-size: 18px; }
.conv-items { flex: 1; overflow-y: auto; }
.conv-item { align-items: center; cursor: pointer; display: flex; gap: 12px; padding: 14px 20px; transition: background 0.15s; }
.conv-item:hover { background: var(--color-bg-hover); }
.conv-item--active { background: var(--color-primary-light); }
.conv-avatar { border-radius: 50%; height: 40px; width: 40px; object-fit: cover; flex-shrink: 0; }
.conv-info { flex: 1; min-width: 0; }
.conv-name { display: block; font-size: 14px; overflow: hidden; text-overflow: ellipsis; white-space: nowrap; }
.conv-preview { color: var(--color-text-muted); display: block; font-size: 12px; overflow: hidden; text-overflow: ellipsis; white-space: nowrap; margin-top: 2px; }
.chat-area { flex: 1; display: flex; flex-direction: column; }
.chat-header { align-items: center; border-bottom: 1px solid var(--color-border); display: flex; gap: 10px; padding: 14px 20px; }
.chat-avatar { border-radius: 50%; height: 32px; width: 32px; object-fit: cover; }
.chat-messages { flex: 1; overflow-y: auto; padding: 20px; display: flex; flex-direction: column; gap: 12px; }
.msg { display: flex; flex-direction: column; max-width: 70%; }
.msg--own { align-self: flex-end; align-items: flex-end; }
.msg-bubble { background: var(--color-bg-hover); border-radius: 12px 12px 12px 4px; font-size: 14px; padding: 10px 14px; word-break: break-word; line-height: 1.5; }
.msg--own .msg-bubble { background: var(--color-primary); color: #fff; border-radius: 12px 12px 4px 12px; }
.msg-time { color: var(--color-text-muted); font-size: 11px; margin-top: 4px; }
.chat-input { border-top: 1px solid var(--color-border); display: flex; gap: 8px; padding: 12px 16px; }
.chat-input__field { border: 1px solid var(--color-border-input); border-radius: 8px; flex: 1; font: inherit; font-size: 14px; padding: 10px 14px; }
.chat-input__field:focus { border-color: var(--color-primary); outline: none; }
.chat-input__send { background: var(--color-primary); border: 0; border-radius: 8px; color: #fff; cursor: pointer; font: inherit; font-size: 14px; padding: 10px 20px; white-space: nowrap; }
.chat-input__send:disabled { opacity: 0.5; }
.chat-empty { flex: 1; display: flex; align-items: center; justify-content: center; }
</style>
