<template>
  <div class="space-y-6 animate-fade-in">
    <!-- Header -->
    <div class="flex items-center justify-between">
      <h1 class="text-2xl font-bold">音乐榜单</h1>
      <div class="flex items-center gap-2">
        <button
          v-for="source in sources"
          :key="source.id"
          :class="[
            'px-4 py-2 rounded-full text-sm font-medium transition-all',
            activeSource === source.id
              ? 'bg-accent text-white'
              : 'glass glass-hover text-white/70'
          ]"
          @click="activeSource = source.id"
        >
          {{ source.name }}
        </button>
      </div>
    </div>

    <!-- Chart List -->
    <GlassCard>
      <div class="space-y-1">
        <div
          v-for="(song, index) in chartData"
          :key="song.id"
          class="flex items-center gap-4 p-3 rounded-xl hover:bg-white/5 transition-colors group"
        >
          <!-- Rank -->
          <span
            :class="[
              'w-8 text-center font-bold',
              index < 3 ? 'text-accent' : 'text-white/40'
            ]"
          >
            {{ index + 1 }}
          </span>

          <!-- Cover -->
          <img
            :src="song.cover || '/default-cover.png'"
            :alt="song.title"
            class="w-14 h-14 rounded-lg object-cover"
          />

          <!-- Info -->
          <div class="flex-1 min-w-0">
            <p class="font-medium truncate">{{ song.title }}</p>
            <p class="text-sm text-white/60 truncate">{{ song.artist }}</p>
          </div>

          <!-- Actions -->
          <div class="flex items-center gap-2 opacity-0 group-hover:opacity-100 transition-opacity">
            <Button variant="ghost" size="sm" @click="playSong(song)">
              <svg class="w-5 h-5" fill="currentColor" viewBox="0 0 24 24">
                <path d="M8 5v14l11-7z"/>
              </svg>
            </Button>
            <Button variant="secondary" size="sm" @click="subscribeSong(song)">
              订阅
            </Button>
          </div>
        </div>
      </div>
    </GlassCard>
  </div>
</template>

<script setup lang="ts">
import { ref, watch, onMounted } from 'vue'
import GlassCard from '@/components/ui/GlassCard.vue'
import Button from '@/components/ui/Button.vue'

const sources = [
  { id: 'netease', name: '网易云音乐' },
  { id: 'qq_music', name: 'QQ音乐' },
]

const activeSource = ref('netease')
const chartData = ref([])

const API_BASE_URL = 'http://localhost:8000'

const fetchChart = async () => {
  try {
    const response = await fetch(`${API_BASE_URL}/api/v1/chart/${activeSource.value}/new_songs?limit=20`)
    const data = await response.json()
    chartData.value = data.entries || []
  } catch (error) {
    console.error('Failed to fetch chart:', error)
  }
}

const playSong = (song: any) => {
  console.log('Play:', song)
}

const subscribeSong = async (song: any) => {
  try {
    await fetch(`${API_BASE_URL}/api/v1/subscribes`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({
        type: 'artist',
        name: song.artist,
      })
    })
    alert(`已订阅 ${song.artist}`)
  } catch (error) {
    console.error('Failed to subscribe:', error)
  }
}

watch(activeSource, fetchChart)
onMounted(fetchChart)
</script>
