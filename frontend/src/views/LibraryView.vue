<template>
  <div class="space-y-6 animate-fade-in">
    <!-- Header -->
    <div class="flex items-center justify-between">
      <h1 class="text-2xl font-bold">音乐库</h1>
      <div class="flex items-center gap-3">
        <Input
          v-model="searchQuery"
          placeholder="搜索专辑..."
          class="w-64"
        />
        <Button variant="primary" @click="refreshLibrary">
          <svg class="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
            <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M4 4v5h.582m15.356 2A8.001 8.001 0 004.582 9m0 0H9m11 11v-5h-.581m0 0a8.003 8.003 0 01-15.357-2m15.357 2H15" />
          </svg>
        </Button>
      </div>
    </div>

    <!-- Filter Tabs -->
    <div class="flex items-center gap-2">
      <button
        v-for="tab in tabs"
        :key="tab.value"
        :class="[
          'px-4 py-2 rounded-full text-sm font-medium transition-all',
          activeTab === tab.value
            ? 'bg-accent text-white'
            : 'glass glass-hover text-white/70'
        ]"
        @click="activeTab = tab.value"
      >
        {{ tab.label }}
      </button>
    </div>

    <!-- Albums Grid -->
    <div class="grid grid-cols-2 sm:grid-cols-3 md:grid-cols-4 lg:grid-cols-5 xl:grid-cols-6 gap-4">
      <AlbumCard
        v-for="album in filteredAlbums"
        :key="album.id"
        :album="album"
      />
    </div>

    <!-- Empty State -->
    <div v-if="!filteredAlbums.length" class="text-center py-20">
      <svg class="w-20 h-20 text-white/20 mx-auto mb-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
        <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M9 19V6l12-3v13M9 19c0 1.105-1.343 2-3 2s-3-.895-3-2 1.343-2 3-2 3 .895 3 2zm12-3c0 1.105-1.343 2-3 2s-3-.895-3-2 1.343-2 3-2 3 .895 3 2zM9 10l12-3" />
      </svg>
      <p class="text-white/60">暂无专辑</p>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, computed, onMounted } from 'vue'
import Input from '@/components/ui/Input.vue'
import Button from '@/components/ui/Button.vue'
import AlbumCard from '@/components/music/AlbumCard.vue'

const searchQuery = ref('')
const activeTab = ref('all')

const tabs = [
  { label: '全部', value: 'all' },
  { label: '最近添加', value: 'recent' },
  { label: '最常播放', value: 'frequent' },
]

const albums = ref([
  { id: 1, title: '范特西', artist: '周杰伦', cover: 'https://via.placeholder.com/300' },
  { id: 2, title: '叶惠美', artist: '周杰伦', cover: 'https://via.placeholder.com/300' },
  { id: 3, title: '七里香', artist: '周杰伦', cover: 'https://via.placeholder.com/300' },
  { id: 4, title: '十一月的萧邦', artist: '周杰伦', cover: 'https://via.placeholder.com/300' },
  { id: 5, title: '依然范特西', artist: '周杰伦', cover: 'https://via.placeholder.com/300' },
  { id: 6, title: '我很忙', artist: '周杰伦', cover: 'https://via.placeholder.com/300' },
])

const filteredAlbums = computed(() => {
  if (!searchQuery.value) return albums.value
  return albums.value.filter(a =>
    a.title.toLowerCase().includes(searchQuery.value.toLowerCase()) ||
    a.artist.toLowerCase().includes(searchQuery.value.toLowerCase())
  )
})

const refreshLibrary = async () => {
  try {
    const response = await fetch('/api/v1/albums')
    const data = await response.json()
    if (data.items) albums.value = data.items
  } catch (error) {
    console.error('Failed to refresh library:', error)
  }
}

onMounted(refreshLibrary)
</script>
