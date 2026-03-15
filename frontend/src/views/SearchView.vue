<template>
  <div class="search-view p-4 md:p-6 lg:p-8">
    <!-- 页面标题 -->
    <div class="mb-6">
      <h1 class="text-3xl font-bold mb-2">搜索音乐</h1>
      <p class="text-white/50">搜索 MusicBrainz 元数据数据库</p>
    </div>

    <!-- 搜索框 -->
    <div class="mb-8">
      <div class="flex gap-4">
        <div class="flex-1 relative">
          <input
            v-model="searchQuery"
            type="text"
            class="w-full px-4 py-3 rounded-xl bg-white/5 border border-white/10 focus:border-accent focus:outline-none transition-colors"
            placeholder="输入艺术家、专辑或歌曲名称..."
            @keyup.enter="handleSearch"
          />
          <span class="absolute right-4 top-1/2 -translate-y-1/2 text-white/40">⌨️</span>
        </div>
        <button
          class="px-6 py-3 rounded-xl bg-accent hover:bg-accent/80 transition-colors font-medium flex items-center gap-2"
          :disabled="loading"
          @click="handleSearch"
        >
          <span v-if="loading" class="animate-spin">⏳</span>
          <span v-else>🔍</span>
          {{ loading ? '搜索中...' : '搜索' }}
        </button>
      </div>
    </div>

    <!-- 搜索结果 -->
    <div v-if="hasSearched">
      <!-- Tab 切换 -->
      <div class="flex gap-2 mb-6">
        <button
          v-for="tab in tabs"
          :key="tab.value"
          class="px-4 py-2 rounded-lg transition-colors"
          :class="activeTab === tab.value ? 'bg-accent text-white' : 'bg-white/5 text-white/60 hover:bg-white/10'"
          @click="activeTab = tab.value"
        >
          {{ tab.label }} ({{ getTabCount(tab.value) }})
        </button>
      </div>

      <!-- 加载状态 -->
      <div v-if="loading" class="flex items-center justify-center py-20">
        <div class="w-8 h-8 border-2 border-accent border-t-transparent rounded-full animate-spin"></div>
      </div>

      <!-- 艺术家结果 -->
      <div v-else-if="activeTab === 'artists'" class="grid grid-cols-2 md:grid-cols-3 lg:grid-cols-4 gap-4">
        <GlassCard
          v-for="artist in searchResults.artists"
          :key="artist.id"
          hoverable
          class="p-4 text-center"
        >
          <div class="w-20 h-20 mx-auto mb-3 rounded-full bg-gradient-to-br from-accent/30 to-accent/10 flex items-center justify-center text-3xl">
            🎤
          </div>
          <h3 class="font-semibold mb-1 truncate">{{ artist.name }}</h3>
          <p class="text-sm text-white/50">{{ artist.country || '未知地区' }}</p>
          <button
            class="mt-3 px-4 py-1.5 rounded-lg bg-accent/20 hover:bg-accent/30 text-accent text-sm transition-colors"
            @click="subscribeArtist(artist)"
          >
            ➕ 订阅
          </button>
        </GlassCard>
      </div>

      <!-- 专辑结果 -->
      <div v-else-if="activeTab === 'albums'" class="grid grid-cols-2 md:grid-cols-3 lg:grid-cols-4 gap-4">
        <GlassCard
          v-for="album in searchResults.albums"
          :key="album.id"
          hoverable
          class="p-4"
        >
          <div class="aspect-square mb-3 rounded-lg bg-gradient-to-br from-accent/30 to-accent/10 flex items-center justify-center text-4xl">
            💿
          </div>
          <h3 class="font-semibold mb-1 truncate">{{ album.title }}</h3>
          <p class="text-sm text-white/50 truncate">{{ album.artist }}</p>
          <button
            class="mt-3 w-full py-1.5 rounded-lg bg-accent/20 hover:bg-accent/30 text-accent text-sm transition-colors"
            @click="subscribeAlbum(album)"
          >
            ➕ 订阅
          </button>
        </GlassCard>
      </div>

      <!-- 歌曲结果 -->
      <div v-else-if="activeTab === 'tracks'" class="space-y-2">
        <GlassCard
          v-for="track in searchResults.tracks"
          :key="track.id"
          hoverable
          class="p-4 flex items-center gap-4"
        >
          <div class="w-12 h-12 rounded-lg bg-gradient-to-br from-accent/30 to-accent/10 flex items-center justify-center text-xl">
            🎵
          </div>
          <div class="flex-1 min-w-0">
            <h3 class="font-medium truncate">{{ track.title }}</h3>
            <p class="text-sm text-white/50 truncate">{{ track.artist }} - {{ track.album }}</p>
          </div>
          <button
            class="px-4 py-1.5 rounded-lg bg-accent/20 hover:bg-accent/30 text-accent text-sm transition-colors"
            @click="subscribeTrack(track)"
          >
            ➕ 订阅
          </button>
        </GlassCard>
      </div>

      <!-- 空结果 -->
      <div v-if="!loading && getTabCount(activeTab) === 0" class="text-center py-20">
        <div class="text-6xl mb-4">🔍</div>
        <p class="text-white/50">未找到相关结果</p>
      </div>
    </div>

    <!-- 初始状态 -->
    <div v-else class="text-center py-20">
      <div class="text-6xl mb-4">🎵</div>
      <p class="text-white/50">输入关键词开始搜索 MusicBrainz</p>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, reactive } from 'vue'
import GlassCard from '@/components/ui/GlassCard.vue'
import { subscribeApi } from '@/api/client'

const searchQuery = ref('')
const loading = ref(false)
const hasSearched = ref(false)
const activeTab = ref('artists')

const tabs = [
  { label: '艺术家', value: 'artists' },
  { label: '专辑', value: 'albums' },
  { label: '歌曲', value: 'tracks' },
]

const searchResults = reactive({
  artists: [] as any[],
  albums: [] as any[],
  tracks: [] as any[],
})

const getTabCount = (tab: string) => {
  return searchResults[tab as keyof typeof searchResults]?.length || 0
}

const handleSearch = async () => {
  if (!searchQuery.value.trim()) return
  
  loading.value = true
  hasSearched.value = true
  
  try {
    // TODO: 调用 MusicBrainz 搜索 API
    // const res = await searchApi.search(searchQuery.value)
    
    // 模拟搜索结果
    searchResults.artists = [
      { id: '1', name: '周杰伦', country: 'Taiwan' },
      { id: '2', name: '林俊杰', country: 'Singapore' },
    ].filter(a => a.name.includes(searchQuery.value))
    
    searchResults.albums = [
      { id: '1', title: '范特西', artist: '周杰伦' },
      { id: '2', title: '七里香', artist: '周杰伦' },
    ].filter(a => a.title.includes(searchQuery.value) || a.artist.includes(searchQuery.value))
    
    searchResults.tracks = [
      { id: '1', title: '稻香', artist: '周杰伦', album: '魔杰座' },
      { id: '2', title: '晴天', artist: '周杰伦', album: '叶惠美' },
    ].filter(t => t.title.includes(searchQuery.value) || t.artist.includes(searchQuery.value))
  } catch (error) {
    console.error('Search failed:', error)
  } finally {
    loading.value = false
  }
}

const subscribeArtist = async (artist: any) => {
  try {
    await subscribeApi.create({
      type: 'artist',
      name: artist.name,
      musicbrainz_id: artist.id,
    })
    alert(`已订阅艺术家: ${artist.name}`)
  } catch (error) {
    console.error('Subscribe failed:', error)
  }
}

const subscribeAlbum = async (album: any) => {
  try {
    await subscribeApi.create({
      type: 'album',
      name: album.title,
      musicbrainz_id: album.id,
    })
    alert(`已订阅专辑: ${album.title}`)
  } catch (error) {
    console.error('Subscribe failed:', error)
  }
}

const subscribeTrack = async (track: any) => {
  try {
    await subscribeApi.create({
      type: 'track',
      name: track.title,
      musicbrainz_id: track.id,
    })
    alert(`已订阅歌曲: ${track.title}`)
  } catch (error) {
    console.error('Subscribe failed:', error)
  }
}
</script>
