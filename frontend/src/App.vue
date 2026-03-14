<template>
  <n-message-provider>
    <div class="min-h-screen bg-dark-900 text-white">
      <!-- Header -->
      <LayoutHeader @toggle-sidebar="sidebarOpen = true" />
      
      <!-- Sidebar -->
      <LayoutSidebar :mobile-open="sidebarOpen" @close="sidebarOpen = false" />
      
      <!-- Main Content -->
      <main
        :class="[
          'min-h-screen pt-16 pb-20 lg:pb-0 transition-all duration-300',
          'lg:pl-64'
        ]"
      >
        <div class="p-4 lg:p-6 max-w-7xl mx-auto">
          <router-view v-slot="{ Component }">
            <transition name="fade" mode="out-in">
              <component :is="Component" />
            </transition>
          </router-view>
        </div>
      </main>
      
      <!-- Player Bar -->
      <PlayerBar />
      
      <!-- Mobile Bottom Navigation -->
      <MobileNav />
      
      <!-- Footer (Desktop only) -->
      <LayoutFooter class="hidden lg:block" />
    </div>
  </n-message-provider>
</template>

<script setup lang="ts">
import { ref } from 'vue'
import { NMessageProvider } from 'naive-ui'
import LayoutHeader from '@/components/common/LayoutHeader.vue'
import LayoutSidebar from '@/components/common/LayoutSidebar.vue'
import LayoutFooter from '@/components/common/LayoutFooter.vue'
import MobileNav from '@/components/common/MobileNav.vue'

const sidebarOpen = ref(false)
</script>

<style>
/* Page transitions */
.fade-enter-active,
.fade-leave-active {
  transition: opacity 0.2s ease;
}

.fade-enter-from,
.fade-leave-to {
  opacity: 0;
}

/* Custom scrollbar */
::-webkit-scrollbar {
  width: 8px;
  height: 8px;
}

::-webkit-scrollbar-track {
  background: #1a1a1a;
  border-radius: 4px;
}

::-webkit-scrollbar-thumb {
  background: rgba(255, 255, 255, 0.2);
  border-radius: 4px;
}

::-webkit-scrollbar-thumb:hover {
  background: rgba(255, 255, 255, 0.3);
}

/* Selection color */
::selection {
  background: rgba(29, 185, 84, 0.3);
  color: white;
}
</style>
