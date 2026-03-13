<template>
  <div class="subscribe-view p-4 md:p-6 lg:p-8">
    <!-- 页面标题 -->
    <div class="flex items-center justify-between mb-6">
      <div>
        <h1 class="text-3xl font-bold mb-1">订阅管理</h1>
        <p class="text-white/50">管理您的音乐订阅</p>
      </div>
      <button class="btn-primary flex items-center gap-2" @click="showCreateModal = true">
        <span>➕</span>
        <span>添加订阅</span>
      </button>
    </div>

    <!-- 标签页切换 -->
    <div class="flex flex-wrap gap-2 mb-6 p-2 glass rounded-2xl">
      <button
        v-for="tab in tabs"
        :key="tab.value"
        class="py-2 px-4 rounded-xl transition-all duration-200 font-medium"
        :class="activeTab === tab.value 
          ? 'bg-accent text-white shadow-lg shadow-accent/25' 
          : 'text-white/60 hover:text-white hover:bg-white/10'"
        @click="activeTab = tab.value"
      >
        {{ tab.label }}
      </button>
    </div>

    <!-- 订阅列表 -->
    <div v-if="currentSubscribes.length" class="space-y-3">
      <GlassCard 
        v-for="subscribe in currentSubscribes" 
        :key="subscribe.id"
        hoverable
        class="flex items-center gap-4"
      >
        <!-- 图标 -->
        <div class="w-12 h-12 rounded-xl bg-gradient-to-br from-accent/30 to-accent/10 flex items-center justify-center text-xl shrink-0">
          {{ getTypeIcon(subscribe.type) }}
        </div>
        
        <!-- 信息 -->
        <div class="flex-1 min-w-0">
          <h3 class="font-semibold truncate">{{ subscribe.name }}</h3>
          <p class="text-white/50 text-sm truncate">{{ subscribe.description || getTypeLabel(subscribe.type) }}</p>
        </div>
        
        <!-- 状态标签 -->
        <div class="flex items-center gap-2 shrink-0">
          <span 
            v-if="subscribe.auto_download"
            class="glass rounded-full px-3 py-1 text-xs"
            :class="subscribe.last_downloaded ? 'text-accent' : 'text-white/40'"
          >
            {{ subscribe.last_downloaded ? '✅ 自动下载' : '⏳ 待下载' }}
          </span>
        </div>
        
        <!-- 操作按钮 -->
        <div class="flex items-center gap-2 shrink-0">
          <button class="btn-ghost p-2" title="刷新" @click="refreshSubscribe(subscribe.id)">
            🔄
          </button>
          <button class="btn-ghost p-2" title="编辑" @click="handleEdit(subscribe)">
            ✏️
          </button>
          <button class="btn-ghost p-2 text-red-400 hover:text-red-300" title="删除" @click="handleDelete(subscribe)">
            🗑️
          </button>
        </div>
      </GlassCard>
    </div>

    <!-- 空状态 -->
    <GlassCard v-else class="flex flex-col items-center justify-center py-16">
      <div class="text-6xl mb-4">📋</div>
      <h3 class="text-xl font-semibold mb-2">暂无订阅</h3>
      <p class="text-white/50 mb-6">添加订阅以获取最新的音乐更新</p>
      <button class="btn-primary" @click="showCreateModal = true">
        添加订阅
      </button>
    </GlassCard>

    <!-- 创建/编辑对话框 -->
    <div v-if="showCreateModal" class="fixed inset-0 bg-black/50 backdrop-blur-sm flex items-center justify-center z-50 p-4" @click.self="showCreateModal = false">
      <GlassCard class="w-full max-w-lg p-6 animate-slide-up max-h-[90vh] overflow-y-auto">
        <h2 class="text-xl font-semibold mb-6">{{ editingSubscribe ? '编辑订阅' : '添加订阅' }}</h2>
        
        <div class="space-y-4">
          <!-- 订阅类型 -->
          <div>
            <label class="block text-white/70 text-sm mb-2">订阅类型</label>
            <div class="flex flex-wrap gap-2">
              <button
                v-for="type in typeOptions"
                :key="type.value"
                class="px-4 py-2 rounded-xl transition-all duration-200"
                :class="form.type === type.value 
                  ? 'bg-accent text-white' 
                  : 'glass text-white/60 hover:text-white'"
                @click="form.type = type.value"
              >
                {{ type.label }}
              </button>
            </div>
          </div>

          <!-- ID -->
          <div>
            <label class="block text-white/70 text-sm mb-2">{{ idLabel }}</label>
            <input v-model="form.id" type="text" class="input-glass w-full" :placeholder="idPlaceholder" />
          </div>

          <!-- 名称 -->
          <div>
            <label class="block text-white/70 text-sm mb-2">名称</label>
            <input v-model="form.name" type="text" class="input-glass w-full" placeholder="订阅名称" />
          </div>

          <!-- 描述 -->
          <div>
            <label class="block text-white/70 text-sm mb-2">描述</label>
            <textarea v-model="form.description" class="input-glass w-full h-24 resize-none" placeholder="订阅描述（可选）"></textarea>
          </div>

          <!-- 自动下载 -->
          <div class="flex items-center justify-between">
            <label class="text-white/70">自动下载</label>
            <button 
              class="w-12 h-6 rounded-full transition-colors duration-200"
              :class="form.auto_download ? 'bg-accent' : 'bg-white/20'"
              @click="form.auto_download = !form.auto_download"
            >
              <span 
                class="block w-5 h-5 bg-white rounded-full transition-transform duration-200"
                :class="form.auto_download ? 'translate-x-6' : 'translate-x-0.5'"
              ></span>
            </button>
          </div>

          <!-- 下载格式 -->
          <div v-if="form.auto_download">
            <label class="block text-white/70 text-sm mb-2">下载格式</label>
            <select v-model="form.download_format" class="input-glass w-full">
              <option value="FLAC">FLAC</option>
              <option value="MP3">MP3</option>
              <option value="APE">APE</option>
            </select>
          </div>
        </div>

        <div class="flex justify-end gap-3 mt-6">
          <button class="btn-secondary" @click="showCreateModal = false">取消</button>
          <button class="btn-primary" @click="handleSubmit">
            {{ editingSubscribe ? '保存' : '创建' }}
          </button>
        </div>
      </GlassCard>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, computed, onMounted, watch } from 'vue'
import GlassCard from '@/components/ui/GlassCard.vue'

interface Subscribe {
  id: string
  type: string
  name: string
  description?: string
  auto_download: boolean
  last_downloaded?: string
  musicbrainz_id?: string
  playlist_id?: string
}

const activeTab = ref('artist')
const showCreateModal = ref(false)
const editingSubscribe = ref<Subscribe | null>(null)

const form = ref({
  type: 'artist',
  id: '',
  name: '',
  description: '',
  auto_download: true,
  download_format: 'FLAC'
})

const tabs = [
  { label: '艺术家', value: 'artist' },
  { label: '专辑', value: 'album' },
  { label: '歌单', value: 'playlist' },
  { label: '榜单', value: 'chart' },
  { label: '发布记录', value: 'history' },
]

const typeOptions = [
  { label: '艺术家', value: 'artist' },
  { label: '专辑', value: 'album' },
  { label: '歌单', value: 'playlist' },
  { label: '榜单', value: 'chart' },
]

// 模拟数据
const subscribes = ref<Subscribe[]>([
  { id: '1', type: 'artist', name: '周杰伦', description: '华语流行天王', auto_download: true, last_downloaded: '2024-01-15' },
  { id: '2', type: 'artist', name: '林俊杰', description: '华语创作歌手', auto_download: true, last_downloaded: '2024-01-14' },
  { id: '3', type: 'album', name: '最伟大的作品', description: '周杰伦2022年专辑', auto_download: true, last_downloaded: '2024-01-10' },
  { id: '4', type: 'playlist', name: '收藏歌单', description: '网易云音乐', auto_download: false },
  { id: '5', type: 'chart', name: '飙升榜', description: 'QQ音乐', auto_download: true },
])

const currentSubscribes = computed(() => {
  if (activeTab.value === 'history') return []
  return subscribes.value.filter(s => s.type === activeTab.value)
})

const idLabel = computed(() => {
  switch (form.value.type) {
    case 'artist':
    case 'album':
      return 'MusicBrainz ID'
    case 'playlist':
      return '歌单 ID'
    case 'chart':
      return '榜单 ID'
    default:
      return 'ID'
  }
})

const idPlaceholder = computed(() => {
  switch (form.value.type) {
    case 'artist':
      return '例如：d36e608f-5491-4b9f-9657-90e7c7b5b2ad'
    case 'album':
      return '例如：8a2d8f3a-4b3e-4c2d-9a1f-2b3c4d5e6f7g'
    case 'playlist':
      return '例如：3778678'
    case 'chart':
      return '例如：19723756'
    default:
      return '请输入 ID'
  }
})

const getTypeIcon = (type: string) => {
  switch (type) {
    case 'artist': return '👤'
    case 'album': return '💿'
    case 'playlist': return '📋'
    case 'chart': return '📊'
    default: return '📌'
  }
}

const getTypeLabel = (type: string) => {
  switch (type) {
    case 'artist': return '艺术家'
    case 'album': return '专辑'
    case 'playlist': return '歌单'
    case 'chart': return '榜单'
    default: return '订阅'
  }
}

const refreshSubscribe = (id: string) => {
  console.log('刷新订阅:', id)
}

const handleEdit = (subscribe: Subscribe) => {
  editingSubscribe.value = subscribe
  form.value = {
    type: subscribe.type,
    id: subscribe.musicbrainz_id || subscribe.playlist_id || '',
    name: subscribe.name,
    description: subscribe.description || '',
    auto_download: subscribe.auto_download,
    download_format: 'FLAC'
  }
  showCreateModal.value = true
}

const handleDelete = (subscribe: Subscribe) => {
  if (confirm(`确定要删除订阅 "${subscribe.name}" 吗？`)) {
    subscribes.value = subscribes.value.filter(s => s.id !== subscribe.id)
  }
}

const handleSubmit = () => {
  if (editingSubscribe.value) {
    // 更新
    const index = subscribes.value.findIndex(s => s.id === editingSubscribe.value?.id)
    if (index !== -1) {
      subscribes.value[index] = {
        ...subscribes.value[index],
        ...form.value,
        musicbrainz_id: form.value.type === 'artist' || form.value.type === 'album' ? form.value.id : undefined,
        playlist_id: form.value.type === 'playlist' || form.value.type === 'chart' ? form.value.id : undefined
      }
    }
  } else {
    // 创建
    subscribes.value.push({
      id: Date.now().toString(),
      ...form.value,
      auto_download: form.value.auto_download
    })
  }
  showCreateModal.value = false
  editingSubscribe.value = null
  resetForm()
}

const resetForm = () => {
  form.value = {
    type: 'artist',
    id: '',
    name: '',
    description: '',
    auto_download: true,
    download_format: 'FLAC'
  }
}

watch(showCreateModal, (val) => {
  if (!val) {
    resetForm()
    editingSubscribe.value = null
  }
})
</script>

<style scoped>
.subscribe-view {
  min-height: 100%;
}
</style>