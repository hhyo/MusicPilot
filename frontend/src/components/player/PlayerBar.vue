<template>
  <div class="player-bar">
    <!-- 进度条 -->
    <div class="progress-container" @click="handleSeek">
      <div class="progress-bar">
        <div class="progress-fill" :style="{ width: progressPercent + '%' }"></div>
      </div>
    </div>

    <!-- 播放器控制区 -->
    <div class="player-controls">
      <!-- 当前曲目信息 -->
      <div class="track-info" v-if="player.currentTrack">
        <div class="track-title">{{ player.currentTrack.title }}</div>
        <div class="track-artist">Artist ID: {{ player.currentTrack.artist_id }}</div>
      </div>
      <div class="track-info" v-else>
        <div class="track-title">No track selected</div>
      </div>

      <!-- 控制按钮 -->
      <div class="control-buttons">
        <!-- 随机播放 -->
        <button
          class="control-btn"
          :class="{ active: player.shuffle }"
          @click="player.toggleShuffle()"
          title="随机播放"
        >
          <span class="icon">🔀</span>
        </button>

        <!-- 上一首 -->
        <button class="control-btn" @click="player.previous()" :disabled="!player.hasTrack">
          <span class="icon">⏮️</span>
        </button>

        <!-- 播放/暂停 -->
        <button class="control-btn play-btn" @click="player.togglePlay()" :disabled="!player.hasTrack || player.isLoading">
          <span class="icon">{{ player.isLoading ? '⏳' : (player.isPlaying ? '⏸️' : '▶️') }}</span>
        </button>

        <!-- 下一首 -->
        <button class="control-btn" @click="player.next()" :disabled="!player.hasTrack">
          <span class="icon">⏭️</span>
        </button>

        <!-- 循环模式 -->
        <button
          class="control-btn"
          :class="{ active: player.repeatMode !== 'off' }"
          @click="toggleRepeatMode()"
          title="循环模式"
        >
          <span class="icon">{{ repeatModeIcon }}</span>
        </button>
      </div>

      <!-- 时间和音量 -->
      <div class="time-volume">
        <div class="time-display">
          {{ formatTime(player.progress) }} / {{ formatTime(player.duration) }}
        </div>

        <!-- 音量控制 -->
        <div class="volume-control">
          <button class="control-btn" @click="player.toggleMute()" title="静音">
            <span class="icon">{{ volumeIcon }}</span>
          </button>
          <input
            type="range"
            class="volume-slider"
            :value="player.muted ? 0 : player.volume * 100"
            @input="handleVolumeChange"
            min="0"
            max="100"
          />
        </div>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { usePlayerStore } from '@/store/player'
import { computed } from 'vue'

const player = usePlayerStore()

// 循环模式图标
const repeatModeIcon = computed(() => {
  switch (player.repeatMode) {
    case 'one':
      return '🔂' // 单曲循环
    case 'all':
      return '🔁' // 列表循环
    default:
      return '🔁' // 无循环（用同一个图标，无激活状态）
  }
})

// 音量图标
const volumeIcon = computed(() => {
  if (player.muted || player.volume === 0) {
    return '🔇'
  } else if (player.volume < 0.5) {
    return '🔉'
  } else {
    return '🔊'
  }
})

// 进度百分比
const progressPercent = computed(() => player.progressPercent)

// 格式化时间（秒 -> MM:SS）
const formatTime = (seconds: number) => {
  if (!seconds || isNaN(seconds)) return '0:00'
  const mins = Math.floor(seconds / 60)
  const secs = Math.floor(seconds % 60)
  return `${mins}:${secs.toString().padStart(2, '0')}`
}

// 处理进度条点击（跳转）
const handleSeek = (event: MouseEvent) => {
  if (!player.howlInstance || !player.duration) return

  const rect = (event.currentTarget as HTMLElement).getBoundingClientRect()
  const x = event.clientX - rect.left
  const percent = x / rect.width
  const targetSeconds = percent * player.duration

  player.seek(targetSeconds)
}

// 处理音量变化
const handleVolumeChange = (event: Event) => {
  const target = event.target as HTMLInputElement
  const volume = parseInt(target.value) / 100
  player.setVolume(volume)
}

// 切换循环模式
const toggleRepeatMode = () => {
  const modes: ('off' | 'one' | 'all')[] = ['off', 'all', 'one']
  const currentIndex = modes.indexOf(player.repeatMode)
  const nextIndex = (currentIndex + 1) % modes.length
  player.setRepeatMode(modes[nextIndex])
}
</script>

<style scoped>
.player-bar {
  position: fixed;
  bottom: 0;
  left: 0;
  right: 0;
  height: 80px;
  background: var(--card-color);
  border-top: 1px solid var(--border-color);
  display: flex;
  flex-direction: column;
  z-index: 1000;
}

/* 进度条 */
.progress-container {
  height: 4px;
  background: var(--border-color);
  cursor: pointer;
  position: relative;
}

.progress-container:hover .progress-bar {
  height: 6px;
}

.progress-bar {
  height: 4px;
  background: var(--border-color);
  transition: height 0.2s;
}

.progress-fill {
  height: 100%;
  background: var(--primary-color);
  transition: width 0.1s linear;
}

/* 播放器控制区 */
.player-controls {
  flex: 1;
  display: flex;
  align-items: center;
  padding: 0 20px;
  gap: 20px;
}

/* 曲目信息 */
.track-info {
  min-width: 200px;
  max-width: 300px;
}

.track-title {
  font-weight: 500;
  white-space: nowrap;
  overflow: hidden;
  text-overflow: ellipsis;
}

.track-artist {
  font-size: 12px;
  color: var(--text-color-secondary);
  white-space: nowrap;
  overflow: hidden;
  text-overflow: ellipsis;
}

/* 控制按钮 */
.control-buttons {
  display: flex;
  align-items: center;
  gap: 10px;
}

.control-btn {
  display: flex;
  align-items: center;
  justify-content: center;
  width: 40px;
  height: 40px;
  border: none;
  background: transparent;
  cursor: pointer;
  border-radius: 50%;
  color: var(--text-color);
  transition: background 0.2s;
}

.control-btn:hover:not(:disabled) {
  background: var(--hover-color);
}

.control-btn:disabled {
  opacity: 0.3;
  cursor: not-allowed;
}

.control-btn.active {
  color: var(--primary-color);
}

.play-btn {
  width: 48px;
  height: 48px;
  background: var(--primary-color);
  color: white;
}

.play-btn:hover:not(:disabled) {
  background: var(--primary-color-hover);
}

.icon {
  font-size: 20px;
  line-height: 1;
}

/* 时间和音量 */
.time-volume {
  display: flex;
  align-items: center;
  gap: 20px;
  margin-left: auto;
}

.time-display {
  font-size: 12px;
  font-family: monospace;
  color: var(--text-color-secondary);
  min-width: 100px;
  text-align: right;
}

/* 音量控制 */
.volume-control {
  display: flex;
  align-items: center;
  gap: 10px;
}

.volume-slider {
  width: 100px;
  height: 4px;
  background: var(--border-color);
  border-radius: 2px;
  appearance: none;
  outline: none;
}

.volume-slider::-webkit-slider-thumb {
  appearance: none;
  width: 12px;
  height: 12px;
  background: var(--primary-color);
  border-radius: 50%;
  cursor: pointer;
}

.volume-slider::-moz-range-thumb {
  width: 12px;
  height: 12px;
  background: var(--primary-color);
  border-radius: 50%;
  cursor: pointer;
  border: none;
}

/* 响应式 */
@media (max-width: 768px) {
  .track-info {
    min-width: 150px;
    max-width: 200px;
  }

  .control-buttons {
    gap: 5px;
  }

  .control-btn {
    width: 36px;
    height: 36px;
  }

  .play-btn {
    width: 44px;
    height: 44px;
  }

  .volume-slider {
    width: 60px;
  }
}
</style>