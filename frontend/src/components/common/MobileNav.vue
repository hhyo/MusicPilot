<template>
  <!-- 移动端底部导航 -->
  <nav class="lg:hidden fixed bottom-0 left-0 right-0 z-40 glass border-t border-white/10">
    <div class="flex items-center justify-around h-16 px-2">
      <router-link
        v-for="item in navItems"
        :key="item.path"
        :to="item.path"
        class="flex flex-col items-center justify-center gap-1 flex-1 h-full py-2 transition-all duration-200"
        :class="isActive(item.path) ? 'text-accent' : 'text-white/50 hover:text-white'"
      >
        <span class="text-xl">{{ item.icon }}</span>
        <span class="text-xs font-medium">{{ item.label }}</span>
      </router-link>
    </div>
  </nav>
</template>

<script setup lang="ts">
import { computed } from 'vue'
import { useRoute } from 'vue-router'

const route = useRoute()

const navItems = [
  { path: '/', icon: '🏠', label: '首页' },
  { path: '/library', icon: '📚', label: '音乐库' },
  { path: '/chart', icon: '📊', label: '榜单' },
  { path: '/download', icon: '⬇️', label: '下载' },
  { path: '/organize', icon: '📁', label: '整理' },
]

const isActive = (path: string) => {
  if (path === '/') {
    return route.path === '/'
  }
  return route.path.startsWith(path)
}
</script>