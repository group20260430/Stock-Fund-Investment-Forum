import { api } from '../utils/request'

/** 获取通知列表 */
export function fetchNotifications(params) {
  return api.get('/notifications', params)
}

/** 标记通知为已读 */
export function markNotificationsRead(notificationIds) {
  return api.put('/notifications/read', notificationIds ? { notification_ids: notificationIds } : {})
}

/** 获取未读通知数量 */
export function fetchUnreadNotificationCount() {
  return api.get('/notifications/unread-count')
}
