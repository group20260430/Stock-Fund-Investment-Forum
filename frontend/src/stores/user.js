import { defineStore } from 'pinia'
import { ref } from 'vue'
import { fetchUserProfile } from '../api/users'

export const useUserStore = defineStore('user', () => {
  const profile = ref(null)
  const loading = ref(false)
  const error = ref('')

  async function loadUserProfile(id) {
    loading.value = true
    error.value = ''
    try {
      profile.value = await fetchUserProfile(id)
      return profile.value
    } catch (err) {
      error.value = err.message
      profile.value = null
      return null
    } finally {
      loading.value = false
    }
  }

  function clearProfile() {
    profile.value = null
    error.value = ''
  }

  return {
    profile,
    loading,
    error,
    loadUserProfile,
    clearProfile,
  }
})
