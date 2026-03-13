<template>
  <div class="space-y-6 animate-fade-in">
    <!-- Header -->
    <div class="flex items-center justify-between">
      <h1 class="text-2xl font-bold">下载管理</h1>
      <Button variant="primary" @click="showAddModal = true">
        <svg class="w-5 h-5 mr-2" fill="none" stroke="currentColor" viewBox="0 0 24 24">
          <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M12 4v16m8-8H4" />
        </svg>
        添加下载
      </Button>
    </div>

    <!-- Stats -->
    <div class="grid grid-cols-2 md:grid-cols-4 gap-4">
      <GlassCard v-for="stat in stats" :key="stat.label">
        <p class="text-2xl font-bold" :class="stat.color">{{ stat.value }}</p>
        <p class="text-sm text-white/60">{{ stat.label }}</p>
      </GlassCard>
    </div>

    <!-- Download List -->
    <GlassCard>
      <div class="space-y-3">
        <div
          v-for="task in tasks"
          :key="task.id"
          class="flex items-center gap-4 p-3 rounded-xl hover:bg-white/5 transition-colors"
        >
          <!-- Status Icon -->
          <div
            :class="[
              'w-10 h-10 rounded-xl flex items-center justify-center',
              task.status === 'completed' ? 'bg-green-500/20 text-green-500' :
              task.status === 'downloading' ? 'bg-accent/20 text-accent' :
              'bg-white/10 text-white/60'
            ]"
          >
            <svg v-if="task.status === 'completed'" class="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M5 13l4 4L19 7" />
            </svg>
            <svg v-else-if="task.status === 'downloading'" class="w-5 h-5 animate-spin" fill="none" viewBox="0 0 24 24">
              <circle class="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" stroke-width="4" />
              <path class="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z" />
            </svg>
            <svg v-else class="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M12 8v4l3 3m6-3a9 9 0 11-18 0 9 9 0 0118 0z" />
            </svg>
          </div>

          <!-- Info -->
          <div class="flex-1 min-w-0">
            <p class="font-medium truncate">{{ task.name }}</p>
            <p class="text-sm text-white/60">{{ task.save_path }}</p>
          </div>

          <!-- Progress -->
          <div v-if="task.status === 'downloading'" class="w-32">
            <div class="h-2 bg-white/10 rounded-full overflow-hidden">
              <div
                class="h-full bg-accent rounded-full transition-all duration-300"
                :style="{ width: `${task.progress}%` }"
              />
            </div>
            <p class="text-xs text-white/60 mt-1">{{ task.progress.toFixed(1) }}%</p>
          </div>

          <!-- Actions -->
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

    <!-- Add Modal -->
    <div v-if="showAddModal" class="fixed inset-0 z-50 flex items-center justify-center p-4 bg-black/50 backdrop-blur-sm">
      <GlassCard class="w-full max-w-md">
        <h3 class="text-xl font-bold mb-4">添加下载</h3>
        <div class="space-y-4">
          <Input
            v-model="newTask.torrent_url"
            label="种子链接"
            placeholder="https://..."
          />
          <Input
            v-model="newTask.save_path"
            label="保存路径"
            placeholder="/downloads/music"
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

const stats = ref([
  { label: '下载中', value: 0, color: 'text-accent' },
  { label: '已完成', value: 0, color: 'text-green-500' },
  { label: '等待中', value: 0, color: 'text-white/60' },
  { label: '失败', value: 0, color: 'text-red-400' },
])

const tasks = ref([])
const showAddModal = ref(false)
const adding = ref(false)
const newTask = ref({
  torrent_url: '',
  save_path: '/downloads/music',
})

const fetchTasks = async () => {
  try {
    const response = await fetch('/api/v1/download/tasks')
    const data = await response.json()
    tasks.value = data.tasks || []
    updateStats()
  } catch (error) {
    console.error('Failed to fetch tasks:', error)
  }
}

const updateStats = () => {
  stats.value[0].value = tasks.value.filter(t => t.status === 'downloading').length
  stats.value[1].value = tasks.value.filter(t => t.status === 'completed').length
  stats.value[2].value = tasks.value.filter(t => t.status === 'pending').length
  stats.value[3].value = tasks.value.filter(t => t.status === 'failed').length
}

const addTask = async () => {
  if (!newTask.value.torrent_url) return
  
  adding.value = true
  try {
    await fetch('/api/v1/download/tasks', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(newTask.value)
    })
    showAddModal.value = false
    newTask.value.torrent_url = ''
    await fetchTasks()
  } catch (error) {
    console.error('Failed to add task:', error)
  } finally {
    adding.value = false
  }
}

const deleteTask = async (id: number) => {
  try {
    await fetch(`/api/v1/download/tasks/${id}`, { method: 'DELETE' })
    await fetchTasks()
  } catch (error) {
    console.error('Failed to delete task:', error)
  }
}

onMounted(fetchTasks)
</script>
