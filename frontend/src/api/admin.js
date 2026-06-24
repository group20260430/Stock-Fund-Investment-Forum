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

/** 实名认证审核列表 */
export function fetchCertifications(params) {
  return api.get('/admin/certifications', params)
}

/** 审核实名认证 */
export function reviewCertification(id, action, reason) {
  return api.post(`/admin/certifications/${id}/review`, { action, comment: reason })
}

/** 专业认证审核列表 */
export function fetchProfessionalCertifications(params) {
  return api.get('/admin/professional-certifications', params)
}

/** 审核专业认证 */
export function reviewProfessionalCertification(id, action, reason) {
  return api.post(`/admin/professional-certifications/${id}/review`, { action, comment: reason })
}

/** 敏感词列表 */
export function fetchSensitiveWords(params) {
  return api.get('/admin/sensitive-words', params)
}

/** 添加敏感词 */
export function addSensitiveWord(word, level) {
  return api.post('/admin/sensitive-words', { word, level })
}

/** 删除敏感词 */
export function deleteSensitiveWord(id) {
  return api.delete(`/admin/sensitive-words/${id}`)
}

/** 操作日志 */
export function fetchActivityLogs(params) {
  return api.get('/admin/activity-logs', params)
}

/** 热门话题分析 */
export function fetchHotTopics(params) {
  return api.get('/admin/stats/hot-topics', params)
}

/** 用户参与度报告 */
export function fetchEngagementReport(params) {
  return api.get('/admin/stats/engagement', params)
}

/** 合规检查：对文本执行合规检测 */
export function checkCompliance(data) {
  return api.post('/admin/compliance/check', data)
}

/** 合规规则列表 */
export function fetchComplianceRules() {
  return api.get('/admin/compliance/rules')
}

/** 添加合规规则 */
export function addComplianceRule(data) {
  return api.post('/admin/compliance/rules', data)
}

/** 删除合规规则 */
export function deleteComplianceRule(id) {
  return api.delete(`/admin/compliance/rules/${id}`)
}
