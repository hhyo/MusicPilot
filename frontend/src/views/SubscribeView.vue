<template>
  <div class="space-y-6 animate-fade-in">
    <!-- Header -->
    <div class="flex items-center justify-between">
      <h1 class="text-2xl font-bold">我的订阅</h1>
      <Button variant="primary" @click="showAddModal = true">
        <svg class="w-5 h-5 mr-2" fill="none" stroke="currentColor" viewBox="0 0 24 24">
          <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M12 4v16m8-8H4" />
        </svg>
        添加订阅
      </Button>
    </div>

    <!-- Subscriptions List -->
    <div class="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
      <GlassCard
        v-for="sub in subscriptions"
        :key="sub.id"
        hoverable
        class="relative"
      >
        <div class="flex items-start justify-between">
          <div class="flex items-center gap-4">
            <div class="w-12 h-12 rounded-xl bg-accent/20 flex items-center justify-center">
              <svg class="w-6 h-6 text-accent" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M9 19V6l12-3v13M9 19c0 1.105-1.343 2-3 2s-3-.895-3-2 1.343-2 3-2 3 .895 3 2zm12-3c0 1.105-1.343 2-3 2s-3-.895-3-2 1.343-2 3-2 3 .895 3 2zM9 10l12-3" />
              </svg>
            </div>
            <div>
              <p class="font-medium">{{ sub.name }}</p>
              <p class="text-sm text-white/60">{{ sub.type === 'artist' ? '艺术家' : '专辑' }}</p>
            </div>
          </div>
          <button
            class="text-white/40 hover:text-red-400 transition-colors"
            @click="deleteSubscribe(sub.id)"
          >
            <svg class="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M19 7l-.867 12.142A2 2 0 0116.138 21H7.862a2 2 0 01-1.995-1.858L5 7m5 4v6m4-6v6m1-10V4a1 1 0 00-1-1h-4a1 1 0 00-1 1v3M4 7h16" />
            </svg>
          </button>
        </div>
        <div class="mt-4 flex items-center gap-4 text-sm text-white/60">
          <span>状态: {{ sub.state }}</span>
          <span>更新: {{ formatDate(sub.last_update) }}</span>
        </div>
      </GlassCard>
    </div>

    <!-- Empty State -->
    <div v-if="!subscriptions.length" class="text-center py-20">
      <svg class="w-20 h-20 text-white/20 mx-auto mb-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
        <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M15 17h5l-1.405-1.405A2.032 2.032 0 0118 14.158V11a6.002 6.002 0 00-4-5.659V5a2 2 0 10-4 0v.341C7.67 6.165 6 8.388 6 11v3.159c0 .538-.214 1.055-.595 1.436L4 17h5m6 0v1a3 3 0 11-6 0v-1m6 0H9" />
      </svg>
      <p class="text-white/60 mb-4">暂无订阅</p>
      <Button variant="primary" @click="showAddModal = true">添加订阅</Button>
    </div>

    <!-- Add Modal -->
    <div v-if="showAddModal" class="fixed inset-0 z-50 flex items-center justify-center p-4 bg-black/50 backdrop-blur-sm">
      <GlassCard class="w-full max-w-md">
        <h3 class="text-xl font-bold mb-4">添加订阅</h3>
        <div class="space-y-4">
          <div>
            <label class="block text-sm text-white/70 mb-2">类型</label>
            <div class="flex gap-2">
              <button
                :class="[
                  'flex-1 py-2 rounded-lg text-sm font-medium transition-all',
                  newSubscribe.type === 'artist'
                    ? 'bg-accent text-white'
                    : 'glass text-white/70'
                ]"
                @click="newSubscribe.type = 'artist'"
              >
                艺术家
              </button>
              <button
                :class="[
                  'flex-1 py-2 rounded-lg text-sm font-medium transition-all',
                  newSubscribe.type === 'album'
                    ? 'bg-accent text-white'
                    : 'glass text-white/70'
                ]"
                @click="newSubscribe.type = 'album'"
              >
                专辑
              </button>
            </div>
          </div>
          <Input
            v-model="newSubscribe.name"
            label="名称"
            placeholder="输入艺术家或专辑名称"
          />
        </div>
        <div class="flex gap-3 mt-6">
          <Button variant="secondary" class="flex-1" @click="showAddModal = false">
            取消
          </Button>
          <Button variant="primary" class="flex-1" :loading="adding" @click="addSubscribe">
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

const subscriptions = ref([])
const showAddModal = ref(false)
const adding = ref(false)
const newSubscribe = ref({
  type: 'artist',
  name: '',
})

const fetchSubscriptions = async () => {
  try {
    const response = await fetch('/api/v1/subscribes')
    const data = await response.json()
    subscriptions.value = data.items || []
  } catch (error) {
    console.error('Failed to fetch subscriptions:', error)
  }
}

const addSubscribe = async () => {
  if (!newSubscribe.value.name) return
  
  adding.value = true
  try {
    await fetch('/api/v1/subscribes', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(newSubscribe.value)
    })
    showAddModal.value = false
    newSubscribe.value.name = ''
    await fetchSubscriptions()
  } catch (error) {
    console.error('Failed to add subscribe:', error)
  } finally {
    adding.value = false
  }
}

const deleteSubscribe = async (id: number) => {
  try {
    await fetch(`/api/v1/subscribes/${id}`, { method: 'DELETE' })
    await fetchSubscriptions()
  } catch (error) {
    console.error('Failed to delete subscribe:', error)
  }
}

const formatDate = (date: string) => {
  if (!date) return '从未'
  return new Date(date).toLocaleDateString('zh-CN')
}

onMounted(fetchSubscriptions)
</script>
