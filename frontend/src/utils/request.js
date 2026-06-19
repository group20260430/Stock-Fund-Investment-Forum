/**
 * HTTP 请求封装 — 统一拦截器、Token 注入、错误处理
 *
 * 后端统一响应格式：{ code: number, message: string, data: any }
 * 前端业务代码只需处理 data 字段。
 */
const API_BASE = import.meta.env.VITE_API_BASE_URL || 'http://localhost:8000/api'

async function request(url, options = {}) {
  const token = localStorage.getItem('token')

  const config = {
    headers: {
      'Content-Type': 'application/json',
      ...(token ? { Authorization: `Bearer ${token}` } : {}),
      ...options.headers,
    },
    ...options,
  }

  // 自动序列化 body
  if (config.body && typeof config.body === 'object' && !(config.body instanceof FormData)) {
    config.body = JSON.stringify(config.body)
  }

  // 剔除自定义字段，避免传给 fetch
  delete config.toast

  let response
  try {
    response = await fetch(`${API_BASE}${url}`, config)
  } catch (_networkError) {
    throw new Error('网络连接失败，请检查网络后重试')
  }

  // 204 No Content（删除操作等）
  if (response.status === 204) {
    return null
  }

  let result
  try {
    result = await response.json()
  } catch (_parseError) {
    throw new Error(`服务器响应异常 (${response.status})`)
  }

  if (!response.ok) {
    // Token 过期 / 未登录 — 清除登录态并跳转
    if (response.status === 401) {
      localStorage.removeItem('token')
      // 仅当不在登录页时才跳转，避免死循环
      if (!window.location.pathname.includes('/login')) {
        window.location.href = `/login?redirect=${encodeURIComponent(window.location.pathname)}`
      }
    }
    // 抛出后端错误信息
    const msg = result.message || `请求失败 (${response.status})`
    throw new Error(msg)
  }

  // 成功 — 解包 data 字段
  return result.data !== undefined ? result.data : result
}

// 便捷方法
export const api = {
  get: (url, params) => {
    const query = params ? '?' + new URLSearchParams(params).toString() : ''
    return request(`${url}${query}`, { method: 'GET' })
  },
  post: (url, data) => request(url, { method: 'POST', body: data }),
  put: (url, data) => request(url, { method: 'PUT', body: data }),
  patch: (url, data) => request(url, { method: 'PATCH', body: data }),
  delete: (url) => request(url, { method: 'DELETE' }),
}

export default request
