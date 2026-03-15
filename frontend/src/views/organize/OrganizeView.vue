<template>
  <div class="organize-view p-4 md:p-6 lg:p-8">
    <!-- 页面标题 -->
    <div class="flex flex-col sm:flex-row sm:items-center justify-between gap-4 mb-6">
      <div>
        <h1 class="text-3xl font-bold mb-1">文件整理</h1>
        <p class="text-white/50">管理您的音乐文件整理任务</p>
      </div>
      <button class="btn-secondary flex items-center gap-2" @click="refresh" :disabled="loading">
        <span :class="{ 'animate-spin': loading }">🔄</span>
        <span>刷新</span>
      </button>
    </div>

    <!-- 整理统计 -->
    <div class="grid grid-cols-2 md:grid-cols-4 gap-4 mb-6">
      <GlassCard class="text-center">
        <div class="text-2xl font-bold text-accent">{{ stats.total }}</div>
        <div class="text-white/50 text-sm">总任务数</div>
      </GlassCard>
      <GlassCard class="text-center">
        <div class="text-2xl font-bold text-green-400">{{ stats.completed }}</div>
        <div class="text-white/50 text-sm">已完成</div>
      </GlassCard>
      <GlassCard class="text-center">
        <div class="text-2xl font-bold text-blue-400">{{ stats.processing }}</div>
        <div class="text-white/50 text-sm">处理中</div>
      </GlassCard>
      <GlassCard class="text-center">
        <div class="text-2xl font-bold text-red-400">{{ stats.failed }}</div>
        <div class="text-white/50 text-sm">失败</div>
      </GlassCard>
    </div>

    <!-- 加载状态 -->
    <div v-if="loading" class="flex items-center justify-center py-20">
      <div class="w-8 h-8 border-2 border-accent border-t-transparent rounded-full animate-spin"></div>
    </div>

    <!-- 空状态 -->
    <GlassCard v-else-if="tasks.length === 0" class="flex flex-col items-center justify-center py-20">
      <div class="text-6xl mb-4">📁</div>
      <h3 class="text-xl font-semibold mb-2">没有整理任务</h3>
      <p class="text-white/50">开始整理您的音乐文件</p>
    </GlassCard>

    <!-- 任务列表 -->
    <div v-else class="space-y-3">
      <GlassCard 
        v-for="task in tasks" 
        :key="task.id"
        hoverable
        class="flex flex-col gap-3"
      >
        <div class="flex items-start gap-4">
          <!-- 状态图标 -->
          <div 
            class="w-10 h-10 rounded-xl flex items-center justify-center text-xl shrink-0"
            :class="statusIconClass(task.status)"
          >
            {{ statusIcon(task.status) }}
          </div>
          
          <!-- 信息 -->
          <div class="flex-1 min-w-0 space-y-1">
            <div class="flex items-center gap-2">
              <span 
                class="shrink-0 px-2 py-0.5 rounded text-xs font-medium"
                :class="statusClass(task.status)"
              >
                {{ statusText(task.status) }}
              </span>
              <span class="text-white/40 text-xs">ID: {{ task.id }}</span>
            </div>
            
            <div class="grid md:grid-cols-2 gap-2 text-sm">
              <div>
                <span class="text-white/50">源路径: </span>
                <span class="text-white/80 truncate">{{ task.source_path }}</span>
              </div>
              <div>
                <span class="text-white/50">目标路径: </span>
                <span class="text-white/80 truncate">{{ task.target_path }}</span>
              </div>
            </div>
            
            <div class="text-white/40 text-xs">
              创建时间: {{ task.created_at ? formatDate(task.created_at) : '-' }}
            </div>
          </div>
          
          <!-- 操作按钮 -->
          <div class="shrink-0">
            <button 
              v-if="task.status === 'failed'"
              class="btn-ghost text-sm" 
              @click="retryTask(task.id)"
            >
              🔄 重试
            </button>
            <button 
              v-else-if="task.status === 'completed'"
              class="btn-ghost text-sm"
              @click="openFolder(task.target_path)"
            >
              📂 打开
            </button>
          </div>
        </div>
      </GlassCard>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, onMounted } from 'vue'
import GlassCard from '@/components/ui/GlassCard.vue'
import { organizeApi } from '@/api/client'

interface OrganizeTask {
  id: number
  source_path: string
  target_path: string
  status: string
  created_at?: string
}

const loading = ref(false)
const tasks = ref<OrganizeTask[]>([])

const stats = ref({
  total: 0,
  completed: 0,
  processing: 0,
  failed: 0,
})

// 状态映射
const statusClass = (status: string) => {
  const classes: Record<string, string> = {
    pending: 'bg-yellow-500/20 text-yellow-400',
    processing: 'bg-blue-500/20 text-blue-400',
    completed: 'bg-green-500/20 text-green-400',
    failed: 'bg-red-500/20 text-red-400',
  }
  return classes[status] || 'bg-white/10 text-white/60'
}

const statusText = (status: string) => {
  const texts: Record<string, string> = {
    pending: '等待中',
    processing: '处理中',
    completed: '已完成',
    failed: '失败',
  }
  return texts[status] || status
}

const statusIcon = (status: string) => {
  const icons: Record<string, string> = {
    pending: '⏳',
    processing: '🔄',
    completed: '✅',
    failed: '❌',
  }
  return icons[status] || '📋'
}

const statusIconClass = (status: string) => {
  const classes: Record<string, string> = {
    pending: 'bg-yellow-500/20',
    processing: 'bg-blue-500/20',
    completed: 'bg-green-500/20',
    failed: 'bg-red-500/20',
  }
  return classes[status] || 'bg-white/10'
}

const fetchTasks = async () => {
  loading.value = true
  try {
    const res = await organizeApi.list()
    tasks.value = res.tasks || []

    // 计算统计
    stats.value = {
      total: tasks.value.length,
      completed: tasks.value.filter(t => t.status === 'completed').length,
      processing: tasks.value.filter(t => t.status === 'processing' || t.status === 'pending').length,
      failed: tasks.value.filter(t => t.status === 'failed').length,
    }
  } catch (error) {
    console.error('Fetch tasks failed:', error)
    tasks.value = []
  } finally {
    loading.value = false
  }
}

const retryTask = async (id: number) => {
  try {
    await organizeApi.retry(id)
    await fetchTasks()
  } catch (error) {
    console.error('Retry failed:', error)
  }
}

const openFolder = (path: string) => {
  // TODO: 调用系统打开文件夹
  console.log('Open folder:', path)
}

const refresh = async () => {
  await fetchTasks()
}

const formatDate = (dateStr: string): string => {
  const date = new Date(dateStr)
  return date.toLocaleString('zh-CN')
}

onMounted(fetchTasks)
</script>

<style scoped>
.organize-view {
  min-height: 100%;
}
</style>