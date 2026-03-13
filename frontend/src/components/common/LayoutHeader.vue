<template>
  <header class="fixed top-0 left-0 right-0 z-50 h-16 glass border-b border-white/10">
    <div class="h-full px-4 lg:px-6 flex items-center justify-between">
      <!-- Left: Logo & Title -->
      <div class="flex items-center gap-4">
        <button
          v-if="isMobile"
          class="lg:hidden btn-ghost p-2"
          @click="$emit('toggle-sidebar')"
        >
          <svg class="w-6 h-6" fill="none" stroke="currentColor" viewBox="0 0 24 24">
            <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M4 6h16M4 12h16M4 18h16" />
          </svg>
        </button>
        <router-link to="/" class="flex items-center gap-3">
          <div class="w-10 h-10 rounded-xl bg-gradient-to-br from-accent to-accent-hover flex items-center justify-center">
            <svg class="w-6 h-6 text-white" fill="currentColor" viewBox="0 0 24 24">
              <path d="M12 3v10.55c-.59-.34-1.27-.55-2-.55-2.21 0-4 1.79-4 4s1.79 4 4 4 4-1.79 4-4V7h4V3h-6z"/>
            </svg>
          </div>
          <h1 class="text-xl font-bold gradient-text hidden sm:block">MusicPilot</h1>
        </router-link>
      </div>

      <!-- Center: Search -->
      <div class="flex-1 max-w-xl mx-4 hidden md:block">
        <div class="relative">
          <input
            v-model="searchQuery"
            type="text"
            placeholder="搜索音乐、艺术家、专辑..."
            class="w-full input-glass pl-10"
            @keyup.enter="handleSearch"
          />
          <svg class="absolute left-3 top-1/2 -translate-y-1/2 w-5 h-5 text-white/40" fill="none" stroke="currentColor" viewBox="0 0 24 24">
            <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M21 21l-6-6m2-5a7 7 0 11-14 0 7 7 0 0114 0z" />
          </svg>
        </div>
      </div>

      <!-- Right: Actions -->
      <div class="flex items-center gap-2">
        <!-- Mobile Search Button -->
        <button class="md:hidden btn-ghost p-2" @click="showMobileSearch = true">
          <svg class="w-6 h-6" fill="none" stroke="currentColor" viewBox="0 0 24 24">
            <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M21 21l-6-6m2-5a7 7 0 11-14 0 7 7 0 0114 0z" />
          </svg>
        </button>

        <!-- Theme Toggle -->
        <button class="btn-ghost p-2" @click="toggleTheme">
          <svg v-if="isDark" class="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
            <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M12 3v1m0 16v1m9-9h-1M4 12H3m15.364 6.364l-.707-.707M6.343 6.343l-.707-.707m12.728 0l-.707.707M6.343 17.657l-.707.707M16 12a4 4 0 11-8 0 4 4 0 018 0z" />
          </svg>
          <svg v-else class="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
            <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M20.354 15.354A9 9 0 018.646 3.646 9.003 9.003 0 0012 21a9.003 9.003 0 008.354-5.646z" />
          </svg>
        </button>

        <!-- Settings -->
        <router-link to="/settings" class="btn-ghost p-2">
          <svg class="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
            <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M10.325 4.317c.426-1.756 2.924-1.756 3.35 0a1.724 1.724 0 002.573 1.066c1.543-.94 3.31.826 2.37 2.37a1.724 1.724 0 001.065 2.572c1.756.426 1.756 2.924 0 3.35a1.724 1.724 0 00-1.066 2.573c.94 1.543-.826 3.31-2.37 2.37a1.724 1.724 0 00-2.572 1.065c-.426 1.756-2.924 1.756-3.35 0a1.724 1.724 0 00-2.573-1.066c-1.543.94-3.31-.826-2.37-2.37a1.724 1.724 0 00-1.065-2.572c-1.756-.426-1.756-2.924 0-3.35a1.724 1.724 0 001.066-2.573c-.94-1.543.826-3.31 2.37-2.37.996.608 2.296.07 2.572-1.065z" />
            <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M15 12a3 3 0 11-6 0 3 3 0 016 0z" />
          </svg>
        </router-link>
      </div>
    </div>

    <!-- Mobile Search Modal -->
    <div
      v-if="showMobileSearch"
      class="fixed inset-0 z-50 bg-dark-900/95 backdrop-blur-xl"
      @click.self="showMobileSearch = false"
    >
      <div class="p-4">
        <div class="flex items-center gap-4 mb-4">
          <input
            v-model="searchQuery"
            type="text"
            placeholder="搜索音乐、艺术家、专辑..."
            class="flex-1 input-glass"
            autofocus
            @keyup.enter="handleSearch"
          />
          <button class="btn-ghost" @click="showMobileSearch = false">取消</button>
        </div>
      </div>
    </div>
  </header>
</template>

<script setup lang="ts">
import { ref, computed } from 'vue'
import { useRouter } from 'vue-router'
import { useTheme } from '@/composables/useTheme'

const router = useRouter()
const { isDark, toggleTheme } = useTheme()

const searchQuery = ref('')
const showMobileSearch = ref(false)

const isMobile = computed(() => window.innerWidth < 1024)

defineEmits<{
  'toggle-sidebar': []
}>()

const handleSearch = () => {
  if (searchQuery.value.trim()) {
    router.push({
      path: '/search',
      query: { q: searchQuery.value }
    })
    showMobileSearch.value = false
  }
}
</script>
