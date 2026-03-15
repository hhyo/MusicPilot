<template>
  <div class="discover-view p-4 md:p-6 lg:p-8">
    <!-- 页面标题 -->
    <div class="mb-6">
      <h1 class="text-3xl font-bold mb-2">发现音乐</h1>
      <p class="text-white/50">搜索、榜单、歌单推荐</p>
    </div>

    <!-- Tab 切换 -->
    <div class="flex gap-2 mb-6">
      <button
        v-for="tab in tabs"
        :key="tab.value"
        class="px-4 py-2 rounded-lg transition-colors"
        :class="activeTab === tab.value ? 'bg-accent text-white' : 'bg-white/5 text-white/60 hover:bg-white/10'"
        @click="activeTab = tab.value"
      >
        {{ tab.label }}
      </button>
    </div>

    <!-- 搜索 -->
    <div v-if="activeTab === 'search'" class="space-y-6">
      <!-- 搜索框 -->
      <div class="flex gap-4">
        <div class="flex-1 relative">
          <input
            v-model="searchQuery"
            type="text"
            class="w-full px-4 py-3 rounded-xl bg-white/5 border border-white/10 focus:border-accent focus:outline-none transition-colors"
            placeholder="输入艺术家、专辑或歌曲名称..."
            @keyup.enter="handleSearch"
          />
        </div>
        <button
          class="px-6 py-3 rounded-xl bg-accent hover:bg-accent/80 transition-colors font-medium"
          :disabled="searchLoading"
          @click="handleSearch"
        >
          {{ searchLoading ? '搜索中...' : '搜索' }}
        </button>
      </div>

      <!-- 搜索结果分类 -->
      <div v-if="hasSearched" class="space-y-6">
        <!-- 艺术家 -->
        <section v-if="searchResults.artists.length">
          <h2 class="text-xl font-bold mb-3">艺术家</h2>
          <div class="grid grid-cols-2 md:grid-cols-4 lg:grid-cols-6 gap-4">
            <GlassCard
              v-for="artist in searchResults.artists"
              :key="artist.id"
              hoverable
              class="p-4 text-center"
              @click="subscribeArtist(artist)"
            >
              <div class="w-16 h-16 mx-auto mb-2 rounded-full bg-gradient-to-br from-accent/30 to-accent/10 flex items-center justify-center text-2xl">
                🎤
              </div>
              <h3 class="font-medium text-sm truncate">{{ artist.name }}</h3>
              <button class="mt-2 text-xs text-accent">➕ 订阅</button>
            </GlassCard>
          </div>
        </section>

        <!-- 专辑 -->
        <section v-if="searchResults.albums.length">
          <h2 class="text-xl font-bold mb-3">专辑</h2>
          <div class="grid grid-cols-2 md:grid-cols-4 lg:grid-cols-6 gap-4">
            <GlassCard
              v-for="album in searchResults.albums"
              :key="album.id"
              hoverable
              class="p-4"
              @click="subscribeAlbum(album)"
            >
              <div class="aspect-square mb-2 rounded-lg bg-gradient-to-br from-accent/30 to-accent/10 flex items-center justify-center text-3xl">
                💿
              </div>
              <h3 class="font-medium text-sm truncate">{{ album.title }}</h3>
              <p class="text-xs text-white/50 truncate">{{ album.artist }}</p>
              <button class="mt-2 text-xs text-accent">➕ 订阅</button>
            </GlassCard>
          </div>
        </section>

        <!-- 歌曲 -->
        <section v-if="searchResults.tracks.length">
          <h2 class="text-xl font-bold mb-3">歌曲</h2>
          <div class="space-y-2">
            <GlassCard
              v-for="track in searchResults.tracks"
              :key="track.id"
              hoverable
              class="p-3 flex items-center gap-3"
            >
              <div class="w-10 h-10 rounded-lg bg-gradient-to-br from-accent/30 to-accent/10 flex items-center justify-center">
                🎵
              </div>
              <div class="flex-1 min-w-0">
                <h3 class="font-medium truncate">{{ track.title }}</h3>
                <p class="text-sm text-white/50 truncate">{{ track.artist }}</p>
              </div>
              <button class="text-xs text-accent" @click="subscribeTrack(track)">➕ 订阅</button>
            </GlassCard>
          </div>
        </section>
      </div>

      <!-- 初始状态 -->
      <div v-else class="text-center py-20">
        <div class="text-6xl mb-4">🔍</div>
        <p class="text-white/50">输入关键词搜索 MusicBrainz</p>
      </div>
    </div>

    <!-- 榜单 -->
    <div v-else-if="activeTab === 'charts'" class="space-y-6">
      <!-- 榜单来源选择 -->
      <div class="flex gap-2">
        <button
          v-for="source in chartSources"
          :key="source.id"
          class="px-4 py-2 rounded-lg transition-colors"
          :class="activeChartSource === source.id ? 'bg-accent text-white' : 'bg-white/5 text-white/60 hover:bg-white/10'"
          @click="activeChartSource = source.id"
        >
          {{ source.name }}
        </button>
      </div>

      <!-- 歌曲列表 -->
      <GlassCard>
        <div class="space-y-1">
          <div
            v-for="(song, index) in chartSongs"
            :key="index"
            class="flex items-center gap-4 p-3 rounded-xl hover:bg-white/5 transition-colors"
          >
            <span class="w-8 text-center font-bold" :class="index < 3 ? 'text-accent' : 'text-white/40'">
              {{ index + 1 }}
            </span>
            <div class="w-12 h-12 rounded-lg bg-gradient-to-br from-accent/30 to-accent/10 flex items-center justify-center">
              🎵
            </div>
            <div class="flex-1 min-w-0">
              <p class="font-medium truncate">{{ song.title }}</p>
              <p class="text-sm text-white/50 truncate">{{ song.artist }}</p>
            </div>
            <button class="text-xs text-accent" @click="subscribeChartSong(song)">➕ 订阅</button>
          </div>
        </div>
      </GlassCard>
    </div>

    <!-- 歌单推荐 -->
    <div v-else-if="activeTab === 'playlists'" class="space-y-6">
      <div class="grid grid-cols-2 md:grid-cols-3 lg:grid-cols-4 gap-4">
        <GlassCard
          v-for="playlist in recommendedPlaylists"
          :key="playlist.id"
          hoverable
          class="p-4"
        >
          <div class="aspect-square mb-3 rounded-lg bg-gradient-to-br from-accent/30 to-accent/10 flex items-center justify-center text-4xl">
            📀
          </div>
          <h3 class="font-semibold mb-1 truncate">{{ playlist.name }}</h3>
          <p class="text-sm text-white/50 truncate">{{ playlist.description }}</p>
          <div class="mt-3 flex gap-2">
            <button class="flex-1 py-1.5 rounded-lg bg-accent/20 text-accent text-sm" @click="viewPlaylist(playlist)">查看</button>
            <button class="flex-1 py-1.5 rounded-lg bg-white/10 text-white/70 text-sm" @click="subscribePlaylist(playlist)">订阅</button>
          </div>
        </GlassCard>
      </div>
    </div>

    <!-- 站点浏览 -->
    <div v-else-if="activeTab === 'sites'" class="space-y-6">
      <div class="flex justify-between items-center">
        <h2 class="text-xl font-bold">PT 站点</h2>
        <router-link to="/site" class="text-accent text-sm">管理站点 ➜</router-link>
      </div>
      <div class="grid grid-cols-2 md:grid-cols-3 lg:grid-cols-4 gap-4">
        <GlassCard
          v-for="site in sites"
          :key="site.id"
          hoverable
          class="p-4"
          @click="browseSite(site)"
        >
          <div class="flex items-center gap-3 mb-3">
            <div class="w-10 h-10 rounded-lg bg-accent/20 flex items-center justify-center text-xl">
              🌐
            </div>
            <div>
              <h3 class="font-semibold">{{ site.name }}</h3>
              <p class="text-xs text-white/50">{{ site.type }}</p>
            </div>
          </div>
          <div class="flex items-center gap-2 text-sm">
            <span class="px-2 py-0.5 rounded bg-green-500/20 text-green-400 text-xs">在线</span>
            <span class="text-white/50">{{ site.torrent_count || 0 }} 种子</span>
          </div>
        </GlassCard>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, reactive, onMounted } from 'vue'
import { useRouter } from 'vue-router'
import GlassCard from '@/components/ui/GlassCard.vue'
import { subscribeApi, chartApi, siteApi, artistApi, albumApi, trackApi } from '@/api/client'

const router = useRouter()

// Tabs
const tabs = [
  { label: '🔍 搜索', value: 'search' },
  { label: '📊 榜单', value: 'charts' },
  { label: '🎵 歌单', value: 'playlists' },
  { label: '🌐 站点', value: 'sites' },
]
const activeTab = ref('search')

// Search
const searchQuery = ref('')
const searchLoading = ref(false)
const hasSearched = ref(false)
const searchResults = reactive({
  artists: [] as any[],
  albums: [] as any[],
  tracks: [] as any[],
})

const handleSearch = async () => {
  if (!searchQuery.value.trim()) return
  searchLoading.value = true
  hasSearched.value = true
  
  try {
    // 同时搜索艺术家、专辑、歌曲
    const [artistRes, albumRes, trackRes] = await Promise.all([
      artistApi.list({ limit: 20 }),
      albumApi.list({ limit: 20 }),
      trackApi.list({ limit: 20 }),
    ])
    
    // 前端过滤匹配的结果
    const keyword = searchQuery.value.toLowerCase()
    searchResults.artists = (artistRes.data || []).filter((a: any) => 
      a.name.toLowerCase().includes(keyword)
    )
    searchResults.albums = (albumRes.data || []).filter((a: any) => 
      a.title.toLowerCase().includes(keyword)
    )
    searchResults.tracks = (trackRes.data || []).filter((t: any) => 
      t.title.toLowerCase().includes(keyword)
    )
  } catch (error) {
    console.error('Search failed:', error)
    searchResults.artists = []
    searchResults.albums = []
    searchResults.tracks = []
  } finally {
    searchLoading.value = false
  }
}

const subscribeArtist = async (artist: any) => {
  try {
    await subscribeApi.create({ type: 'artist', name: artist.name, musicbrainz_id: artist.id })
    alert(`已订阅艺术家: ${artist.name}`)
  } catch (error) {
    console.error('Subscribe failed:', error)
  }
}

const subscribeAlbum = async (album: any) => {
  try {
    await subscribeApi.create({ type: 'album', name: album.title, musicbrainz_id: album.id })
    alert(`已订阅专辑: ${album.title}`)
  } catch (error) {
    console.error('Subscribe failed:', error)
  }
}

const subscribeTrack = async (track: any) => {
  try {
    await subscribeApi.create({ type: 'track', name: track.title, musicbrainz_id: track.id })
    alert(`已订阅歌曲: ${track.title}`)
  } catch (error) {
    console.error('Subscribe failed:', error)
  }
}

// Charts
const chartSources = [
  { id: 'netease', name: '网易云音乐' },
  { id: 'qq_music', name: 'QQ音乐' },
]
const activeChartSource = ref('netease')
const chartSongs = ref<any[]>([])

const loadChart = async () => {
  try {
    const res = await chartApi.get(activeChartSource.value, 'new_songs', { limit: 20 })
    chartSongs.value = res.entries || []
  } catch (error) {
    console.error('Load chart failed:', error)
  }
}

const subscribeChartSong = async (song: any) => {
  try {
    await subscribeApi.create({ type: 'artist', name: song.artist })
    alert(`已订阅: ${song.artist}`)
  } catch (error) {
    console.error('Subscribe failed:', error)
  }
}

// Playlists
const recommendedPlaylists = ref([
  { id: 1, name: '华语经典', description: '经典华语歌曲合集' },
  { id: 2, name: '欧美流行', description: '最新欧美流行音乐' },
  { id: 3, name: '日语精选', description: '精选日语歌曲' },
  { id: 4, name: 'K-Pop热门', description: '韩国流行音乐' },
])

const viewPlaylist = (playlist: any) => {
  router.push(`/playlist/${playlist.id}`)
}

const subscribePlaylist = async (playlist: any) => {
  try {
    await subscribeApi.create({ type: 'playlist', name: playlist.name })
    alert(`已订阅歌单: ${playlist.name}`)
  } catch (error) {
    console.error('Subscribe failed:', error)
  }
}

// Sites
const sites = ref<any[]>([])

const loadSites = async () => {
  try {
    const res = await siteApi.list()
    sites.value = res.sites || []
  } catch (error) {
    console.error('Load sites failed:', error)
  }
}

const browseSite = (site: any) => {
  router.push(`/site`)
}

// Init
onMounted(() => {
  loadChart()
  loadSites()
})
</script>
