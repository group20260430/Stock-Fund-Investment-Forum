import { defineStore } from 'pinia'
import { ref, computed } from 'vue'
import { getToken, setToken, removeToken, setUser, removeUser, getUser, parseToken } from '../utils/auth'
import { getMe, loginWithPassword as loginApi, loginWithCode as loginCodeApi, register as registerApi } from '../api/auth'

export const useAuthStore = defineStore('auth', () => {
  // State
  const user = ref(getUser())
  const token = ref(getToken())

  // Getters
  const isLoggedIn = computed(() => !!token.value)
  const userRole = computed(() => {
    if (!token.value) return null
    const payload = parseToken(token.value)
    return payload?.role || 'user'
  })
  const isAdmin = computed(() => {
    if (userRole.value === 'admin') return true
    if (user.value?.role === 'admin') return true
    return false
  })

  // Actions
  async function login(credentials) {
    let result
    if (credentials.login_type === 'code' || credentials.code) {
      result = await loginCodeApi(credentials.phone, credentials.code)
    } else {
      result = await loginApi(credentials.phone, credentials.password)
    }
    return commitLogin(result)
  }

  async function register(data) {
    const result = await registerApi(data)
    return commitLogin(result)
  }

  async function registerByEmailAction(data) {
    const { registerByEmail } = await import('../api/auth')
    const result = await registerByEmail(data)
    return commitLogin(result)
  }

  function commitLogin(data) {
    if (data.token) {
      token.value = data.token
      setToken(data.token)
    }
    if (data.user) {
      user.value = data.user
      setUser(data.user)
    }
    return data
  }

  async function fetchUser() {
    try {
      const data = await getMe()
      user.value = data
      setUser(data)
      return data
    } catch (err) {
      // Token 过期或其他错误 — 不清除状态，由 request.js 拦截处理
      console.error('获取用户信息失败:', err.message)
      return null
    }
  }

  async function updateProfile(data) {
    const { updateProfile } = await import('../api/auth')
    const result = await updateProfile(data)
    user.value = { ...user.value, ...result }
    setUser(user.value)
    return result
  }

  function logout() {
    token.value = null
    user.value = null
    removeToken()
    removeUser()
  }

  return {
    user,
    token,
    isLoggedIn,
    userRole,
    isAdmin,
    login,
    register,
    registerByEmail: registerByEmailAction,
    fetchUser,
    updateProfile,
    logout,
  }
})
