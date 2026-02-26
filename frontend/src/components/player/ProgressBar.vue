<template>
  <div class="progress-bar">
    <span class="time current">{{ formatTime(currentTime) }}</span>
    <n-slider
      v-model:value="progress"
      :step="0.01"
      :max="100"
      style="flex: 1; margin: 0 12px;"
      @update:value="handleSeek"
    />
    <span class="time duration">{{ formatTime(duration) }}</span>
  </div>
</template>

<script setup lang="ts">
import { computed } from 'vue'
import { NSlider } from 'naive-ui'
import { usePlayerStore } from '@/store/player'

const playerStore = usePlayerStore()

const progress = computed({
  get: () => playerStore.progress,
  set: (val: number) => playerStore.seek(val / 100 * playerStore.duration)
})

const currentTime = computed(() => (progress.value / 100) * playerStore.duration)
const duration = computed(() => playerStore.duration)

function handleSeek(value: number) {
  playerStore.seek(value / 100 * duration.value)
}

function formatTime(seconds: number): string {
  if (!seconds || isNaN(seconds)) return '0:00'
  const mins = Math.floor(seconds / 60)
  const secs = Math.floor(seconds % 60)
  return `${mins}:${secs.toString().padStart(2, '0')}`
}
</script>

<style scoped>
.progress-bar {
  display: flex;
  align-items: center;
  flex: 1;
  max-width: 400px;
}

.time {
  font-size: 12px;
  color: var(--n-text-color-2);
  min-width: 40px;
}

.current {
  text-align: right;
}

.duration {
  text-align: left;
}
</style>