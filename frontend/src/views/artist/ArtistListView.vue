<template>
  <div class="artist-list">
    <n-h1>艺术家列表</n-h1>
    
    <n-spin :show="loading">
      <n-grid v-if="artists.length" :cols="4" :x-gap="16" :y-gap="16">
        <n-gi v-for="artist in artists" :key="artist.id">
          <n-card hoverable>
            <n-space vertical align="center">
              <n-avatar v-if="artist.image_url" :src="artist.image_url" :size="80" />
              <n-avatar v-else :size="80">{{ artist.name?.charAt(0) }}</n-avatar>
              <n-text strong>{{ artist.name }}</n-text>
            </n-space>
          </n-card>
        </n-gi>
      </n-grid>
      
      <n-empty v-else description="暂无艺术家数据">
        <template #extra>
          <n-button @click="loadArtists">刷新</n-button>
        </template>
      </n-empty>
    </n-spin>
  </div>
</template>

<script setup lang="ts">
import { ref, onMounted } from 'vue'
import { NH1, NEmpty, NButton, NCard, NGrid, NGi, NAvatar, NText, NSpace, NSpin } from 'naive-ui'
import { artistApi } from '@/api/artist'

interface Artist {
  id: number
  name: string
  image_url?: string
}

const artists = ref<Artist[]>([])
const loading = ref(false)

const loadArtists = async () => {
  loading.value = true
  try {
    const response = await artistApi.getList()
    artists.value = response.data?.data || []
  } catch (error) {
    console.error('Failed to load artists:', error)
  } finally {
    loading.value = false
  }
}

onMounted(() => {
  loadArtists()
})
</script>

<style scoped>
.artist-list {
  padding: 20px;
}
</style>
