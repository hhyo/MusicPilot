<template>
  <div class="album-list">
    <n-h1>专辑列表</n-h1>
    
    <n-spin :show="loading">
      <n-grid v-if="albums.length" :cols="4" :x-gap="16" :y-gap="16">
        <n-gi v-for="album in albums" :key="album.id">
          <n-card hoverable>
            <n-space vertical align="center">
              <n-avatar v-if="album.cover_url" :src="album.cover_url" :size="80" />
              <n-avatar v-else :size="80">{{ album.title?.charAt(0) }}</n-avatar>
              <n-text strong>{{ album.title }}</n-text>
              <n-text depth="3">{{ album.year || '' }}</n-text>
            </n-space>
          </n-card>
        </n-gi>
      </n-grid>
      
      <n-empty v-else description="暂无专辑数据">
        <template #extra>
          <n-button @click="loadAlbums">刷新</n-button>
        </template>
      </n-empty>
    </n-spin>
  </div>
</template>

<script setup lang="ts">
import { ref, onMounted } from 'vue'
import { NH1, NEmpty, NButton, NCard, NGrid, NGi, NAvatar, NText, NSpace, NSpin } from 'naive-ui'
import { albumApi } from '@/api/album'

interface Album {
  id: number
  title: string
  year?: number
  cover_url?: string
}

const albums = ref<Album[]>([])
const loading = ref(false)

const loadAlbums = async () => {
  loading.value = true
  try {
    const response = await albumApi.getList()
    albums.value = response.data || []
  } catch (error) {
    console.error('Failed to load albums:', error)
  } finally {
    loading.value = false
  }
}

onMounted(() => {
  loadAlbums()
})
</script>

<style scoped>
.album-list {
  padding: 20px;
}
</style>
