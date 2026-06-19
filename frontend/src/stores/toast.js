import { defineStore } from 'pinia'
import { ref } from 'vue'

let nextId = 0

export const useToastStore = defineStore('toast', () => {
  const toasts = ref([])

  function add(message, type = 'info', duration = 4000) {
    const id = ++nextId
    toasts.value.push({ id, message, type, duration })
    if (duration > 0) {
      setTimeout(() => remove(id), duration)
    }
    return id
  }

  function remove(id) {
    toasts.value = toasts.value.filter(t => t.id !== id)
  }

  function success(msg, duration) { return add(msg, 'success', duration) }
  function error(msg, duration) { return add(msg, 'error', duration ?? 6000) }
  function info(msg, duration) { return add(msg, 'info', duration) }
  function warning(msg, duration) { return add(msg, 'warning', duration) }

  function clear() {
    toasts.value = []
  }

  return { toasts, add, remove, success, error, info, warning, clear }
})
