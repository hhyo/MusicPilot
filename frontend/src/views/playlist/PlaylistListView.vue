<template>
  <div class="playlist-list">
    <n-h1>播放列表</n-h1>
    
    <n-spin :show="loading">
      <n-grid v-if="playlists.length" :cols="4" :x-gap="16" :y-gap="16">
        <n-gi v-for="playlist in playlists" :key="playlist.id">
          <n-card hoverable>
            <n-space vertical align="center">
              <n-avatar :size="80">🎵</n-avatar>
              <n-text strong>{{ playlist.name }}</n-text>
              <n-text depth="3">{{ playlist.description || '' }}</n-text>
            </n-space>
          </n-card>
        </n-gi>
      </n-grid>
      
      <n-empty v-else description="暂无播放列表">
        <template #extra>
          <n-button @click="loadPlaylists">刷新</n-button>
        </template>
      </n-empty>
    </n-spin>
  </div>
</template>

<script setup lang="ts">
import { ref, onMounted } from 'vue'
import { NH1, NEmpty, NButton, NCard, NGrid, NGi, NAvatar, NText, NSpace, NSpin } from 'naive-ui'
import { playlistApi } from '@/api/playlist'

interface Playlist {
  id: number
  name: string
  description?: string
}

const playlists = ref<Playlist[]>([])
const loading = ref(false)

const loadPlaylists = async () => {
  loading.value = true
  try {
    const response = await playlistApi.getList()
    playlists.value = response.data || []
  } catch (error) {
    console.error('Failed to load playlists:', error)
  } finally {
    loading.value = false
  }
}

onMounted(() => {
  loadPlaylists()
})
</script>

<style scoped>
.playlist-list {
  padding: 20px;
}
</style>
