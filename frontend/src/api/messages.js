import { api } from '../utils/request'

/** 获取私信列表（对话分组或指定对话详情） */
export function fetchMessages(params) {
  return api.get('/messages', params)
}

/** 发送私信 */
export function sendMessage(data) {
  return api.post('/messages', data)
}

/** 删除私信 */
export function deleteMessage(messageId) {
  return api.delete(`/messages/${messageId}`)
}

/** 获取未读私信数量 */
export function fetchUnreadMessageCount() {
  return api.get('/messages/unread-count')
}
