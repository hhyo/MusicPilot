<template>
  <div class="track-list">
    <n-list bordered>
      <n-list-item v-for="(track, index) in tracks" :key="track.id">
        <div class="track-item" @click="playTrack(track)">
          <div class="track-index">{{ index + 1 }}</div>
          <div class="track-cover">
            <img v-if="track.cover" :src="track.cover" alt="封面" />
            <div v-else class="cover-placeholder">
              <n-icon><MusicalNoteIcon /></n-icon>
            </div>
          </div>
          <div class="track-info">
            <div class="track-title">{{ track.title }}</div>
            <div class="track-meta">
              <span class="artist">{{ track.artist }}</span>
              <span v-if="track.album" class="separator">·</span>
              <span v-if="track.album" class="album">{{ track.album }}</span>
            </div>
          </div>
          <div class="track-actions">
            <n-button quaternary circle size="small">
              <template #icon>
                <n-icon><PlayIcon /></n-icon>
              </template>
            </n-button>
            <n-button quaternary circle size="small">
              <template #icon>
                <n-icon><HeartOutlineIcon /></n-icon>
              </template>
            </n-button>
          </div>
        </div>
      </n-list-item>
    </n-list>
  </div>
</template>

<script setup lang="ts">
import { defineProps } from 'vue'
import { NList, NListItem, NButton, NIcon } from 'naive-ui'
import { MusicalNotesOutline as MusicalNoteIcon, PlayOutline as PlayIcon, HeartOutline as HeartOutlineIcon } from '@vicons/ionicons5'
import { usePlayerStore } from '@/store/player'

interface Track {
  id: number
  title: string
  artist?: string
  album?: string
  cover?: string
  duration?: number
}

const props = defineProps<{
  tracks: Track[]
}>()

const playerStore = usePlayerStore()

function playTrack(track: Track) {
  playerStore.playTrack(track)
}
</script>

<style scoped>
.track-item {
  display: flex;
  align-items: center;
  gap: 12px;
  cursor: pointer;
  padding: 8px 0;
}

.track-item:hover {
  background: var(--n-color);
}

.track-index {
  width: 32px;
  text-align: center;
  color: var(--n-text-color-2);
  font-size: 14px;
}

.track-cover {
  width: 48px;
  height: 48px;
  border-radius: 4px;
  overflow: hidden;
  flex-shrink: 0;
}

.track-cover img {
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
  background: var(--n-color);
  color: var(--n-text-color-3);
}

.track-info {
  flex: 1;
  min-width: 0;
}

.track-title {
  font-size: 14px;
  font-weight: 500;
  margin-bottom: 4px;
  white-space: nowrap;
  overflow: hidden;
  text-overflow: ellipsis;
}

.track-meta {
  font-size: 12px;
  color: var(--n-text-color-2);
}

.separator {
  margin: 0 4px;
}

.track-actions {
  display: flex;
  gap: 4px;
}
</style>