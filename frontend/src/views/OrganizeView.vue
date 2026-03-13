<template>
  <div class="space-y-6 animate-fade-in">
    <!-- Header -->
    <div class="flex items-center justify-between">
      <h1 class="text-2xl font-bold">文件整理</h1>
      <Button variant="primary" @click="showAddModal = true">
        <svg class="w-5 h-5 mr-2" fill="none" stroke="currentColor" viewBox="0 0 24 24">
          <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M12 4v16m8-8H4" />
        </svg>
        创建任务
      </Button>
    </div>

    <!-- Stats -->
    <div class="grid grid-cols-2 md:grid-cols-4 gap-4">
      <GlassCard v-for="stat in stats" :key="stat.label">
        <p class="text-2xl font-bold" :class="stat.color">{{ stat.value }}</p>
        <p class="text-sm text-white/60">{{ stat.label }}</p>
      </GlassCard>
    </div>

    <!-- Loading State -->
    <GlassCard v-if="loading">
      <div class="space-y-3">
        <div v-for="i in 5" :key="i" class="flex items-center gap-4 p-3 animate-pulse">
          <div class="w-10 h-10 rounded-xl bg-white/10"></div>
          <div class="flex-1">
            <div class="h-4 bg-white/10 rounded w-1/2 mb-2"></div>
            <div class="h-3 bg-white/10 rounded w-1/3"></div>
          </div>
        </div>
      </div>
    </GlassCard>

    <!-- Organize List -->
    <GlassCard v-else>
      <div class="space-y-3">
        <div
          v-for="task in tasks"
          :key="task.id"
          class="flex items-center gap-4 p-3 rounded-xl hover:bg-white/5 transition-colors"
        >
          <!-- Status -->
          <div
            :class="[
              'w-10 h-10 rounded-xl flex items-center justify-center',
              task.status === 'completed' ? 'bg-green-500/20 text-green-500' :
              task.status === 'processing' ? 'bg-accent/20 text-accent' :
              'bg-white/10 text-white/60'
            ]"
          >
            <svg v-if="task.status === 'completed'" class="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M5 13l4 4L19 7" />
            </svg>
            <svg v-else-if="task.status === 'processing'" class="w-5 h-5 animate-spin" fill="none" viewBox="0 0 24 24">
              <circle class="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" stroke-width="4" />
              <path class="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z" />
            </svg>
            <svg v-else class="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M12 8v4l3 3m6-3a9 9 0 11-18 0 9 9 0 0118 0z" />
            </svg>
          </div>

          <!-- Info -->
          <div class="flex-1 min-w-0">
            <p class="font-medium">{{ task.source_path }}</p>
            <p class="text-sm text-white/60">→ {{ task.target_path }}</p>
          </div>

          <!-- Status Label -->
          <span :class="[
            'text-sm px-2 py-1 rounded',
            task.status === 'completed' ? 'bg-green-500/20 text-green-500' :
            task.status === 'processing' ? 'bg-accent/20 text-accent' :
            task.status === 'failed' ? 'bg-red-500/20 text-red-500' :
            'bg-white/10 text-white/60'
          ]">
            {{ getStatusLabel(task.status) }}
          </span>

          <!-- Actions -->
          <Button
            v-if="task.status === 'failed'"
            variant="secondary"
            size="sm"
            @click="retryTask(task.id)"
          >
            重试
          </Button>
          <Button
            variant="ghost"
            size="sm"
            @click="deleteTask(task.id)"
          >
            <svg class="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M19 7l-.867 12.142A2 2 0 0116.138 21H7.862a2 2 0 01-1.995-1.858L5 7m5 4v6m4-6v6m1-10V4a1 1 0 00-1-1h-4a1 1 0 00-1 1v3M4 7h16" />
            </svg>
          </Button>
        </div>
      </div>
    </GlassCard>

    <!-- Empty State -->
    <div v-if="!loading && !tasks.length" class="text-center py-20">
      <svg class="w-20 h-20 text-white/20 mx-auto mb-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
        <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M3 7v10a2 2 0 002 2h14a2 2 0 002-2V9a2 2 0 00-2-2h-6l-2-2H5a2 2 0 00-2 2z" />
      </svg>
      <p class="text-white/60 mb-4">暂无整理任务</p>
      <Button variant="primary" @click="showAddModal = true">创建任务</Button>
    </div>

    <!-- Add Modal -->
    <div v-if="showAddModal" class="fixed inset-0 z-50 flex items-center justify-center p-4 bg-black/50 backdrop-blur-sm">
      <GlassCard class="w-full max-w-md">
        <h3 class="text-xl font-bold mb-4">创建整理任务</h3>
        <div class="space-y-4">
          <Input
            v-model="newTask.source_path"
            label="源路径"
            placeholder="/downloads/music"
          />
          <Input
            v-model="newTask.target_path"
            label="目标路径"
            placeholder="/library/music"
          />
        </div>
        <div class="flex gap-3 mt-6">
          <Button variant="secondary" class="flex-1" @click="showAddModal = false">
            取消
          </Button>
          <Button variant="primary" class="flex-1" :loading="adding" @click="addTask">
            确认
          </Button>
        </div>
      </GlassCard>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, onMounted } from 'vue'
import GlassCard from '@/components/ui/GlassCard.vue'
import Button from '@/components/ui/Button.vue'
import Input from '@/components/ui/Input.vue'
import { organizeApi } from '@/api/client'

const stats = ref([
  { label: '进行中', value: 0, color: 'text-accent' },
  { label: '已完成', value: 0, color: 'text-green-500' },
  { label: '等待中', value: 0, color: 'text-white/60' },
  { label: '失败', value: 0, color: 'text-red-400' },
])

const tasks = ref<any[]>([])
const loading = ref(false)
const showAddModal = ref(false)
const adding = ref(false)
const newTask = ref({
  source_path: '/downloads/music',
  target_path: '/library/music',
})

const getStatusLabel = (status: string) => {
  const map: Record<string, string> = {
    processing: '处理中',
    completed: '已完成',
    pending: '等待中',
    failed: '失败',
  }
  return map[status] || status
}

const fetchTasks = async () => {
  loading.value = true
  try {
    const res = await organizeApi.list()
    tasks.value = res.tasks || []
    updateStats()
  } catch (error) {
    console.error('Failed to fetch tasks:', error)
    tasks.value = []
  } finally {
    loading.value = false
  }
}

const updateStats = () => {
  stats.value[0].value = tasks.value.filter(t => t.status === 'processing').length
  stats.value[1].value = tasks.value.filter(t => t.status === 'completed').length
  stats.value[2].value = tasks.value.filter(t => t.status === 'pending').length
  stats.value[3].value = tasks.value.filter(t => t.status === 'failed').length
}

const addTask = async () => {
  if (!newTask.value.source_path || !newTask.value.target_path) return
  
  adding.value = true
  try {
    await organizeApi.create({
      source_path: newTask.value.source_path,
      target_path: newTask.value.target_path,
    })
    showAddModal.value = false
    await fetchTasks()
  } catch (error) {
    console.error('Failed to add task:', error)
    alert('创建整理任务失败')
  } finally {
    adding.value = false
  }
}

const retryTask = async (id: number) => {
  try {
    await organizeApi.retry(id)
    await fetchTasks()
  } catch (error) {
    console.error('Failed to retry task:', error)
    alert('重试失败')
  }
}

const deleteTask = async (id: number) => {
  if (!confirm('确定要删除这个任务吗？')) return
  
  try {
    await organizeApi.delete(id)
    await fetchTasks()
  } catch (error) {
    console.error('Failed to delete task:', error)
    alert('删除任务失败')
  }
}

onMounted(fetchTasks)
</script>