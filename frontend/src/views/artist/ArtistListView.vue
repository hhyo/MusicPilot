<template>
  <div class="artist-list-view p-4 md:p-6 lg:p-8">
    <!-- 页面标题 -->
    <div class="flex items-center justify-between mb-6">
      <div>
        <h1 class="text-3xl font-bold mb-1">艺术家</h1>
        <p class="text-white/50">{{ total }} 位艺术家</p>
      </div>
      <div class="relative">
        <input 
          v-model="searchQuery"
          type="text" 
          class="input-glass w-64 pl-10" 
          placeholder="搜索艺术家..."
        />
        <span class="absolute left-3 top-1/2 -translate-y-1/2 text-white/40">🔍</span>
      </div>
    </div>

    <!-- 加载状态 -->
    <div v-if="loading" class="flex items-center justify-center py-20">
      <div class="w-8 h-8 border-2 border-accent border-t-transparent rounded-full animate-spin"></div>
    </div>

    <!-- 空状态 -->
    <GlassCard v-else-if="!filteredArtists.length" class="flex flex-col items-center justify-center py-20">
      <div class="text-6xl mb-4">👤</div>
      <h3 class="text-xl font-semibold mb-2">暂无艺术家</h3>
      <p class="text-white/50 mb-6">添加音乐后会自动生成艺术家列表</p>
      <button class="btn-primary" @click="loadArtists">
        刷新
      </button>
    </GlassCard>

    <!-- 艺术家网格 -->
    <div v-else class="grid grid-cols-2 sm:grid-cols-3 md:grid-cols-4 lg:grid-cols-5 xl:grid-cols-6 gap-4">
      <GlassCard 
        v-for="artist in filteredArtists" 
        :key="artist.id"
        hoverable
        padding
        class="flex flex-col items-center text-center cursor-pointer"
        @click="goToArtistDetail(artist.id)"
      >
        <!-- 艺术家头像 -->
        <div class="w-24 h-24 rounded-full overflow-hidden mb-4 bg-gradient-to-br from-accent/30 to-accent/10">
          <img 
            v-if="artist.image_url" 
            :src="artist.image_url" 
            :alt="artist.name"
            class="w-full h-full object-cover"
          />
          <div v-else class="w-full h-full flex items-center justify-center text-4xl text-accent">
            {{ artist.name?.charAt(0) }}
          </div>
        </div>
        
        <!-- 艺术家名称 -->
        <h3 class="font-semibold truncate w-full">{{ artist.name }}</h3>
        
        <!-- 歌曲数量 -->
        <p class="text-white/50 text-sm mt-1">{{ artist.trackCount || 0 }} 首歌曲</p>
      </GlassCard>
    </div>

    <!-- 分页 -->
    <div v-if="total > pageSize" class="flex justify-center mt-8">
      <div class="flex items-center gap-2">
        <button 
          class="btn-ghost"
          :disabled="currentPage === 1"
          @click="currentPage--"
        >
          上一页
        </button>
        <span class="text-white/60 px-4">
          {{ currentPage }} / {{ Math.ceil(total / pageSize) }}
        </span>
        <button 
          class="btn-ghost"
          :disabled="currentPage >= Math.ceil(total / pageSize)"
          @click="currentPage++"
        >
          下一页
        </button>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, computed, onMounted } from 'vue'
import { useRouter } from 'vue-router'
import GlassCard from '@/components/ui/GlassCard.vue'

interface Artist {
  id: number
  name: string
  image_url?: string
  trackCount?: number
}

const router = useRouter()
const loading = ref(false)
const artists = ref<Artist[]>([])
const searchQuery = ref('')
const currentPage = ref(1)
const pageSize = ref(30)
const total = ref(0)

// 计算过滤后的艺术家
const filteredArtists = computed(() => {
  if (!searchQuery.value) return artists.value
  const query = searchQuery.value.toLowerCase()
  return artists.value.filter(artist => 
    artist.name?.toLowerCase().includes(query)
  )
})

const loadArtists = async () => {
  loading.value = true
  try {
    // TODO: 调用 API 获取艺术家列表
    artists.value = [
      { id: 1, name: '周杰伦', image_url: '', trackCount: 234 },
      { id: 2, name: '林俊杰', image_url: '', trackCount: 156 },
      { id: 3, name: '陈奕迅', image_url: '', trackCount: 189 },
      { id: 4, name: '张学友', image_url: '', trackCount: 267 },
      { id: 5, name: '邓紫棋', image_url: '', trackCount: 98 },
      { id: 6, name: 'Ed Sheeran', image_url: '', trackCount: 145 },
      { id: 7, name: 'Taylor Swift', image_url: '', trackCount: 178 },
      { id: 8, name: 'The Weeknd', image_url: '', trackCount: 123 },
    ]
    total.value = artists.value.length
  } catch (error) {
    console.error('Failed to load artists:', error)
  } finally {
    loading.value = false
  }
}

const goToArtistDetail = (id: number) => {
  router.push(`/artist/${id}`)
}

onMounted(() => {
  loadArtists()
})
</script>

<style scoped>
.artist-list-view {
  min-height: 100%;
}
</style>