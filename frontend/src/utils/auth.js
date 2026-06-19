/**
 * Token 管理工具
 */
const TOKEN_KEY = 'token'
const USER_KEY = 'user'

export function getToken() {
  return localStorage.getItem(TOKEN_KEY)
}

export function setToken(token) {
  localStorage.setItem(TOKEN_KEY, token)
}

export function removeToken() {
  localStorage.removeItem(TOKEN_KEY)
}

export function getUser() {
  try {
    const raw = localStorage.getItem(USER_KEY)
    return raw ? JSON.parse(raw) : null
  } catch {
    return null
  }
}

export function setUser(user) {
  localStorage.setItem(USER_KEY, JSON.stringify(user))
}

export function removeUser() {
  localStorage.removeItem(USER_KEY)
}

/**
 * 解析 JWT payload（不验证签名，仅用于读取用户角色等非敏感信息）
 */
export function parseToken(token) {
  try {
    const payload = token.split('.')[1]
    return JSON.parse(atob(payload))
  } catch {
    return null
  }
}

/**
 * 获取当前登录用户的角色
 */
export function getUserRole() {
  const token = getToken()
  if (!token) return null
  const payload = parseToken(token)
  return payload?.role || 'user'
}

/**
 * 检查是否已登录
 */
export function isLoggedIn() {
  return !!getToken()
}

/**
 * 清除所有登录状态
 */
export function clearAuth() {
  removeToken()
  removeUser()
}
