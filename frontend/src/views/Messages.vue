<script setup>
import { ref, onMounted, onUnmounted, nextTick, watch } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { useAuthStore } from '../stores/auth'
import { useToastStore } from '../stores/toast'
import { fetchMessages, sendMessage, deleteMessage } from '../api/messages'
import { search as searchUsers } from '../api/search'
import { fetchUserProfile } from '../api/users'
import { markNotificationsRead } from '../api/notifications'
import AppIcon from '../components/common/AppIcon.vue'
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
const chatLoading = ref(false)
const sending = ref(false)
const deleting = ref(null) // 正在删除的消息 ID
const messageAnimateIds = new Set() // 需要播放入场动画的消息 ID
const chatUser = ref(null)
const chatContainer = ref(null)

// 新对话弹窗
const showNewConv = ref(false)
const searchKeyword = ref('')
const searchResults = ref([])
const searchingUsers = ref(false)
let searchTimer = null

// 消息轮询
let pollingTimer = null
const POLL_INTERVAL = 8000 // 8 秒轮询

// 附件上传
const attachmentInput = ref(null)
const uploadingFile = ref(false)
const API_BASE = import.meta.env.VITE_API_BASE_URL || 'http://localhost:8000/api'

onMounted(async () => {
  await loadConversations()
  startPolling()
  // 将未读私信通知标记为已读
  markAllMessageNotificationsRead()
})

/** 将所有 NEW_MESSAGE 类型未读通知标记为已读 */
async function markAllMessageNotificationsRead() {
  try {
    await markNotificationsRead() // 不传 ids 则标记全部已读
  } catch { /* ignore */ }
}

onUnmounted(() => {
  stopPolling()
})

// 页面可见性变化：可见时恢复轮询，隐藏时暂停
document.addEventListener('visibilitychange', () => {
  if (document.hidden) {
    stopPolling()
  } else {
    startPolling()
  }
})

function startPolling() {
  stopPolling()
  pollingTimer = setInterval(pollNewMessages, POLL_INTERVAL)
}

function stopPolling() {
  if (pollingTimer) {
    clearInterval(pollingTimer)
    pollingTimer = null
  }
}

async function pollNewMessages() {
  try {
    // 静默刷新对话列表
    const data = await fetchMessages()
    const newConversations = data?.items || (Array.isArray(data) ? data : [])
    conversations.value = newConversations

    // 如果正在聊天中，刷新当前对话消息
    if (activeChat.value) {
      const chatData = await fetchMessages({ other_user_id: activeChat.value })
      const items = chatData?.items || (Array.isArray(chatData) ? chatData : [])
      const newItems = items.slice().reverse()
      const prevLen = messages.value.length
      // 给新收到的消息标记动画
      if (newItems.length > prevLen) {
        const existingIds = new Set(messages.value.map(m => m.id))
        newItems.forEach(m => {
          if (!existingIds.has(m.id) && m.sender_id !== auth.user?.id) {
            messageAnimateIds.add(m.id)
          }
        })
      }
      messages.value = newItems
      if (messages.value.length > prevLen) {
        scrollToBottom()
      }
      // 刷新对话列表以更新未读数
      conversations.value = newConversations
      window.dispatchEvent(new CustomEvent('messages-read'))
    }
  } catch { /* 静默失败 */ }
}

async function loadConversations() {
  loading.value = true
  try {
    // GET /messages (无 other_user_id) → 按对话聚合的最近消息
    const data = await fetchMessages()
    conversations.value = data?.items || (Array.isArray(data) ? data : [])
  } catch (err) {
    console.error('加载私信列表失败:', err.message)
  } finally {
    loading.value = false
  }
}

async function openChat(userId) {
  activeChat.value = userId
  chatLoading.value = true
  messages.value = []

  // 若 userId 无效则忽略
  if (!userId || isNaN(Number(userId))) return

  // 获取对方用户信息
  try {
    chatUser.value = await fetchUserProfile(userId)
  } catch {
    chatUser.value = { id: userId, nickname: `用户${userId}` }
  }

  // 获取该对话的历史消息：GET /messages?other_user_id=<userId>
  try {
    const data = await fetchMessages({ other_user_id: userId })
    const items = data?.items || (Array.isArray(data) ? data : [])
    // 按时间升序排列（后端返回 desc，需要反转）
    messages.value = items.slice().reverse()
  } catch (err) {
    console.error('加载对话消息失败:', err.message)
  } finally {
    chatLoading.value = false
    scrollToBottom()
  }
  markAllMessageNotificationsRead()
  // 通知 NavBar 消息已读
  window.dispatchEvent(new CustomEvent('messages-read'))
}

function scrollToBottom() {
  nextTick(() => {
    const el = chatContainer.value
    if (el) el.scrollTop = el.scrollHeight
  })
}

async function handleSend() {
  if (!messageText.value.trim() || !activeChat.value || sending.value) return
  sending.value = true
  const text = messageText.value.trim()
  messageText.value = ''

  // 立即插入临时"发送中"消息（乐观更新）
  const tempId = 'temp_' + Date.now()
  const tempMsg = {
    id: tempId,
    sender_id: auth.user?.id,
    receiver_id: activeChat.value,
    content: text,
    message_type: 'text',
    is_read: true,
    created_at: new Date().toISOString(),
    pending: true,
  }
  messages.value.push(tempMsg)
  messageAnimateIds.add(tempId)
  scrollToBottom()

  try {
    await sendMessage({
      receiver_id: activeChat.value,
      content: text,
    })
    // 移除临时消息，用服务端真实数据替换
    messages.value = messages.value.filter(m => m.id !== tempId)
    await loadConversationMessages(activeChat.value)
    await loadConversations()
  } catch (err) {
    // 标记临时消息为失败
    const idx = messages.value.findIndex(m => m.id === tempId)
    if (idx >= 0) {
      messages.value[idx] = { ...messages.value[idx], failed: true, pending: false }
    }
    toast.error(err.message || '发送失败')
  } finally {
    sending.value = false
  }
}

async function retrySend(failedMsg) {
  if (sending.value) return
  messages.value = messages.value.filter(m => m.id !== failedMsg.id)
  sending.value = true
  const tempId = 'temp_' + Date.now()
  const tempMsg = {
    id: tempId,
    sender_id: auth.user?.id,
    receiver_id: activeChat.value,
    content: failedMsg.content,
    message_type: 'text',
    is_read: true,
    created_at: new Date().toISOString(),
    pending: true,
  }
  messages.value.push(tempMsg)
  messageAnimateIds.add(tempId)
  scrollToBottom()
  try {
    await sendMessage({
      receiver_id: activeChat.value,
      content: failedMsg.content,
    })
    messages.value = messages.value.filter(m => m.id !== tempId)
    await loadConversationMessages(activeChat.value)
    await loadConversations()
  } catch (err) {
    const idx = messages.value.findIndex(m => m.id === tempId)
    if (idx >= 0) {
      messages.value[idx] = { ...messages.value[idx], failed: true, pending: false }
    }
    toast.error(err.message || '发送失败')
  } finally {
    sending.value = false
  }
}

async function handleDelete(messageId) {
  if (!messageId || deleting.value) return
  deleting.value = messageId
  try {
    await deleteMessage(messageId)
    messages.value = messages.value.filter(m => m.id !== messageId)
    toast.success('消息已删除')
  } catch (err) {
    toast.error(err.message || '删除失败')
  } finally {
    deleting.value = null
  }
}

async function loadConversationMessages(userId) {
  try {
    const data = await fetchMessages({ other_user_id: userId })
    const items = data?.items || (Array.isArray(data) ? data : [])
    messages.value = items.slice().reverse()
    scrollToBottom()
  } catch { /* ignore */ }
}

function showNewConversation() {
  showNewConv.value = true
  searchKeyword.value = ''
  searchResults.value = []
}

function closeNewConversation() {
  showNewConv.value = false
  searchKeyword.value = ''
  searchResults.value = []
}

async function handleSearchUsers() {
  const kw = searchKeyword.value.trim()
  if (!kw || kw.length < 1) {
    searchResults.value = []
    return
  }
  searchingUsers.value = true
  try {
    const data = await searchUsers({ keyword: kw, type: 'user', size: 20 })
    searchResults.value = (data?.items || []).filter(u => u.id !== auth.user?.id)
  } catch (err) {
    console.error('搜索用户失败:', err.message)
  } finally {
    searchingUsers.value = false
  }
}

function onSearchInput() {
  clearTimeout(searchTimer)
  searchTimer = setTimeout(handleSearchUsers, 300)
}

function startNewChat(userId) {
  closeNewConversation()
  openChat(userId)
  loadConversations()
}

function formatTime(t) {
  if (!t) return ''
  return new Date(t).toLocaleString('zh-CN', { month: '2-digit', day: '2-digit', hour: '2-digit', minute: '2-digit' })
}

// ===== 附件功能 =====

function triggerAttachment() {
  attachmentInput.value?.click()
}

async function handleAttachmentSelected(e) {
  const files = e.target.files
  if (!files || !files.length) return
  const file = files[0]
  if (file.size > 10 * 1024 * 1024) {
    toast.warning('文件大小超过 10MB 限制')
    e.target.value = ''
    return
  }

  uploadingFile.value = true
  try {
    // 上传文件
    const formData = new FormData()
    formData.append('file', file)
    const token = localStorage.getItem('token')
    const response = await fetch(`${API_BASE}/uploads`, {
      method: 'POST',
      headers: token ? { Authorization: `Bearer ${token}` } : {},
      body: formData,
    })
    if (!response.ok) {
      const err = await response.json().catch(() => ({}))
      throw new Error(err.message || `上传失败 (${response.status})`)
    }
    const result = await response.json()
    const attachmentUrl = result.data.file_url

    // 判断消息类型
    const isImage = file.type.startsWith('image/')
    const msgType = isImage ? 'image' : 'file'

    // 发送带附件的消息
    await sendMessage({
      receiver_id: activeChat.value,
      content: isImage ? '[图片]' : `[文件] ${file.name}`,
      message_type: msgType,
      attachment_url: attachmentUrl,
    })
    await loadConversationMessages(activeChat.value)
    await loadConversations()
    toast.success(isImage ? '图片已发送' : '文件已发送')
  } catch (err) {
    toast.error(err.message || '上传失败')
  } finally {
    uploadingFile.value = false
    e.target.value = ''
  }
}

function isImageMessage(msg) {
  return msg.message_type === 'image'
}

function isFileMessage(msg) {
  return msg.message_type === 'file'
}

function getFileName(msg) {
  if (!msg.attachment_url) return '未知文件'
  const parts = msg.attachment_url.split('/')
  return parts[parts.length - 1] || '未知文件'
}

// 监听路由参数变化（从用户资料页点击"私信"按钮）
watch(() => route.params.userId, (val) => {
  if (val && Number(val)) {
    openChat(Number(val))
  }
})
</script>

<template>
    <div class="messages-layout">
      <!-- 会话列表 -->
      <aside class="conv-list">
        <header class="conv-list__header">
          <h2>私信</h2>
          <button class="new-conv-btn" title="新建私信" @click="showNewConversation">+</button>
        </header>
        <Loading v-if="loading" variant="skeleton" :rows="5" />
        <EmptyState v-else-if="conversations.length === 0" icon="✉️" title="暂无私信" description="去群组或用户页面开始交流" action-label="发起私信" @action="showNewConversation" />
        <div v-else class="conv-items">
          <div
            v-for="conv in conversations"
            :key="conv.id || conv.other_user?.id"
            :class="['conv-item', { 'conv-item--active': activeChat === (conv.other_user?.id || conv.user_id) }]"
            @click="openChat(conv.other_user?.id || conv.user_id)"
          >
            <img :src="conv.other_user?.avatar_url || ''" class="conv-avatar" @error="$event.target.style.display='none'" />
            <div class="conv-info">
              <div class="conv-name-row">
                <strong class="conv-name" :class="{ 'conv-name--unread': !conv.is_read && activeChat !== (conv.other_user?.id || conv.user_id) }">{{ conv.other_user?.nickname || conv.other_user?.username || '用户' }}</strong>
                <span
                  v-if="(conv.unread_count || 0) > 0 && activeChat !== (conv.other_user?.id || conv.user_id)"
                  class="conv-unread-badge"
                >{{ (conv.unread_count || 0) > 99 ? '99+' : (conv.unread_count || 0) }}</span>
              </div>
              <span class="conv-preview" :class="{ 'conv-preview--unread': !conv.is_read && activeChat !== (conv.other_user?.id || conv.user_id) }">{{ conv.last_message || conv.content || '' }}</span>
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
          <div class="chat-messages" ref="chatContainer">
            <Loading v-if="chatLoading" variant="skeleton" :rows="3" />
            <template v-else>
              <TransitionGroup name="msg-slide">
                <div
                  v-for="msg in messages"
                  :key="msg.id"
                  :class="['msg', {
                    'msg--own': msg.sender_id === auth.user?.id,
                    'msg--pending': msg.pending,
                    'msg--failed': msg.failed,
                  }]"
                >
                <div class="msg-bubble">
                  <!-- 发送中三点动画 -->
                  <span v-if="msg.pending" class="msg-sending-indicator">
                    <span class="msg-sending-dot" />
                    <span class="msg-sending-dot" />
                    <span class="msg-sending-dot" />
                  </span>
                  <!-- 图片附件 -->
                  <img
                    v-if="isImageMessage(msg)"
                    :src="msg.attachment_url"
                    class="msg-image"
                    loading="lazy"
                    @error="$event.target.style.display='none'"
                  />
                  <!-- 文件附件 -->
                  <a
                    v-else-if="isFileMessage(msg)"
                    :href="msg.attachment_url"
                    class="msg-file"
                    target="_blank"
                    rel="noopener"
                    :download="getFileName(msg)"
                  >
                    <span class="msg-file__icon">📎</span>
                    <span class="msg-file__name">{{ getFileName(msg) }}</span>
                  </a>
                  <!-- 文字内容 -->
                  <span v-else>{{ msg.content }}</span>
                </div>
                <div class="msg-meta">
                  <span v-if="msg.pending" class="msg-status">发送中...</span>
                  <button
                    v-if="msg.failed"
                    class="msg-retry-btn"
                    @click="retrySend(msg)"
                    title="重新发送"
                  >发送失败，点击重试</button>
                  <span v-else class="msg-time">{{ formatTime(msg.created_at) }}</span>
                  <button
                    v-if="msg.sender_id === auth.user?.id && !msg.pending"
                    class="msg-delete-btn"
                    :disabled="deleting === msg.id"
                    @click="handleDelete(msg.id)"
                    title="删除消息"
                  >{{ deleting === msg.id ? '...' : '×' }}</button>
                  <span
                    v-if="msg.sender_id === auth.user?.id && !msg.pending && !msg.failed"
                    class="msg-read-status"
                    :class="{ 'msg-read-status--read': msg.is_read }"
                  >{{ msg.is_read ? '已读' : '未读' }}</span>
                </div>
                </div>
              </TransitionGroup>
              <EmptyState v-if="!chatLoading && messages.length === 0" icon="💬" title="开始对话" description="发送第一条消息" />
            </template>
          </div>
          <div class="chat-input">
            <button
              class="chat-input__attach"
              :disabled="uploadingFile"
              @click="triggerAttachment"
              :title="uploadingFile ? '上传中...' : '发送图片/文件'"
            >
              <AppIcon v-if="!uploadingFile" name="image" :size="18" />
              <span v-else class="uploading-spinner" />
            </button>
            <input
              v-model="messageText"
              class="chat-input__field"
              placeholder="输入消息..."
              maxlength="5000"
              @keyup.enter="handleSend"
            />
            <!-- 隐藏的文件选择器 -->
            <input
              ref="attachmentInput"
              type="file"
              accept="image/*,.pdf,.doc,.docx,.xls,.xlsx,.ppt,.pptx,.txt,.csv,.zip"
              style="display:none"
              @change="handleAttachmentSelected"
            />
            <button class="chat-input__send" :disabled="(!messageText.trim() && !uploadingFile) || sending" @click="handleSend">
              {{ sending ? '...' : '发送' }}
            </button>
          </div>
        </template>
        <div v-else class="chat-empty">
          <EmptyState icon="✉️" title="选择一个对话" description="从左侧选择私信开始交流" action-label="发起新私信" @action="showNewConversation" />
        </div>
      </main>
    </div>

    <!-- 新对话弹窗 -->
    <Teleport to="body">
      <div v-if="showNewConv" class="new-conv-overlay" @click.self="closeNewConversation">
        <div class="new-conv-dialog">
          <div class="new-conv-dialog__header">
            <h3>发起新私信</h3>
            <button class="new-conv-dialog__close" @click="closeNewConversation">×</button>
          </div>
          <div class="new-conv-dialog__search">
            <input
              v-model="searchKeyword"
              class="new-conv-dialog__input"
              placeholder="搜索用户昵称..."
              @input="onSearchInput"
              @keyup.escape="closeNewConversation"
            />
          </div>
          <div class="new-conv-dialog__results">
            <Loading v-if="searchingUsers" variant="skeleton" :rows="4" />
            <EmptyState v-else-if="searchKeyword.trim() && searchResults.length === 0" icon="🔍" title="未找到用户" />
            <button
              v-for="user in searchResults"
              :key="user.id"
              class="user-result-item"
              @click="startNewChat(user.id)"
            >
              <img
                :src="user.avatar_url || ''"
                :alt="user.nickname"
                class="user-result-avatar"
                @error="$event.target.style.display='none'"
              />
              <div class="user-result-info">
                <strong>{{ user.nickname }}</strong>
                <span v-if="user.bio">{{ user.bio }}</span>
              </div>
            </button>
          </div>
        </div>
      </div>
    </Teleport>
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
.conv-name-row { display: flex; align-items: center; gap: 6px; }
.conv-name { display: block; font-size: 14px; overflow: hidden; text-overflow: ellipsis; white-space: nowrap; flex: 1; }
.conv-name--unread { font-weight: 700; color: var(--color-text-primary); }
.conv-unread-badge {
  display: inline-flex;
  align-items: center;
  justify-content: center;
  min-width: 18px;
  height: 18px;
  padding: 0 5px;
  border-radius: 9px;
  background: var(--color-primary);
  color: #fff;
  font-size: 11px;
  font-weight: 700;
  line-height: 1;
  flex-shrink: 0;
}
.conv-preview { color: var(--color-text-muted); display: block; font-size: 12px; overflow: hidden; text-overflow: ellipsis; white-space: nowrap; margin-top: 2px; }
.conv-preview--unread { color: var(--color-text-body); font-weight: 500; }
.chat-area { flex: 1; display: flex; flex-direction: column; }
.chat-header { align-items: center; border-bottom: 1px solid var(--color-border); display: flex; gap: 10px; padding: 14px 20px; }
.chat-avatar { border-radius: 50%; height: 32px; width: 32px; object-fit: cover; }
.chat-messages { flex: 1; overflow-y: auto; padding: 20px; display: flex; flex-direction: column; gap: 12px; }
.msg { display: flex; flex-direction: column; max-width: 70%; }
.msg--own { align-self: flex-end; align-items: flex-end; }
.msg-bubble { background: var(--color-bg-hover); border-radius: 12px 12px 12px 4px; font-size: 14px; padding: 10px 14px; word-break: break-word; line-height: 1.5; }
.msg--own .msg-bubble { background: var(--color-primary); color: #fff; border-radius: 12px 12px 4px 12px; }
.msg-meta {
  display: flex;
  align-items: center;
  gap: 6px;
  margin-top: 4px;
}
.msg--own .msg-meta { justify-content: flex-end; }
.msg-time { color: var(--color-text-muted); font-size: 11px; }
.msg-delete-btn {
  background: none;
  border: 0;
  border-radius: 50%;
  color: var(--color-text-muted);
  cursor: pointer;
  font-size: 16px;
  line-height: 1;
  padding: 0;
  width: 18px;
  height: 18px;
  display: inline-flex;
  align-items: center;
  justify-content: center;
  opacity: 0;
  transition: opacity 0.15s, color 0.15s;
}
.msg:hover .msg-delete-btn { opacity: 1; }
.msg-delete-btn:hover { color: var(--color-danger); }
.msg-delete-btn:disabled { opacity: 0.5; cursor: not-allowed; }
.msg-read-status {
  color: var(--color-text-muted);
  font-size: 10px;
  flex-shrink: 0;
  white-space: nowrap;
}
.msg-read-status--read {
  opacity: 0.5;
}
.chat-input { border-top: 1px solid var(--color-border); display: flex; gap: 8px; padding: 12px 16px; }
.chat-input__field { border: 1px solid var(--color-border-input); border-radius: 8px; flex: 1; font: inherit; font-size: 14px; padding: 10px 14px; }
.chat-input__field:focus { border-color: var(--color-primary); outline: none; }
.chat-input__send { background: var(--color-primary); border: 0; border-radius: 8px; color: #fff; cursor: pointer; font: inherit; font-size: 14px; padding: 10px 20px; white-space: nowrap; }
.chat-input__send:disabled { opacity: 0.5; }
.chat-empty { flex: 1; display: flex; align-items: center; justify-content: center; }

/* === 消息入场动画（侧栏滑入） === */
.msg-slide-enter-active {
  animation-duration: 0.3s;
  animation-timing-function: cubic-bezier(0.25, 0.46, 0.45, 0.94);
  animation-fill-mode: both;
}
.msg-slide-leave-active {
  animation: msg-slide-out 0.2s ease forwards;
}

/* 自己发的消息：从右侧滑入 */
.msg--own.msg-slide-enter-active {
  animation-name: msg-slide-in-right;
}
/* 收到的消息：从左侧滑入 */
.msg:not(.msg--own).msg-slide-enter-active {
  animation-name: msg-slide-in-left;
}

@keyframes msg-slide-in-right {
  from {
    opacity: 0;
    transform: translateX(40px);
  }
  to {
    opacity: 1;
    transform: translateX(0);
  }
}
@keyframes msg-slide-in-left {
  from {
    opacity: 0;
    transform: translateX(-40px);
  }
  to {
    opacity: 1;
    transform: translateX(0);
  }
}
@keyframes msg-slide-out {
  from { opacity: 1; transform: scale(1); }
  to { opacity: 0; transform: scale(0.8); }
}

/* === 发送中状态 === */
.msg--pending .msg-bubble {
  opacity: 0.65;
}
.msg-sending-indicator {
  display: flex;
  gap: 4px;
  align-items: center;
  justify-content: center;
}
.msg-sending-dot {
  width: 6px;
  height: 6px;
  border-radius: 50%;
  background: var(--color-text-muted);
  animation: dot-bounce 1.2s infinite ease-in-out both;
}
.msg--own .msg-sending-dot {
  background: rgba(255,255,255,0.8);
}
.msg-sending-dot:nth-child(1) { animation-delay: -0.32s; }
.msg-sending-dot:nth-child(2) { animation-delay: -0.16s; }
.msg-sending-dot:nth-child(3) { animation-delay: 0s; }
@keyframes dot-bounce {
  0%, 80%, 100% { transform: scale(0.4); opacity: 0.3; }
  40% { transform: scale(1); opacity: 1; }
}

/* === 发送失败状态 === */
.msg--failed .msg-bubble {
  border: 1px dashed var(--color-danger);
  opacity: 0.7;
}
.msg-status {
  color: var(--color-text-muted);
  font-size: 11px;
}
.msg-retry-btn {
  background: none;
  border: 0;
  color: var(--color-danger);
  cursor: pointer;
  font-size: 11px;
  padding: 0;
  text-decoration: underline;
}
.msg-retry-btn:hover { color: #c0392b; }

/* 附件按钮 */
.chat-input__attach {
  background: none;
  border: 1px solid var(--color-border-input);
  border-radius: 8px;
  color: var(--color-text-secondary);
  cursor: pointer;
  padding: 10px;
  display: inline-flex;
  align-items: center;
  justify-content: center;
  transition: background 0.15s, border-color 0.15s;
}
.chat-input__attach:hover { background: var(--color-bg-hover); border-color: var(--color-primary); }
.chat-input__attach:disabled { opacity: 0.5; cursor: not-allowed; }

.uploading-spinner {
  border: 2px solid var(--color-border);
  border-top-color: var(--color-primary);
  border-radius: 50%;
  width: 14px;
  height: 14px;
  animation: spin 0.6s linear infinite;
  display: inline-block;
}
@keyframes spin { to { transform: rotate(360deg); } }

/* 图片消息 */
.msg-image {
  border-radius: 8px;
  max-width: 240px;
  max-height: 240px;
  object-fit: cover;
  display: block;
}
.msg-bubble:has(.msg-image) {
  padding: 4px;
  background: transparent !important;
}
.msg--own .msg-bubble:has(.msg-image) {
  background: transparent !important;
}

/* 文件消息 */
.msg-file {
  align-items: center;
  color: inherit;
  display: flex;
  gap: 8px;
  text-decoration: none;
}
.msg--own .msg-file { color: #fff; }
.msg-file__icon { font-size: 18px; flex-shrink: 0; }
.msg-file__name {
  font-size: 13px;
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
  text-decoration: underline;
}

/* 新对话按钮 */
.conv-list__header {
  display: flex;
  align-items: center;
  justify-content: space-between;
}
.new-conv-btn {
  background: var(--color-primary);
  border: 0;
  border-radius: 50%;
  color: #fff;
  cursor: pointer;
  font-size: 18px;
  width: 28px;
  height: 28px;
  display: inline-flex;
  align-items: center;
  justify-content: center;
  line-height: 1;
  padding: 0;
  transition: background 0.15s;
}
.new-conv-btn:hover { background: var(--color-primary-hover); }

/* 新对话弹窗 */
.new-conv-overlay {
  background: var(--color-bg-overlay);
  inset: 0;
  position: fixed;
  z-index: 100;
  display: flex;
  align-items: center;
  justify-content: center;
}
.new-conv-dialog {
  background: var(--color-bg-card);
  border-radius: 12px;
  width: 420px;
  max-height: 480px;
  display: flex;
  flex-direction: column;
  box-shadow: 0 10px 40px rgba(0,0,0,0.25);
}
.new-conv-dialog__header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: 16px 20px;
  border-bottom: 1px solid var(--color-border);
}
.new-conv-dialog__header h3 { margin: 0; font-size: 16px; }
.new-conv-dialog__close {
  background: none;
  border: 0;
  border-radius: 6px;
  color: var(--color-text-muted);
  cursor: pointer;
  font-size: 20px;
  padding: 4px 8px;
  line-height: 1;
}
.new-conv-dialog__close:hover { background: var(--color-bg-hover); color: var(--color-text-body); }
.new-conv-dialog__search { padding: 12px 20px; border-bottom: 1px solid var(--color-border); }
.new-conv-dialog__input {
  border: 1px solid var(--color-border-input);
  border-radius: 8px;
  font: inherit;
  font-size: 14px;
  padding: 10px 14px;
  width: 100%;
  box-sizing: border-box;
}
.new-conv-dialog__input:focus { border-color: var(--color-primary); outline: none; }
.new-conv-dialog__results { flex: 1; overflow-y: auto; padding: 8px; }
.user-result-item {
  align-items: center;
  background: none;
  border: 0;
  border-radius: 8px;
  cursor: pointer;
  display: flex;
  gap: 12px;
  padding: 10px 12px;
  width: 100%;
  text-align: left;
  font: inherit;
  transition: background 0.15s;
}
.user-result-item:hover { background: var(--color-bg-hover); }
.user-result-avatar {
  border-radius: 50%;
  height: 40px;
  width: 40px;
  object-fit: cover;
  flex-shrink: 0;
}
.user-result-info {
  display: grid;
  gap: 2px;
  min-width: 0;
}
.user-result-info strong { font-size: 14px; color: var(--color-text-primary); }
.user-result-info span {
  font-size: 12px;
  color: var(--color-text-muted);
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
}
</style>
