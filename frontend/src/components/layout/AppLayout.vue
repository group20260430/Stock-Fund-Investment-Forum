<script setup>
import { ref } from 'vue'
import SideBar from '../common/SideBar.vue'
import NavBar from '../common/NavBar.vue'
import ToastContainer from '../common/ToastContainer.vue'

const showMobileMenu = ref(false)

function toggleMobileMenu() {
  showMobileMenu.value = !showMobileMenu.value
}
</script>

<template>
  <div class="app-layout">
    <!-- 移动端遮罩 -->
    <div
      v-if="showMobileMenu"
      class="app-layout__overlay"
      @click="showMobileMenu = false"
    />

    <SideBar v-model:showMobileMenu="showMobileMenu" />

    <div class="app-layout__main">
      <NavBar
        v-model:showMobileMenu="showMobileMenu"
        @toggle-mobile-menu="toggleMobileMenu"
      />

      <main class="app-layout__content">
        <slot />
      </main>
    </div>

    <ToastContainer />
  </div>
</template>

<style scoped>
.app-layout {
  display: grid;
  grid-template-columns: var(--space-sidebar) 1fr;
  min-height: 100vh;
  background: var(--color-bg-page);
}

.app-layout__main {
  display: flex;
  flex-direction: column;
  min-width: 0;
  height: 100vh;
  overflow-y: auto;
}

.app-layout__content {
  padding: var(--space-content-padding);
  flex: 1;
}

.app-layout__overlay {
  background: var(--color-bg-overlay);
  display: none;
  inset: 0;
  position: fixed;
  z-index: var(--z-overlay);
}

@media (max-width: 780px) {
  .app-layout {
    grid-template-columns: 1fr;
  }

  .app-layout__overlay {
    display: block;
  }

  .app-layout__content {
    padding: var(--space-content-padding-mobile);
  }
}
</style>
