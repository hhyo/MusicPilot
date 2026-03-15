<template>
  <!-- Desktop Sidebar -->
  <aside
    :class="[
      'fixed left-0 top-16 bottom-0 w-64 glass border-r border-white/10 z-40',
      'hidden lg:block transition-all duration-300',
      collapsed && 'w-20'
    ]"
  >
    <nav class="p-4 space-y-2">
      <NavItem
        v-for="item in navItems"
        :key="item.path"
        :item="item"
        :collapsed="collapsed"
      />
    </nav>

    <!-- Collapse Button -->
    <button
      class="absolute -right-3 top-8 w-6 h-6 rounded-full bg-accent text-white flex items-center justify-center shadow-lg"
      @click="collapsed = !collapsed"
    >
      <svg
        :class="['w-4 h-4 transition-transform', collapsed && 'rotate-180']"
        fill="none"
        stroke="currentColor"
        viewBox="0 0 24 24"
      >
        <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M15 19l-7-7 7-7" />
      </svg>
    </button>
  </aside>

  <!-- Mobile Sidebar Drawer -->
  <Transition name="slide">
    <div
      v-if="mobileOpen"
      class="fixed inset-0 z-50 lg:hidden"
    >
      <!-- Backdrop -->
      <div
        class="absolute inset-0 bg-black/50 backdrop-blur-sm"
        @click="$emit('close')"
      />
      
      <!-- Drawer -->
      <aside class="absolute left-0 top-0 bottom-0 w-72 bg-dark-800 border-r border-white/10">
        <div class="p-4">
          <div class="flex items-center justify-between mb-6">
            <h2 class="text-xl font-bold gradient-text">MusicPilot</h2>
            <button class="btn-ghost p-2" @click="$emit('close')">
              <svg class="w-6 h-6" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M6 18L18 6M6 6l12 12" />
              </svg>
            </button>
          </div>
          
          <nav class="space-y-2">
            <NavItem
              v-for="item in navItems"
              :key="item.path"
              :item="item"
              :collapsed="false"
              @click="$emit('close')"
            />
          </nav>
        </div>
      </aside>
    </div>
  </Transition>

  <!-- Mobile Bottom Navigation -->
  <nav class="fixed bottom-0 left-0 right-0 h-16 glass border-t border-white/10 z-50 lg:hidden">
    <div class="h-full flex items-center justify-around px-4">
      <router-link
        v-for="item in mobileNavItems"
        :key="item.path"
        :to="item.path"
        class="flex flex-col items-center gap-1 text-white/60 hover:text-white transition-colors"
        :class="{ 'text-accent': $route.path === item.path }"
      >
        <component :is="item.icon" class="w-6 h-6" />
        <span class="text-xs">{{ item.label }}</span>
      </router-link>
    </div>
  </nav>
</template>

<script setup lang="ts">
import { ref, computed, Component } from 'vue'
import { useRoute } from 'vue-router'
import NavItem from './NavItem.vue'
import { 
  Home as HomeIcon,
  Search as SearchIcon,
  Notifications as BellIcon,
  Download as DownloadIcon,
  Folder as FolderIcon,
  Globe as GlobeIcon,
  Settings as SettingsIcon
} from '@vicons/ionicons5'

const route = useRoute()

interface NavItemType {
  path: string
  label: string
  icon: Component
  children?: NavItemType[]
}

const collapsed = ref(false)

const props = defineProps<{
  mobileOpen: boolean
}>()

defineEmits<{
  close: []
}>()

const navItems: NavItemType[] = [
  { path: '/', label: '首页', icon: HomeIcon },
  { path: '/discover', label: '发现', icon: SearchIcon },
  { path: '/subscribe', label: '订阅', icon: BellIcon },
  { path: '/download', label: '下载', icon: DownloadIcon },
  { path: '/organize', label: '整理', icon: FolderIcon },
  { path: '/site', label: '站点', icon: GlobeIcon },
]

const mobileNavItems = [
  { path: '/', label: '首页', icon: HomeIcon },
  { path: '/discover', label: '发现', icon: SearchIcon },
  { path: '/subscribe', label: '订阅', icon: BellIcon },
  { path: '/settings', label: '设置', icon: SettingsIcon },
]
</script>

<style scoped>
.slide-enter-active,
.slide-leave-active {
  transition: transform 0.3s ease;
}

.slide-enter-from,
.slide-leave-to {
  transform: translateX(-100%);
}
</style>
