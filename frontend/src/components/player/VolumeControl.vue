<template>
  <div class="volume-control">
    <n-button quaternary circle size="small">
      <template #icon>
        <n-icon :size="16">
          <VolumeMuteIcon v-if="muted" />
          <VolumeLowIcon v-else-if="volume < 0.5" />
          <VolumeHighIcon v-else />
        </n-icon>
      </template>
    </n-button>
    <n-slider
      v-model:value="volume"
      :min="0"
      :max="1"
      :step="0.01"
      style="width: 80px; margin-left: 8px;"
      @update:value="handleVolumeChange"
    />
  </div>
</template>

<script setup lang="ts">
import { computed } from 'vue'
import { NButton, NIcon, NSlider } from 'naive-ui'
import {
  VolumeMuteOutline as VolumeMuteIcon,
  VolumeLowOutline as VolumeLowIcon,
  VolumeHighOutline as VolumeHighIcon,
} from '@vicons/ionicons5'
import { usePlayerStore } from '@/store/player'

const playerStore = usePlayerStore()

const volume = computed({
  get: () => playerStore.volume,
  set: (val: number) => playerStore.setVolume(val)
})

const muted = computed(() => volume.value === 0)

function handleVolumeChange(value: number) {
  playerStore.setVolume(value)
}
</script>

<style scoped>
.volume-control {
  display: flex;
  align-items: center;
  gap: 8px;
  width: 120px;
}
</style>