<template>
  <div class="player-controls">
    <n-button quaternary circle @click="prev">
      <template #icon>
        <n-icon :size="20"><PlaySkipBackIcon /></n-icon>
      </template>
    </n-button>
    <n-button circle size="large" type="primary" @click="togglePlay">
      <template #icon>
        <n-icon :size="24">
          <PlayIcon v-if="!isPlaying" />
          <PauseIcon v-else />
        </n-icon>
      </template>
    </n-button>
    <n-button quaternary circle @click="next">
      <template #icon>
        <n-icon :size="20"><PlaySkipForwardIcon /></n-icon>
      </template>
    </n-button>
  </div>
</template>

<script setup lang="ts">
import { computed } from 'vue'
import { NButton, NIcon } from 'naive-ui'
import {
  PlaySkipBackOutline as PlaySkipBackIcon,
  PlaySkipForwardOutline as PlaySkipForwardIcon,
  PlayOutline as PlayIcon,
  PauseOutline as PauseIcon,
} from '@vicons/ionicons5'
import { usePlayerStore } from '@/store/player'

const playerStore = usePlayerStore()

const isPlaying = computed(() => playerStore.isPlaying)

function togglePlay() {
  if (isPlaying.value) {
    playerStore.pause()
  } else {
    // TODO: 实现播放逻辑
  }
}

function prev() {
  playerStore.prev()
}

function next() {
  playerStore.next()
}
</script>

<style scoped>
.player-controls {
  display: flex;
  align-items: center;
  gap: 8px;
}
</style>