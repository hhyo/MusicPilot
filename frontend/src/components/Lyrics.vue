<template>
  <div class="lyrics-container" ref="containerRef">
    <div class="lyrics-header" v-if="title">
      <div class="lyrics-title">{{ title }}</div>
      <button class="close-btn" @click="$emit('close')">×</button>
    </div>

    <div class="lyrics-content" ref="contentRef">
      <div v-if="!lyrics || lyrics.length === 0" class="lyrics-empty">
        <div class="empty-icon">🎵</div>
        <div class="empty-text">暂无歌词</div>
        <button class="load-btn" @click="loadLyrics" :loading="loading">
          {{ loading ? '加载中...' : '搜索歌词' }}
        </button>
      </div>

      <div v-else class="lyrics-lines">
        <div
          v-for="(line, index) in lyrics"
          :key="index"
          class="lyrics-line"
          :class="{ active: index === currentIndex }"
          :style="getLineStyle(index)"
          @click="seekToLine(line.time)"
        >
          <div class="lyrics-text">{{ line.text }}</div>
          <div v-if="line.translation" class="lyrics-translation">{{ line.translation }}</div>
        </div>
      </div>
    </div>

    <!-- 时间标记 -->
    <div class="lyrics-time" v-if="lyrics && lyrics.length > 0">
      {{ formatTime(currentTime) }}
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, computed, watch, onMounted, onUnmounted, nextTick } from 'vue'
import { usePlayerStore } from '@/store/player'

interface LyricLine {
  time: number  // 时间（秒）
  text: string
  translation?: string
}

interface Props {
  trackId?: number
  title?: string
  artist?: string
}

const props = defineProps<Props>()

defineEmits<{
  close: []
}>()

const player = usePlayerStore()

const containerRef = ref<HTMLDivElement>()
const contentRef = ref<HTMLDivElement>()
const lyrics = ref<LyricLine[]>([])
const currentIndex = ref(-1)
const currentTime = ref(0)
const loading = ref(false)
let updateTimer: number | null = null

/**
 * 解析 LRC 歌词
 */
const parseLrc = (lrcText: string): LyricLine[] => {
  const lines: LyricLine[] = []
  const timeRegex = /\[(\d{2}):(\d{2})(?:\.(\d{2,3}))?\](.*)/
  const linesText = lrcText.split('\n')

  linesText.forEach(lineText => {
    const match = lineText.match(timeRegex)
    if (match) {
      const minutes = parseInt(match[1], 10)
      const seconds = parseInt(match[2], 10)
      const milliseconds = match[3] ? parseInt(match[3].padEnd(3, '0'), 10) : 0
      const text = match[4].trim()

      if (text) {
        const time = minutes * 60 + seconds + milliseconds / 1000
        lines.push({ time, text })
      }
    }
  })

  return lines.sort((a, b) => a.time - b.time)
}

/**
 * 加载歌词
 */
const loadLyrics = async () => {
  if (!props.trackId) return

  loading.value = true

  try {
    // TODO: 从 API 获取歌词
    // const response = await fetchLyrics(props.trackId)
    // const lrcText = response.lyrics

    // 临时：模拟歌词
    const mockLyrics = `[00:00.00]MusicPilot
[00:02.00]这是一个测试歌词
[00:05.00]第一行歌词内容
[00:10.00]第二行歌词内容
[00:15.00]第三行歌词内容
[00:20.00]MusicPilot 播放器
[00:25.00]让音乐更美好
[00:30.00]让生活更精彩
[00:35.00]...`

    lyrics.value = parseLrc(mockLyrics)

    // 开始同步
    startSync()
  } catch (error) {
    console.error('加载歌词失败:', error)
  } finally {
    loading.value = false
  }
}

/**
 * 开始同步歌词
 */
const startSync = () => {
  stopSync()

  updateTimer = window.setInterval(() => {
    currentTime.value = player.progress

    // 找到当前应该显示的歌词行
    let newIndex = -1
    for (let i = lyrics.value.length - 1; i >= 0; i--) {
      if (lyrics.value[i].time <= currentTime.value) {
        newIndex = i
        break
      }
    }

    if (newIndex !== currentIndex.value) {
      currentIndex.value = newIndex
      scrollToCurrentLine()
    }
  }, 100)
}

/**
 * 停止同步
 */
const stopSync = () => {
  if (updateTimer) {
    clearInterval(updateTimer)
    updateTimer = null
  }
}

/**
 * 滚动到当前歌词行
 */
const scrollToCurrentLine = async () => {
  if (currentIndex.value < 0 || !contentRef.value) return

  await nextTick()

  const lines = contentRef.value.querySelectorAll('.lyrics-line')
  const currentLine = lines[currentIndex.value]

  if (currentLine) {
    currentLine.scrollIntoView({
      behavior: 'smooth',
      block: 'center',
    })
  }
}

/**
 * 获取歌词行样式
 */
const getLineStyle = (index: number) => {
  const isActive = index === currentIndex.value
  const isBefore = index < currentIndex.value
  const isAfter = index > currentIndex.value

  if (isActive) {
    return {
      opacity: 1,
      transform: 'scale(1.05)',
      fontWeight: 500,
    }
  } else if (isBefore) {
    return {
      opacity: 0.5,
    }
  } else {
    return {
      opacity: 0.7,
    }
  }
}

/**
 * 点击歌词行跳转到对应时间
 */
const seekToLine = (time: number) => {
  player.seek(time)
}

/**
 * 格式化时间
 */
const formatTime = (seconds: number) => {
  const mins = Math.floor(seconds / 60)
  const secs = Math.floor(seconds % 60)
  return `${mins}:${secs.toString().padStart(2, '0')}`
}

// 监听曲目变化
watch(() => props.trackId, () => {
  lyrics.value = []
  currentIndex.value = -1
  if (props.trackId) {
    loadLyrics()
  }
})

// 监听播放状态
watch(() => player.isPlaying, (isPlaying) => {
  if (isPlaying && lyrics.value.length > 0) {
    startSync()
  } else {
    stopSync()
  }
})

// 挂载时加载
onMounted(() => {
  if (props.trackId) {
    loadLyrics()
  }
})

// 卸载时清理
onUnmounted(() => {
  stopSync()
})

defineExpose({
  loadLyrics,
})
</script>

<style scoped>
.lyrics-container {
  display: flex;
  flex-direction: column;
  height: 100%;
  background: linear-gradient(180deg, rgba(24, 24, 27, 0.95) 0%, rgba(0, 0, 0, 0.98) 100%);
  border-radius: 12px;
  overflow: hidden;
}

/* 歌词头部 */
.lyrics-header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: 16px 20px;
  border-bottom: 1px solid rgba(255, 255, 255, 0.1);
}

.lyrics-title {
  font-size: 16px;
  font-weight: 500;
  color: var(--text-color);
}

.close-btn {
  display: flex;
  align-items: center;
  justify-content: center;
  width: 32px;
  height: 32px;
  border: none;
  background: transparent;
  color: var(--text-color-secondary);
  font-size: 24px;
  cursor: pointer;
  border-radius: 50%;
  transition: all 0.2s;
}

.close-btn:hover {
  background: rgba(255, 255, 255, 0.1);
  color: var(--text-color);
}

/* 歌词内容 */
.lyrics-content {
  flex: 1;
  overflow-y: auto;
  padding: 20px 0;
  scroll-behavior: smooth;
}

/* 空状态 */
.lyrics-empty {
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  height: 100%;
  gap: 16px;
}

.empty-icon {
  font-size: 64px;
  opacity: 0.3;
}

.empty-text {
  font-size: 14px;
  color: var(--text-color-secondary);
}

.load-btn {
  padding: 8px 20px;
  background: var(--primary-color);
  color: white;
  border: none;
  border-radius: 8px;
  font-size: 14px;
  cursor: pointer;
  transition: background 0.2s;
}

.load-btn:hover {
  background: var(--primary-color-hover);
}

.load-btn:disabled {
  opacity: 0.5;
  cursor: not-allowed;
}

/* 歌词行 */
.lyrics-lines {
  padding: 0 20px;
}

.lyrics-line {
  padding: 16px 20px;
  border-radius: 8px;
  cursor: pointer;
  transition: all 0.3s ease;
  margin-bottom: 4px;
}

.lyrics-line:hover {
  background: rgba(255, 255, 255, 0.05);
}

.lyrics-line.active .lyrics-text {
  color: var(--primary-color);
}

.lyrics-text {
  font-size: 16px;
  color: var(--text-color);
  line-height: 1.6;
  transition: all 0.3s ease;
}

.lyrics-translation {
  font-size: 14px;
  color: var(--text-color-secondary);
  margin-top: 4px;
}

/* 时间标记 */
.lyrics-time {
  padding: 12px 20px;
  font-size: 12px;
  color: var(--text-color-secondary);
  font-family: monospace;
  text-align: center;
  border-top: 1px solid rgba(255, 255, 255, 0.1);
}

/* 滚动条 */
.lyrics-content::-webkit-scrollbar {
  width: 6px;
}

.lyrics-content::-webkit-scrollbar-track {
  background: transparent;
}

.lyrics-content::-webkit-scrollbar-thumb {
  background: rgba(255, 255, 255, 0.2);
  border-radius: 3px;
}

.lyrics-content::-webkit-scrollbar-thumb:hover {
  background: rgba(255, 255, 255, 0.3);
}
</style>