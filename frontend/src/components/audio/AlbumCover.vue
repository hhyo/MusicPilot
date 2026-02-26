<template>
  <div class="album-cover">
    <img v-if="coverUrl" :src="coverUrl" :alt="title" @error="handleError" />
    <div v-else class="cover-placeholder">
      <n-icon :size="40"><AlbumIcon /></n-icon>
    </div>
    <div v-if="playing" class="playing-indicator">
      <n-icon :size="16"><MusicalNoteIcon /></n-icon>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref } from 'vue'
import { NIcon } from 'naive-ui'
import { MusicalNoteOutline as MusicalNoteIcon, AlbumOutline as AlbumIcon } from '@vicons/ionicons5'

defineProps<{
  coverUrl?: string
  title?: string
  playing?: boolean
}>()

const defaultCover = 'data:image/svg+xml,%3Csvg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 24 24" fill="%23666"%3E%3Crect width="24" height="24"/%3E%3C/svg%3E'

function handleError() {
  console.warn('封面加载失败')
}
</script>

<style scoped>
.album-cover {
  position: relative;
  width: 100%;
  aspect-ratio: 1;
  border-radius: 8px;
  overflow: hidden;
  background: var(--n-color);
}

.album-cover img {
  width: 100%;
  height: 100%;
  object-fit: cover;
}

.cover-placeholder {
  width: 100%;
  height: 100%;
  display: flex;
  align-items: center;
  justify-content: center;
  color: var(--n-text-color-3);
}

.playing-indicator {
  position: absolute;
  bottom: 8px;
  right: 8px;
  width: 32px;
  height: 32px;
  border-radius: 50%;
  background: var(--n-primary-color);
  display: flex;
  align-items: center;
  justify-content: center;
  color: white;
}
</style>