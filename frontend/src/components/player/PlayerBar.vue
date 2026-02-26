<template>
  <div class="player-bar">
    <div class="track-info">
      <div class="album-cover">
        <img v-if="currentTrack" :src="currentTrack.cover || defaultCover" alt="封面" />
      </div>
      <div class="track-details">
        <div class="track-title">{{ currentTrack?.title || '未播放' }}</div>
        <div class="track-artist">{{ currentTrack?.artist || '-' }}</div>
      </div>
    </div>
    <PlayerControls />
    <ProgressBar />
    <VolumeControl />
  </div>
</template>

<script setup lang="ts">
import { computed } from 'vue'
import { usePlayerStore } from '@/store/player'
import PlayerControls from './PlayerControls.vue'
import ProgressBar from './ProgressBar.vue'
import VolumeControl from './VolumeControl.vue'

const playerStore = usePlayerStore()
const currentTrack = computed(() => playerStore.currentTrack)
const defaultCover = 'data:image/svg+xml,%3Csvg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 24 24" fill="%23666"%3E%3Crect width="24" height="24"/%3E%3C/svg%3E'
</script>

<style scoped>
.player-bar {
  height: 80px;
  display: flex;
  align-items: center;
  padding: 0 20px;
  border-top: 1px solid var(--n-border-color);
  background: var(--n-color);
}

.track-info {
  display: flex;
  align-items: center;
  width: 240px;
  gap: 12px;
}

.album-cover img {
  width: 48px;
  height: 48px;
  border-radius: 4px;
  object-fit: cover;
}

.track-details {
  flex: 1;
  overflow: hidden;
}

.track-title {
  font-size: 14px;
  font-weight: 500;
  white-space: nowrap;
  overflow: hidden;
  text-overflow: ellipsis;
}

.track-artist {
  font-size: 12px;
  color: var(--n-text-color-2);
}
</style>