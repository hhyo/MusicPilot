<template>
  <div class="album-list-view p-4 md:p-6 lg:p-8">
    <!-- 页面标题 -->
    <div class="flex items-center justify-between mb-6">
      <div>
        <h1 class="text-3xl font-bold mb-1">专辑</h1>
        <p class="text-white/50">{{ total }} 张专辑</p>
      </div>
      <div class="relative">
        <input 
          v-model="searchQuery"
          type="text" 
          class="input-glass w-64 pl-10" 
          placeholder="搜索专辑..."
        />
        <span class="absolute left-3 top-1/2 -translate-y-1/2 text-white/40">🔍</span>
      </div>
    </div>

    <!-- 加载状态 -->
    <div v-if="loading" class="flex items-center justify-center py-20">
      <div class="w-8 h-8 border-2 border-accent border-t-transparent rounded-full animate-spin"></div>
    </div>

    <!-- 空状态 -->
    <GlassCard v-else-if="!filteredAlbums.length" class="flex flex-col items-center justify-center py-20">
      <div class="text-6xl mb-4">💿</div>
      <h3 class="text-xl font-semibold mb-2">暂无专辑</h3>
      <p class="text-white/50 mb-6">添加音乐后会自动生成专辑列表</p>
      <button class="btn-primary" @click="loadAlbums">
        刷新
      </button>
    </GlassCard>

    <!-- 专辑网格 -->
    <div v-else class="grid grid-cols-2 sm:grid-cols-3 md:grid-cols-4 lg:grid-cols-5 xl:grid-cols-6 gap-4">
      <GlassCard 
        v-for="album in filteredAlbums" 
        :key="album.id"
        hoverable
        padding
        class="flex flex-col items-center text-center cursor-pointer"
        @click="goToAlbumDetail(album.id)"
      >
        <!-- 专辑封面 -->
        <div class="w-24 h-24 rounded-xl overflow-hidden mb-4 shadow-lg">
          <img 
            v-if="album.cover_url" 
            :src="album.cover_url" 
            :alt="album.title"
            class="w-full h-full object-cover"
          />
          <div v-else class="w-full h-full bg-gradient-to-br from-accent/30 to-purple-500/30 flex items-center justify-center text-4xl">
            💿
          </div>
        </div>
        
        <!-- 专辑名称 -->
        <h3 class="font-semibold truncate w-full">{{ album.title }}</h3>
        
        <!-- 年份 -->
        <p class="text-white/50 text-sm mt-1">{{ album.year || '未知年份' }}</p>
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

interface Album {
  id: number
  title: string
  year?: number
  cover_url?: string
}

const router = useRouter()
const loading = ref(false)
const albums = ref<Album[]>([])
const searchQuery = ref('')
const currentPage = ref(1)
const pageSize = ref(30)
const total = ref(0)

// 计算过滤后的专辑
const filteredAlbums = computed(() => {
  if (!searchQuery.value) return albums.value
  const query = searchQuery.value.toLowerCase()
  return albums.value.filter(album => 
    album.title?.toLowerCase().includes(query)
  )
})

const loadAlbums = async () => {
  loading.value = true
  try {
    // TODO: 调用 API 获取专辑列表
    albums.value = [
      { id: 1, title: '七里香', year: 2004, cover_url: '' },
      { id: 2, title: '范特西', year: 2001, cover_url: '' },
      { id: 3, title: '依然', year: 2022, cover_url: '' },
      { id: 4, title: '伟大的渺小', year: 2017, cover_url: '' },
      { id: 5, title: '和自己对话', year: 2015, cover_url: '' },
      { id: 6, title: '学不会', year: 2012, cover_url: '' },
      { id: 7, title: '她说', year: 2011, cover_url: '' },
      { id: 8, title: '曹操', year: 2006, cover_url: '' },
    ]
    total.value = albums.value.length
  } catch (error) {
    console.error('Failed to load albums:', error)
  } finally {
    loading.value = false
  }
}

const goToAlbumDetail = (id: number) => {
  router.push(`/album/${id}`)
}

onMounted(() => {
  loadAlbums()
})
</script>

<style scoped>
.album-list-view {
  min-height: 100%;
}
</style>