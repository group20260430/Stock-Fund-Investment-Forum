<script setup>
import { ref, watch, nextTick, onMounted, onUnmounted } from "vue"
import { searchSuggestions } from "../../api/search"

const props = defineProps({
  modelValue: { type: String, default: "" },
  placeholder: { type: String, default: "输入内容..." },
  rows: { type: [Number, String], default: 3 },
  maxlength: { type: [Number, String], default: 2000 },
  disabled: { type: Boolean, default: false },
})

const emit = defineEmits(["update:modelValue", "submit"])

const textareaRef = ref(null)
const dropdownRef = ref(null)
const suggestions = ref([])
const selectedIndex = ref(0)
const showDropdown = ref(false)
const mentionStart = ref(-1)
const mentionKeyword = ref("")
let debounceTimer = null

function getCursorPos(el) { return el.selectionStart }
function setCursorPos(el, pos) { el.focus(); el.setSelectionRange(pos, pos) }
function getTextBeforeCursor(el) { return el.value.slice(0, el.selectionStart) }

function checkMention() {
  const el = textareaRef.value
  if (!el) return
  const textBefore = getTextBeforeCursor(el)
  const atMatch = textBefore.match(/@([^@\s]*)$/)
  if (atMatch) {
    mentionStart.value = atMatch.index
    mentionKeyword.value = atMatch[1]
    fetchSuggestions(atMatch[1])
  } else {
    hideDropdown()
  }
}

function hideDropdown() {
  showDropdown.value = false
  suggestions.value = []
  selectedIndex.value = 0
  mentionStart.value = -1
  mentionKeyword.value = ""
}

async function fetchSuggestions(keyword) {
  if (debounceTimer) clearTimeout(debounceTimer)
  if (!keyword) { suggestions.value = []; showDropdown.value = false; return }
  debounceTimer = setTimeout(async () => {
    try {
      const data = await searchSuggestions(keyword, "user")
      suggestions.value = (data?.users || []).slice(0, 8)
      selectedIndex.value = 0
      showDropdown.value = suggestions.value.length > 0
    } catch { suggestions.value = []; showDropdown.value = false }
  }, 200)
}

function insertMention(user) {
  const el = textareaRef.value
  if (!el || mentionStart.value < 0) return
  const name = user.nickname || user.username || user.name || ""
  const before = el.value.slice(0, mentionStart.value)
  const after = el.value.slice(getCursorPos(el))
  const mentionText = "@" + name + " "
  emit("update:modelValue", before + mentionText + after)
  hideDropdown()
  nextTick(() => setCursorPos(el, mentionStart.value + mentionText.length))
}

function onKeydown(e) {
  if (!showDropdown.value || suggestions.value.length === 0) {
    if (e.key === "Enter" && !e.shiftKey) { e.preventDefault(); emit("submit") }
    return
  }
  if (e.key === "ArrowDown") { e.preventDefault(); selectedIndex.value = Math.min(selectedIndex.value + 1, suggestions.value.length - 1) }
  else if (e.key === "ArrowUp") { e.preventDefault(); selectedIndex.value = Math.max(selectedIndex.value - 1, 0) }
  else if (e.key === "Enter" || e.key === "Tab") { e.preventDefault(); const u = suggestions.value[selectedIndex.value]; if (u) insertMention(u) }
  else if (e.key === "Escape") { hideDropdown() }
}

function onInput(e) { emit("update:modelValue", e.target.value); checkMention() }

function onClickOutside(e) {
  if (dropdownRef.value && !dropdownRef.value.contains(e.target) && textareaRef.value && !textareaRef.value.contains(e.target)) { hideDropdown() }
}

function userDisplayName(user) { return user.nickname || user.username || user.name || "" }
function userAvatar(user) { return user.avatar_url || user.avatar || "" }

onMounted(() => document.addEventListener("click", onClickOutside))
onUnmounted(() => { document.removeEventListener("click", onClickOutside); if (debounceTimer) clearTimeout(debounceTimer) })
defineExpose({ focus: () => textareaRef.value?.focus() })
</script>

<template>
  <div class="mention-textarea">
    <textarea
      ref="textareaRef"
      :value="modelValue"
      :placeholder="placeholder"
      :rows="rows"
      :maxlength="maxlength"
      :disabled="disabled"
      class="mention-textarea__input"
      @input="onInput"
      @keydown="onKeydown"
    />
    <Transition name="mention-dropdown">
      <div v-if="showDropdown && suggestions.length" ref="dropdownRef" class="mention-dropdown">
        <div
          v-for="(user, idx) in suggestions"
          :key="user.id || idx"
          :class="['mention-dropdown__item', { 'mention-dropdown__item--active': idx === selectedIndex }]"
          @mousedown.prevent="insertMention(user)"
        >
          <img v-if="userAvatar(user)" :src="userAvatar(user)" :alt="userDisplayName(user)" class="mention-dropdown__avatar">
          <span v-else class="mention-dropdown__avatar-placeholder">{{ userDisplayName(user).charAt(0) }}</span>
          <div class="mention-dropdown__info">
            <span class="mention-dropdown__name">{{ userDisplayName(user) }}</span>
            <span v-if="user.username && user.username !== userDisplayName(user)" class="mention-dropdown__username">@{{ user.username }}</span>
          </div>
        </div>
      </div>
    </Transition>
  </div>
</template>

<style scoped>
.mention-textarea { position: relative; }
.mention-textarea__input {
  border: 1px solid var(--color-border-input);
  border-radius: var(--radius-lg);
  font: inherit;
  font-size: var(--font-size-base);
  padding: 12px 14px;
  resize: vertical;
  width: 100%;
  background: var(--color-bg-input);
  color: var(--color-text-primary);
  transition: border-color var(--duration-fast) var(--ease-out), box-shadow var(--duration-fast) var(--ease-out);
}
.mention-textarea__input:focus {
  border-color: var(--color-primary);
  box-shadow: 0 0 0 3px var(--color-primary-ring);
  outline: none;
  background: var(--color-bg-card);
}
.mention-textarea__input:disabled { opacity: 0.5; cursor: not-allowed; }

.mention-dropdown {
  position: absolute;
  left: 0;
  right: 0;
  bottom: 100%;
  margin-bottom: 4px;
  z-index: var(--z-dropdown);
  background: var(--color-bg-card);
  border: 1px solid var(--color-border);
  border-radius: var(--radius-xl);
  box-shadow: var(--shadow-lg);
  max-height: 224px;
  overflow-y: auto;
  padding: 6px;
}
.mention-dropdown-enter-active { transition: opacity var(--duration-fast) var(--ease-out), transform var(--duration-fast) var(--ease-out); }
.mention-dropdown-leave-active { transition: opacity var(--duration-fast) var(--ease-in-out), transform var(--duration-fast) var(--ease-in-out); }
.mention-dropdown-enter-from, .mention-dropdown-leave-to { opacity: 0; transform: translateY(4px); }
.mention-dropdown__item {
  align-items: center;
  border-radius: var(--radius-md);
  cursor: pointer;
  display: flex;
  gap: 10px;
  padding: 8px 10px;
  transition: background var(--duration-fast) var(--ease-out);
}
.mention-dropdown__item:hover, .mention-dropdown__item--active { background: var(--color-primary-light); }
.mention-dropdown__avatar { border-radius: var(--radius-full); flex-shrink: 0; height: 32px; object-fit: cover; width: 32px; }
.mention-dropdown__avatar-placeholder {
  align-items: center;
  background: var(--color-primary-light);
  border-radius: var(--radius-full);
  color: var(--color-primary);
  display: inline-flex;
  flex-shrink: 0;
  font-size: var(--font-size-sm);
  font-weight: var(--font-weight-semibold);
  height: 32px;
  justify-content: center;
  width: 32px;
}
.mention-dropdown__info { display: flex; flex-direction: column; min-width: 0; }
.mention-dropdown__name {
  color: var(--color-text-primary);
  font-size: var(--font-size-base);
  font-weight: var(--font-weight-medium);
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
}
.mention-dropdown__username { color: var(--color-text-muted); font-size: var(--font-size-xs); }
</style>
