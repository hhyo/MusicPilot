<template>
  <div class="player-bar glass border-t border-white/10">
    <!-- 进度条 -->
    <div 
      class="h-1 bg-white/10 cursor-pointer group relative" 
      @click="handleSeek"
    >
      <div 
        class="h-full bg-accent transition-all duration-100 relative"
        :style="{ width: progressPercent + '%' }"
      >
        <!-- 进度条悬停指示器 -->
        <div class="absolute right-0 top-1/2 -translate-y-1/2 w-3 h-3 bg-accent rounded-full opacity-0 group-hover:opacity-100 transition-opacity shadow-lg shadow-accent/50"></div>
      </div>
    </div>

    <!-- 播放器控制区 -->
    <div class="flex items-center h-20 px-4 gap-4 md:gap-6">
      <!-- 当前曲目信息 -->
      <div class="flex items-center gap-3 min-w-0 flex-1 max-w-[200px] md:max-w-[300px] lg:max-w-[400px]">
        <div 
          v-if="player.currentTrack"
          class="w-12 h-12 md:w-14 md:h-14 rounded-lg bg-gradient-to-br from-accent/20 to-accent/10 flex items-center justify-center text-xl shrink-0"
        >
          🎵
        </div>
        <div v-else class="w-12 h-12 md:w-14 md:h-14 rounded-lg bg-white/5 flex items-center justify-center text-xl shrink-0">
          🎵
        </div>
        <div class="min-w-0">
          <div v-if="player.currentTrack" class="font-medium truncate hover:text-accent transition-colors">
            {{ player.currentTrack.title }}
          </div>
          <div v-else class="text-white/40">未选择曲目</div>
          <div v-if="player.currentTrack" class="text-white/50 text-sm truncate">
            Artist ID: {{ player.currentTrack.artist_id }}
          </div>
        </div>
      </div>

      <!-- 控制按钮 -->
      <div class="flex items-center gap-1 md:gap-2">
        <!-- 随机播放 -->
        <button
          class="control-btn"
          :class="{ 'text-accent': player.shuffle }"
          @click="player.toggleShuffle()"
          title="随机播放"
        >
          <span class="text-sm md:text-base">🔀</span>
        </button>

        <!-- 上一首 -->
        <button 
          class="control-btn" 
          @click="player.previous()" 
          :disabled="!player.hasTrack"
          title="上一首"
        >
          <span class="text-sm md:text-base">⏮️</span>
        </button>

        <!-- 播放/暂停 -->
        <button 
          class="control-btn play-btn" 
          @click="player.togglePlay()" 
          :disabled="!player.hasTrack || player.isLoading"
          title="{{ player.isPlaying ? '暂停' : '播放' }}"
        >
          <span class="text-lg md:text-xl">
            {{ player.isLoading ? '⏳' : (player.isPlaying ? '⏸️' : '▶️') }}
          </span>
        </button>

        <!-- 下一首 -->
        <button 
          class="control-btn" 
          @click="player.next()" 
          :disabled="!player.hasTrack"
          title="下一首"
        >
          <span class="text-sm md:text-base">⏭️</span>
        </button>

        <!-- 循环模式 -->
        <button
          class="control-btn"
          :class="{ 'text-accent': player.repeatMode !== 'off' }"
          @click="toggleRepeatMode()"
          title="循环模式"
        >
          <span class="text-sm md:text-base">{{ repeatModeIcon }}</span>
        </button>
      </div>

      <!-- 时间和音量 (桌面端) -->
      <div class="hidden md:flex items-center gap-4 shrink-0">
        <div class="text-xs md:text-sm text-white/50 font-mono whitespace-nowrap">
          {{ formatTime(player.progress) }} / {{ formatTime(player.duration) }}
        </div>

        <!-- 音量控制 -->
        <div class="flex items-center gap-2 group">
          <button 
            class="control-btn p-1" 
            @click="player.toggleMute()" 
            title="静音"
          >
            <span class="text-sm">{{ volumeIcon }}</span>
          </button>
          <div class="w-20 lg:w-24 h-1 bg-white/20 rounded-full overflow-hidden cursor-pointer group-hover:h-1.5 transition-all">
            <div 
              class="h-full bg-accent transition-all"
              :style="{ width: (player.muted ? 0 : player.volume) * 100 + '%' }"
            ></div>
            <input
              type="range"
              class="absolute inset-0 w-full h-full opacity-0 cursor-pointer"
              :value="player.muted ? 0 : player.volume * 100"
              @input="handleVolumeChange"
              min="0"
              max="100"
            />
          </div>
        </div>
      </div>
    </div>

    <!-- 移动端简化控制 -->
    <div class="md:hidden flex items-center justify-between px-4 pb-3">
      <div class="text-xs text-white/50 font-mono">
        {{ formatTime(player.progress) }}
      </div>
      <div class="flex items-center gap-2">
        <button 
          class="p-2" 
          @click="player.toggleMute()" 
          title="静音"
        >
          <span class="text-sm">{{ volumeIcon }}</span>
        </button>
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
      return '🔂'
    case 'all':
      return '🔁'
    default:
      return '🔁'
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

// 格式化时间
const formatTime = (seconds: number) => {
  if (!seconds || isNaN(seconds)) return '0:00'
  const mins = Math.floor(seconds / 60)
  const secs = Math.floor(seconds % 60)
  return `${mins}:${secs.toString().padStart(2, '0')}`
}

// 处理进度条点击
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
  z-index: 1000;
  background: rgba(15, 15, 15, 0.8);
  backdrop-filter: blur(20px);
  -webkit-backdrop-filter: blur(20px);
}

/* 控制按钮 */
.control-btn {
  display: flex;
  align-items: center;
  justify-content: center;
  width: 36px;
  h-height: 36px;
  width: 40px;
  height: 40px;
  border: none;
  background: transparent;
  cursor: pointer;
  border-radius: 50%;
  color: white;
  transition: all 0.2s;
}

.control-btn:hover:not(:disabled) {
  background: rgba(255, 255, 255, 0.1);
  transform: scale(1.1);
}

.control-btn:disabled {
  opacity: 0.3;
  cursor: not-allowed;
}

.control-btn:disabled:hover {
  transform: none;
}

/* 播放按钮 */
.play-btn {
  width: 44px;
  height: 44px;
  background: white;
  color: black;
}

.play-btn:hover:not(:disabled) {
  background: #1ed760;
  transform: scale(1.1);
}
</style>