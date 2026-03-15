<template>
  <div class="download-view p-4 md:p-6 lg:p-8">
    <!-- 页面标题 -->
    <div class="flex flex-col sm:flex-row sm:items-center justify-between gap-4 mb-6">
      <div>
        <h1 class="text-3xl font-bold mb-1">下载管理</h1>
        <p class="text-white/50">管理您的下载任务</p>
      </div>
      <div class="flex items-center gap-3">
        <button class="btn-secondary flex items-center gap-2" @click="refresh" :disabled="loading">
          <span :class="{ 'animate-spin': loading }">🔄</span>
          <span class="hidden sm:inline">刷新</span>
        </button>
        <button class="btn-primary flex items-center gap-2" @click="showSearchModal = true">
          <span>⬇️</span>
          <span class="hidden sm:inline">添加下载</span>
        </button>
      </div>
    </div>

    <!-- 下载统计 -->
    <div class="grid grid-cols-2 md:grid-cols-4 gap-4 mb-6">
      <GlassCard class="text-center">
        <div class="text-2xl font-bold text-accent">{{ stats.total }}</div>
        <div class="text-white/50 text-sm">总下载量</div>
      </GlassCard>
      <GlassCard class="text-center">
        <div class="text-2xl font-bold text-green-400">{{ stats.completed }}</div>
        <div class="text-white/50 text-sm">成功</div>
      </GlassCard>
      <GlassCard class="text-center">
        <div class="text-2xl font-bold text-red-400">{{ stats.failed }}</div>
        <div class="text-white/50 text-sm">失败</div>
      </GlassCard>
      <GlassCard class="text-center">
        <div class="text-2xl font-bold text-blue-400">{{ successRate }}%</div>
        <div class="text-white/50 text-sm">成功率</div>
      </GlassCard>
    </div>

    <!-- Tab 切换 -->
    <div class="flex flex-wrap gap-2 mb-6 p-2 glass rounded-2xl">
      <button
        v-for="tab in tabs"
        :key="tab.value"
        class="flex-1 min-w-[80px] py-2.5 px-4 rounded-xl transition-all duration-300 font-medium text-sm"
        :class="activeTab === tab.value 
          ? 'bg-accent text-white shadow-lg shadow-accent/25' 
          : 'text-white/60 hover:text-white hover:bg-white/10'"
        @click="activeTab = tab.value"
      >
        {{ tab.label }}
        <span v-if="tab.count" class="ml-1 text-xs opacity-70">({{ tab.count }})</span>
      </button>
    </div>

    <!-- 加载状态 -->
    <div v-if="loading" class="flex items-center justify-center py-20">
      <div class="w-8 h-8 border-2 border-accent border-t-transparent rounded-full animate-spin"></div>
    </div>

    <!-- 空状态 -->
    <GlassCard v-else-if="displayTasks.length === 0" class="flex flex-col items-center justify-center py-20">
      <div class="text-6xl mb-4">{{ emptyIcon }}</div>
      <h3 class="text-xl font-semibold mb-2">{{ emptyText }}</h3>
      <button v-if="activeTab === 'downloading'" class="btn-primary mt-4" @click="showSearchModal = true">
        添加下载
      </button>
    </GlassCard>

    <!-- 任务列表 -->
    <div v-else class="space-y-3">
      <GlassCard 
        v-for="task in displayTasks" 
        :key="task.task_id || task.source_id"
        hoverable
        class="flex flex-col gap-4"
      >
        <div class="flex items-start gap-4">
          <!-- 封面/图标 -->
          <div class="w-12 h-12 rounded-xl bg-gradient-to-br from-accent/30 to-accent/10 flex items-center justify-center text-2xl shrink-0">
            🎵
          </div>
          
          <!-- 信息 -->
          <div class="flex-1 min-w-0">
            <h3 class="font-semibold truncate">{{ task.title || task.task_id }}</h3>
            <p class="text-white/50 text-sm truncate">{{ task.artist || '-' }} · {{ task.album || '-' }}</p>
          </div>
          
          <!-- 状态标签 -->
          <span 
            class="shrink-0 px-3 py-1 rounded-full text-xs font-medium"
            :class="statusClass(task.status || (task.progress !== undefined ? 'downloading' : 'completed'))"
          >
            {{ statusText(task.status || (task.progress !== undefined ? 'downloading' : 'completed')) }}
          </span>
        </div>
        
        <!-- 进度条 -->
        <div v-if="task.progress !== undefined" class="space-y-2">
          <div class="flex justify-between text-sm text-white/60">
            <span>{{ formatFileSize(task.downloaded_bytes || 0) }} / {{ formatFileSize(task.total_bytes || 0) }}</span>
            <span>{{ Math.round((task.progress || 0) * 100) }}%</span>
          </div>
          <div class="h-2 bg-white/10 rounded-full overflow-hidden">
            <div 
              class="h-full bg-accent transition-all duration-300 rounded-full"
              :style="{ width: `${(task.progress || 0) * 100}%` }"
            ></div>
          </div>
        </div>
        
        <!-- 操作按钮 -->
        <div class="flex items-center justify-between">
          <div class="text-sm text-white/40">
            <span v-if="task.quality">{{ qualityMap[task.quality] || task.quality }}</span>
            <span v-if="task.created_at" class="ml-2">{{ formatDate(task.created_at) }}</span>
          </div>
          <div class="flex items-center gap-2">
            <button 
              v-if="task.progress !== undefined"
              class="btn-ghost text-sm" 
              @click="cancelDownload(task.task_id)"
            >
              取消
            </button>
            <button 
              v-else-if="task.status === 'failed'"
              class="btn-ghost text-sm" 
              @click="retryDownload(task)"
            >
              🔄 重试
            </button>
            <button 
              v-else-if="task.status === 'completed' || task.file_path"
              class="btn-ghost text-sm" 
              @click="playTrack(task.file_path)"
            >
              ▶️ 播放
            </button>
          </div>
        </div>
      </GlassCard>
    </div>

    <!-- 搜索下载弹窗 -->
    <div 
      v-if="showSearchModal" 
      class="fixed inset-0 bg-black/50 backdrop-blur-sm flex items-center justify-center z-50 p-4"
      @click.self="showSearchModal = false"
    >
      <GlassCard class="w-full max-w-lg p-6 animate-slide-up max-h-[90vh] overflow-y-auto">
        <h2 class="text-xl font-semibold mb-6">搜索并下载</h2>
        <div class="space-y-4">
          <div>
            <label class="block text-white/70 text-sm mb-2">关键词</label>
            <input 
              v-model="searchForm.keyword" 
              type="text" 
              class="input-glass w-full" 
              placeholder="歌曲名、艺术家或专辑"
            />
          </div>
          <div>
            <label class="block text-white/70 text-sm mb-2">来源</label>
            <select v-model="searchForm.source" class="input-glass w-full">
              <option v-for="opt in sourceOptions" :key="opt.value" :value="opt.value">
                {{ opt.label }}
              </option>
            </select>
          </div>
          <div>
            <label class="block text-white/70 text-sm mb-2">音质</label>
            <select v-model="searchForm.quality" class="input-glass w-full">
              <option v-for="opt in qualityOptions" :key="opt.value" :value="opt.value">
                {{ opt.label }}
              </option>
            </select>
          </div>
          <div>
            <label class="block text-white/70 text-sm mb-2">数量</label>
            <input 
              v-model.number="searchForm.limit" 
              type="number" 
              min="1" 
              max="20"
              class="input-glass w-full" 
            />
          </div>
        </div>
        <div class="flex justify-end gap-3 mt-6">
          <button class="btn-secondary" @click="showSearchModal = false">取消</button>
          <button class="btn-primary" @click="handleSearchAndDownload" :loading="searching">
            搜索并下载
          </button>
        </div>
      </GlassCard>
    </div>

    <!-- URL 下载弹窗 -->
    <div 
      v-if="showUrlModal" 
      class="fixed inset-0 bg-black/50 backdrop-blur-sm flex items-center justify-center z-50 p-4"
      @click.self="showUrlModal = false"
    >
      <GlassCard class="w-full max-w-lg p-6 animate-slide-up max-h-[90vh] overflow-y-auto">
        <h2 class="text-xl font-semibold mb-6">通过 URL 下载</h2>
        <div class="space-y-4">
          <div>
            <label class="block text-white/70 text-sm mb-2">URL</label>
            <input 
              v-model="urlForm.url" 
              type="text" 
              class="input-glass w-full" 
              placeholder="音乐 URL 或 ID"
            />
          </div>
          <div>
            <label class="block text-white/70 text-sm mb-2">来源</label>
            <select v-model="urlForm.source" class="input-glass w-full">
              <option v-for="opt in sourceOptions" :key="opt.value" :value="opt.value">
                {{ opt.label }}
              </option>
            </select>
          </div>
          <div>
            <label class="block text-white/70 text-sm mb-2">音质</label>
            <select v-model="urlForm.quality" class="input-glass w-full">
              <option v-for="opt in qualityOptions" :key="opt.value" :value="opt.value">
                {{ opt.label }}
              </option>
            </select>
          </div>
          <div>
            <label class="block text-white/70 text-sm mb-2">标题（可选）</label>
            <input 
              v-model="urlForm.title" 
              type="text" 
              class="input-glass w-full" 
              placeholder="覆盖自动识别的标题"
            />
          </div>
          <div>
            <label class="block text-white/70 text-sm mb-2">艺术家（可选）</label>
            <input 
              v-model="urlForm.artist" 
              type="text" 
              class="input-glass w-full" 
              placeholder="覆盖自动识别的艺术家"
            />
          </div>
        </div>
        <div class="flex justify-end gap-3 mt-6">
          <button class="btn-secondary" @click="showUrlModal = false">取消</button>
          <button class="btn-primary" @click="handleUrlDownload" :loading="downloadingByUrl">
            开始下载
          </button>
        </div>
      </GlassCard>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, computed, onMounted, onUnmounted } from 'vue'
import GlassCard from '@/components/ui/GlassCard.vue'
import { downloadApi } from '@/api/client'

// 状态
const loading = ref(false)
const searching = ref(false)
const downloadingByUrl = ref(false)
const showSearchModal = ref(false)
const showUrlModal = ref(false)
const activeTab = ref('downloading')

// 下载任务数据
const activeDownloads = ref<any[]>([])
const completedDownloads = ref<any[]>([])
const failedDownloads = ref<any[]>([])
const downloadHistory = ref<any[]>([])

// 统计
const stats = ref({
  total: 0,
  completed: 0,
  failed: 0,
})

// 计算显示的任务
const displayTasks = computed(() => {
  switch (activeTab.value) {
    case 'downloading': return activeDownloads.value
    case 'completed': return completedDownloads.value
    case 'failed': return failedDownloads.value
    case 'history': return downloadHistory.value
    default: return []
  }
})

// Tab 配置
const tabs = computed(() => [
  { label: '下载中', value: 'downloading', count: activeDownloads.value.length },
  { label: '已完成', value: 'completed', count: completedDownloads.value.length },
  { label: '失败', value: 'failed', count: failedDownloads.value.length },
  { label: '历史', value: 'history', count: downloadHistory.value.length },
])

// 空状态
const emptyIcon = computed(() => {
  const icons: Record<string, string> = {
    downloading: '⏳',
    completed: '✅',
    failed: '❌',
    history: '📋',
  }
  return icons[activeTab.value] || '📭'
})

const emptyText = computed(() => {
  const texts: Record<string, string> = {
    downloading: '没有正在下载的任务',
    completed: '没有已完成的下载',
    failed: '没有失败的下载',
    history: '没有下载历史',
  }
  return texts[activeTab.value] || '没有数据'
})

// 计算成功率
const successRate = computed(() => {
  const total = stats.value.completed + stats.value.failed
  return total > 0 ? Math.round((stats.value.completed / total) * 100) : 0
})

// 状态映射
const statusClass = (status: string) => {
  const classes: Record<string, string> = {
    pending: 'bg-yellow-500/20 text-yellow-400',
    downloading: 'bg-blue-500/20 text-blue-400',
    completed: 'bg-green-500/20 text-green-400',
    failed: 'bg-red-500/20 text-red-400',
    cancelled: 'bg-gray-500/20 text-gray-400',
  }
  return classes[status] || 'bg-white/10 text-white/60'
}

const statusText = (status: string) => {
  const texts: Record<string, string> = {
    pending: '等待中',
    downloading: '下载中',
    completed: '已完成',
    failed: '失败',
    cancelled: '已取消',
  }
  return texts[status] || status
}

// 选项配置
const sourceOptions = [
  { label: '网易云音乐', value: 'netease' },
  { label: 'QQ音乐', value: 'qq' },
  { label: '酷狗音乐', value: 'kugou' },
]

const qualityOptions = [
  { label: '标准 (128kbps)', value: 'standard' },
  { label: '高品质 (320kbps)', value: 'high' },
  { label: '无损 (FLAC)', value: 'lossless' },
]

const qualityMap: Record<string, string> = {
  standard: '标准',
  high: '高品质',
  lossless: '无损',
}

// 搜索表单
const searchForm = ref({
  keyword: '',
  source: 'netease',
  quality: 'standard',
  limit: 1,
})

// URL 表单
const urlForm = ref({
  url: '',
  source: 'netease',
  quality: 'standard',
  title: '',
  artist: '',
  album: '',
})

// 方法
const refresh = async () => {
  loading.value = true
  try {
    await Promise.all([
      fetchActiveDownloads(),
      fetchCompletedDownloads(),
      fetchFailedDownloads(),
      fetchDownloadHistory(),
      fetchStats(),
    ])
  } catch (error) {
    console.error('Refresh failed:', error)
  } finally {
    loading.value = false
  }
}

const fetchActiveDownloads = async () => {
  try {
    const res = await downloadApi.list()
    activeDownloads.value = (res.tasks || []).filter((t: any) => t.status === 'downloading')
    completedDownloads.value = (res.tasks || []).filter((t: any) => t.status === 'completed')
    failedDownloads.value = (res.tasks || []).filter((t: any) => t.status === 'failed')
  } catch (error) {
    console.error('Failed to fetch downloads:', error)
  }
}

const fetchCompletedDownloads = async () => {
  // Data is already loaded in fetchActiveDownloads
}

const fetchFailedDownloads = async () => {
  // Data is already loaded in fetchActiveDownloads
}

const fetchDownloadHistory = async () => {
  try {
    const res = await downloadApi.list()
    downloadHistory.value = res.tasks || []
  } catch (error) {
    console.error('Failed to fetch download history:', error)
  }
}

const fetchStats = async () => {
  stats.value = {
    total: activeDownloads.value.length + completedDownloads.value.length + failedDownloads.value.length,
    completed: completedDownloads.value.length,
    failed: failedDownloads.value.length,
  }
}

const handleSearchAndDownload = async () => {
  if (!searchForm.value.keyword.trim()) return
  
  searching.value = true
  try {
    console.log('Search and download:', searchForm.value)
    showSearchModal.value = false
    searchForm.value = { keyword: '', source: 'netease', quality: 'standard', limit: 1 }
    await refresh()
  } catch (error) {
    console.error('Search failed:', error)
  } finally {
    searching.value = false
  }
}

const handleUrlDownload = async () => {
  if (!urlForm.value.url.trim()) return
  
  downloadingByUrl.value = true
  try {
    await downloadApi.create({ torrent_url: urlForm.value.url })
    showUrlModal.value = false
    urlForm.value = { url: '', source: 'netease', quality: 'standard', title: '', artist: '', album: '' }
    await refresh()
  } catch (error) {
    console.error('URL download failed:', error)
  } finally {
    downloadingByUrl.value = false
  }
}

const cancelDownload = async (taskId: string) => {
  try {
    await downloadApi.delete(Number(taskId))
    await refresh()
  } catch (error) {
    console.error('Cancel download failed:', error)
  }
}

const retryDownload = async (task: any) => {
  console.log('Retry download:', task)
  await refresh()
}

const playTrack = async (filePath: string) => {
  // TODO: 调用播放器
  console.log('Play track:', filePath)
}

const formatFileSize = (bytes: number): string => {
  if (bytes === 0) return '0 B'
  const k = 1024
  const sizes = ['B', 'KB', 'MB', 'GB']
  const i = Math.floor(Math.log(bytes) / Math.log(k))
  return Math.round((bytes / Math.pow(k, i)) * 100) / 100 + ' ' + sizes[i]
}

const formatDate = (dateStr: string): string => {
  const date = new Date(dateStr)
  return date.toLocaleString('zh-CN')
}

// 定时刷新
let refreshTimer: NodeJS.Timeout | null = null

onMounted(async () => {
  await refresh()
  
  refreshTimer = setInterval(async () => {
    if (activeTab.value === 'downloading') {
      await fetchActiveDownloads()
    }
  }, 5000)
})

onUnmounted(() => {
  if (refreshTimer) {
    clearInterval(refreshTimer)
    refreshTimer = null
  }
})
</script>

<style scoped>
.download-view {
  min-height: 100%;
}
</style>