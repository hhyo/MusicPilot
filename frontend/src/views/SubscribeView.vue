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

    <!-- Loading State -->
    <div v-if="loading" class="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
      <div v-for="i in 6" :key="i" class="animate-pulse">
        <GlassCard>
          <div class="flex items-center gap-4">
            <div class="w-12 h-12 rounded-xl bg-white/10"></div>
            <div class="flex-1">
              <div class="h-4 bg-white/10 rounded w-1/2 mb-2"></div>
              <div class="h-3 bg-white/10 rounded w-1/3"></div>
            </div>
          </div>
        </GlassCard>
      </div>
    </div>

    <!-- Subscriptions List -->
    <div v-else class="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
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
              <p class="text-sm text-white/60">{{ getTypeLabel(sub.type) }}</p>
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
          <span>状态: {{ getStateLabel(sub.state) }}</span>
          <span>更新: {{ formatDate(sub.last_update) }}</span>
        </div>
      </GlassCard>
    </div>

    <!-- Empty State -->
    <div v-if="!loading && !subscriptions.length" class="text-center py-20">
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
          <Input
            v-model="newSubscribe.musicbrainz_id"
            label="MusicBrainz ID (可选)"
            placeholder="例如: test-artist"
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
import { subscribeApi } from '@/api/client'

const subscriptions = ref<any[]>([])
const loading = ref(false)
const showAddModal = ref(false)
const adding = ref(false)
const newSubscribe = ref({
  type: 'artist',
  name: '',
  musicbrainz_id: '',
})

const getTypeLabel = (type: string) => {
  const map: Record<string, string> = {
    artist: '艺术家',
    album: '专辑',
    playlist: '播放列表',
    chart: '榜单',
  }
  return map[type] || type
}

const getStateLabel = (state: string) => {
  const map: Record<string, string> = {
    active: '活跃',
    pending: '等待中',
    disabled: '已禁用',
  }
  return map[state] || state
}

const fetchSubscriptions = async () => {
  loading.value = true
  try {
    const res = await subscribeApi.list({ limit: 100 })
    // API returns { items, total, page, page_size }
    subscriptions.value = res.items || []
  } catch (error) {
    console.error('Failed to fetch subscriptions:', error)
    subscriptions.value = []
  } finally {
    loading.value = false
  }
}

const addSubscribe = async () => {
  if (!newSubscribe.value.name) return
  
  adding.value = true
  try {
    await subscribeApi.create({
      type: newSubscribe.value.type,
      name: newSubscribe.value.name,
      musicbrainz_id: newSubscribe.value.musicbrainz_id || undefined,
    })
    showAddModal.value = false
    newSubscribe.value = { type: 'artist', name: '', musicbrainz_id: '' }
    await fetchSubscriptions()
  } catch (error) {
    console.error('Failed to add subscribe:', error)
    alert('添加订阅失败')
  } finally {
    adding.value = false
  }
}

const deleteSubscribe = async (id: number) => {
  if (!confirm('确定要删除这个订阅吗？')) return
  
  try {
    await subscribeApi.delete(id)
    await fetchSubscriptions()
  } catch (error) {
    console.error('Failed to delete subscribe:', error)
    alert('删除订阅失败')
  }
}

const formatDate = (date: string) => {
  if (!date) return '从未'
  return new Date(date).toLocaleDateString('zh-CN')
}

onMounted(fetchSubscriptions)
</script>