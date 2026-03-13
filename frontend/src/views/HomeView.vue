<template>
  <div class="space-y-6 animate-fade-in">
    <!-- Stats Cards -->
    <div class="grid grid-cols-2 md:grid-cols-4 gap-4">
      <GlassCard v-for="stat in stats" :key="stat.label" hoverable>
        <div class="flex items-center gap-4">
          <div :class="['w-12 h-12 rounded-xl flex items-center justify-center', stat.bgColor]">
            <component :is="stat.icon" class="w-6 h-6 text-white" />
          </div>
          <div>
            <p class="text-2xl font-bold">{{ stat.value }}</p>
            <p class="text-sm text-white/60">{{ stat.label }}</p>
          </div>
        </div>
      </GlassCard>
    </div>

    <!-- Quick Actions -->
    <section>
      <h2 class="text-xl font-bold mb-4">快速操作</h2>
      <div class="grid grid-cols-2 md:grid-cols-4 gap-4">
        <button
          v-for="action in quickActions"
          :key="action.label"
          class="glass glass-hover rounded-2xl p-6 text-left transition-all duration-300 hover:scale-[1.02]"
          @click="$router.push(action.path)"
        >
          <component :is="action.icon" class="w-8 h-8 text-accent mb-3" />
          <p class="font-medium">{{ action.label }}</p>
          <p class="text-sm text-white/60">{{ action.desc }}</p>
        </button>
      </div>
    </section>

    <!-- Recent Albums -->
    <section>
      <div class="flex items-center justify-between mb-4">
        <h2 class="text-xl font-bold">最近添加</h2>
        <router-link to="/library" class="text-accent hover:text-accent-hover text-sm">
          查看全部
        </router-link>
      </div>
      <div class="grid grid-cols-2 sm:grid-cols-3 md:grid-cols-4 lg:grid-cols-5 gap-4">
        <AlbumCard
          v-for="album in recentAlbums"
          :key="album.id"
          :album="album"
        />
      </div>
    </section>

    <!-- Chart Preview -->
    <section>
      <div class="flex items-center justify-between mb-4">
        <h2 class="text-xl font-bold">热门榜单</h2>
        <router-link to="/chart" class="text-accent hover:text-accent-hover text-sm">
          查看全部
        </router-link>
      </div>
      <GlassCard>
        <div class="space-y-3">
          <div
            v-for="(song, index) in chartPreview"
            :key="song.id"
            class="flex items-center gap-4 p-3 rounded-xl hover:bg-white/5 transition-colors cursor-pointer"
          >
            <span class="w-8 text-center text-white/40 font-bold">{{ index + 1 }}</span>
            <img :src="song.cover" :alt="song.title" class="w-12 h-12 rounded-lg object-cover" />
            <div class="flex-1 min-w-0">
              <p class="font-medium truncate">{{ song.title }}</p>
              <p class="text-sm text-white/60 truncate">{{ song.artist }}</p>
            </div>
            <Button variant="ghost" size="sm" @click="subscribeSong(song)">
              订阅
            </Button>
          </div>
        </div>
      </GlassCard>
    </section>
  </div>
</template>

<script setup lang="ts">
import { ref, onMounted } from 'vue'
import GlassCard from '@/components/ui/GlassCard.vue'
import Button from '@/components/ui/Button.vue'
import AlbumCard from '@/components/music/AlbumCard.vue'

// Stats
const stats = ref([
  { label: '艺术家', value: 128, icon: 'UsersIcon', bgColor: 'bg-blue-500' },
  { label: '专辑', value: 512, icon: 'DiscIcon', bgColor: 'bg-purple-500' },
  { label: '歌曲', value: 2048, icon: 'MusicIcon', bgColor: 'bg-green-500' },
  { label: '订阅', value: 16, icon: 'BellIcon', bgColor: 'bg-orange-500' },
])

// Quick Actions
const quickActions = [
  { label: '搜索音乐', desc: '查找艺术家、专辑', icon: 'SearchIcon', path: '/search' },
  { label: '音乐榜单', desc: '查看热门榜单', icon: 'ChartIcon', path: '/chart' },
  { label: '我的订阅', desc: '管理音乐订阅', icon: 'BellIcon', path: '/subscribe' },
  { label: '下载管理', desc: '查看下载任务', icon: 'DownloadIcon', path: '/download' },
]

// Recent Albums
const recentAlbums = ref([
  { id: 1, title: '范特西', artist: '周杰伦', cover: 'https://via.placeholder.com/300' },
  { id: 2, title: '叶惠美', artist: '周杰伦', cover: 'https://via.placeholder.com/300' },
  { id: 3, title: '七里香', artist: '周杰伦', cover: 'https://via.placeholder.com/300' },
  { id: 4, title: '十一月的萧邦', artist: '周杰伦', cover: 'https://via.placeholder.com/300' },
  { id: 5, title: '依然范特西', artist: '周杰伦', cover: 'https://via.placeholder.com/300' },
])

// Chart Preview
const chartPreview = ref([
  { id: 1, title: '稻香', artist: '周杰伦', cover: 'https://via.placeholder.com/100' },
  { id: 2, title: '晴天', artist: '周杰伦', cover: 'https://via.placeholder.com/100' },
  { id: 3, title: '夜曲', artist: '周杰伦', cover: 'https://via.placeholder.com/100' },
  { id: 4, title: '青花瓷', artist: '周杰伦', cover: 'https://via.placeholder.com/100' },
  { id: 5, title: '告白气球', artist: '周杰伦', cover: 'https://via.placeholder.com/100' },
])

const subscribeSong = (song: any) => {
  console.log('Subscribe:', song)
}

onMounted(async () => {
  // Fetch real data from API
  try {
    const response = await fetch('/api/v1/albums/recent?limit=5')
    const data = await response.json()
    if (data.length) {
      recentAlbums.value = data
    }
  } catch (error) {
    console.error('Failed to fetch recent albums:', error)
  }
})
</script>
