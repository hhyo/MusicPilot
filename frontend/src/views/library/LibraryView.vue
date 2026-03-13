<template>
  <div class="library-view p-4 md:p-6 lg:p-8">
    <!-- 页面标题 -->
    <div class="flex items-center justify-between mb-6">
      <div>
        <h1 class="text-3xl font-bold mb-1">音乐库</h1>
        <p class="text-white/50">管理您的音乐收藏</p>
      </div>
      <button class="btn-primary flex items-center gap-2" @click="showAddDialog = true">
        <span>➕</span>
        <span>添加音乐库</span>
      </button>
    </div>

    <!-- 加载状态 -->
    <div v-if="loading" class="flex items-center justify-center py-20">
      <div class="w-8 h-8 border-2 border-accent border-t-transparent rounded-full animate-spin"></div>
    </div>

    <!-- 空状态 -->
    <GlassCard v-else-if="!libraries.length" class="flex flex-col items-center justify-center py-20">
      <div class="text-6xl mb-4">📁</div>
      <h3 class="text-xl font-semibold mb-2">暂无音乐库</h3>
      <p class="text-white/50 mb-6">添加一个音乐库开始管理您的音乐</p>
      <button class="btn-primary" @click="showAddDialog = true">
        添加音乐库
      </button>
    </GlassCard>

    <!-- 音乐库列表 -->
    <div v-else class="grid gap-4">
      <GlassCard 
        v-for="library in libraries" 
        :key="library.id"
        hoverable
        class="flex flex-col md:flex-row md:items-center gap-4"
      >
        <!-- 音乐库图标 -->
        <div class="w-16 h-16 rounded-2xl bg-gradient-to-br from-accent/30 to-accent/10 flex items-center justify-center text-3xl shrink-0">
          🎵
        </div>
        
        <!-- 音乐库信息 -->
        <div class="flex-1 min-w-0">
          <h3 class="text-lg font-semibold mb-1 truncate">{{ library.name }}</h3>
          <p class="text-white/50 text-sm truncate">{{ library.path }}</p>
        </div>
        
        <!-- 统计 -->
        <div class="flex items-center gap-3 shrink-0">
          <span class="glass rounded-full px-4 py-1.5 text-sm">
            {{ library.trackCount || 0 }} 首曲目
          </span>
          <span class="glass rounded-full px-4 py-1.5 text-sm">
            {{ library.albumCount || 0 }} 张专辑
          </span>
        </div>
        
        <!-- 操作按钮 -->
        <div class="flex items-center gap-2 shrink-0">
          <button class="btn-ghost p-2" title="扫描" @click="scanLibrary(library.id)">
            🔄
          </button>
          <button class="btn-ghost p-2" title="设置" @click="editLibrary(library.id)">
            ⚙️
          </button>
          <button class="btn-ghost p-2 text-red-400 hover:text-red-300" title="删除" @click="deleteLibrary(library.id)">
            🗑️
          </button>
        </div>
      </GlassCard>
    </div>

    <!-- 添加音乐库对话框 -->
    <div v-if="showAddDialog" class="fixed inset-0 bg-black/50 backdrop-blur-sm flex items-center justify-center z-50" @click.self="showAddDialog = false">
      <GlassCard class="w-full max-w-md p-6 animate-slide-up">
        <h2 class="text-xl font-semibold mb-6">添加音乐库</h2>
        <div class="space-y-4">
          <div>
            <label class="block text-white/70 text-sm mb-2">音乐库名称</label>
            <input v-model="newLibrary.name" type="text" class="input-glass w-full" placeholder="例如：我的音乐" />
          </div>
          <div>
            <label class="block text-white/70 text-sm mb-2">音乐库路径</label>
            <input v-model="newLibrary.path" type="text" class="input-glass w-full" placeholder="/path/to/music" />
          </div>
        </div>
        <div class="flex justify-end gap-3 mt-6">
          <button class="btn-secondary" @click="showAddDialog = false">取消</button>
          <button class="btn-primary" @click="addLibrary">添加</button>
        </div>
      </GlassCard>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, onMounted } from 'vue'
import GlassCard from '@/components/ui/GlassCard.vue'

interface Library {
  id: string
  name: string
  path: string
  trackCount?: number
  albumCount?: number
}

const loading = ref(false)
const libraries = ref<Library[]>([])
const showAddDialog = ref(false)
const newLibrary = ref({ name: '', path: '' })

onMounted(async () => {
  loading.value = true
  // TODO: 调用 API 获取音乐库列表
  libraries.value = [
    { id: '1', name: '我的音乐', path: '/home/user/Music', trackCount: 1234, albumCount: 89 },
    { id: '2', name: '下载音乐', path: '/home/user/Downloads', trackCount: 56, albumCount: 12 },
  ]
  loading.value = false
})

const addLibrary = () => {
  // TODO: 实现添加音乐库
  showAddDialog.value = false
  newLibrary.value = { name: '', path: '' }
}

const scanLibrary = (id: string) => {
  // TODO: 实现扫描音乐库
}

const editLibrary = (id: string) => {
  // TODO: 实现编辑音乐库
}

const deleteLibrary = (id: string) => {
  // TODO: 实现删除音乐库
}
</script>

<style scoped>
.library-view {
  min-height: 100%;
}
</style>