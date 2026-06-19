import { api } from '../utils/request'

/** 审核队列 */
export function fetchReviewQueue(params) {
  return api.get('/admin/review-queue', params)
}

/** 审核操作 */
export function reviewItem(id, action, comment) {
  return api.post(`/admin/review-queue/${id}/review`, { action, comment })
}

/** 用户列表 */
export function fetchUsers(params) {
  return api.get('/admin/users', params)
}

/** 封禁/解封用户 */
export function banUser(userId, action, reason, durationHours) {
  return api.post(`/admin/users/${userId}/ban`, { action, reason, duration_hours: durationHours })
}

/** 数据总览 */
export function fetchStatsOverview() {
  return api.get('/admin/stats/overview')
}

/** 趋势数据 */
export function fetchStatsTrend(params) {
  return api.get('/admin/stats/trend', params)
}

/** 创建板块 */
export function createCategory(data) {
  return api.post('/admin/categories', data)
}

/** 编辑板块 */
export function updateCategory(id, data) {
  return api.put(`/admin/categories/${id}`, data)
}

/** 删除板块 */
export function deleteCategory(id) {
  return api.delete(`/admin/categories/${id}`)
}

/** 举报列表 */
export function fetchReports(params) {
  return api.get('/admin/reports', params)
}

/** 处理举报 */
export function handleReport(id, action) {
  return api.post(`/admin/reports/${id}`, { action })
}

/** 提交举报 */
export function submitReport(data) {
  return api.post('/report', data)
}

/** 私信列表 */
export function fetchMessages(params) {
  return api.get('/messages', params)
}

/** 发送私信 */
export function sendMessage(data) {
  return api.post('/messages', data)
}
