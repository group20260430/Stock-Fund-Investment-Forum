import { api } from '../utils/request'

/** 发送验证码 */
export function sendCode(phone, type = 'register') {
  return api.post('/auth/send-code', { phone, type })
}

/** 邮箱验证码 */
export function sendEmailCode(email, type = 'register') {
  return api.post('/auth/email/send-code', { email, type })
}

/** 验证邮箱验证码 */
export function verifyEmailCode(email, code) {
  return api.post('/auth/email/verify-code', { email, code })
}

/** 邮箱注册 */
export function registerByEmail(data) {
  return api.post('/auth/email/register', data)
}

/** 手机号注册 */
export function register(data) {
  return api.post('/auth/register', data)
}

/** 密码登录 */
export function loginWithPassword(phone, password) {
  return api.post('/auth/login', { phone, password, login_type: 'password' })
}

/** 验证码登录 */
export function loginWithCode(phone, code) {
  return api.post('/auth/login', { phone, code, login_type: 'code' })
}

/** 忘记密码：验证码重置密码 */
export function resetPassword(account, code, newPassword) {
  return api.post('/auth/reset-password', { account, code, new_password: newPassword })
}

/** 刷新 Token */
export function refreshToken() {
  return api.post('/auth/refresh')
}

/** 获取当前用户信息 */
export function getMe() {
  return api.get('/auth/me')
}

/** 更新个人资料 */
export function updateProfile(data) {
  return api.put('/auth/profile', data)
}

/** 提交实名认证 */
export function submitCertification(data) {
  return api.post('/auth/certification', data)
}

/** 提交风险评估问卷 */
export function submitRiskAssessment(answers) {
  return api.post('/auth/risk-assessment', { answers })
}

/** 获取风险评估问卷 */
export function getRiskQuestions() {
  return api.get('/auth/risk-assessment/questions')
}

/** 获取历史评估记录 */
export function fetchRiskHistory(params) {
  return api.get('/auth/risk-assessment/history', params)
}

/** 获取隐私设置 */
export function fetchPrivacySettings() {
  return api.get('/auth/privacy')
}

/** 更新隐私设置 */
export function updatePrivacySettings(data) {
  return api.put('/auth/privacy', data)
}

/** 获取积分历史 */
export function fetchPointsHistory(params) {
  return api.get('/auth/points/history', params)
}
