/**
 * 播放器状态管理
 * 基于 Howler.js
 */
import { defineStore } from 'pinia'
import { Howl } from 'howler'

export interface Track {
  id: number
  title: string
  artist_id: number
  album_id: number
  duration: number
  path: string
  file_format: string
}

export interface PlaybackSession {
  session_id?: string
  track_id: number
  is_playing: boolean
  position: number
  volume: number
  muted: boolean
  repeat_mode: 'off' | 'one' | 'all'
  shuffle: boolean
}

export const usePlayerStore = defineStore('player', {
  state: () => ({
    currentTrack: null as Track | null,
    isPlaying: false,
    isLoading: false,
    progress: 0,
    duration: 0,
    volume: 1.0,
    muted: false,
    repeatMode: 'off' as 'off' | 'one' | 'all',
    shuffle: false,
    queue: [] as Track[],
    queueIndex: -1,
    history: [] as Track[],
    howlInstance: null as Howl | null,
  }),

  getters: {
    hasTrack: (state) => state.currentTrack !== null,
    hasNext: (state) => state.queueIndex < state.queue.length - 1,
    hasPrevious: (state) => state.queueIndex > 0,
    progressPercent: (state) => (state.duration > 0 ? (state.progress / state.duration) * 100 : 0),
  },

  actions: {
    /**
     * 播放曲目
     */
    async playTrack(track: Track, playImmediately = true) {
      this.isLoading = true

      // 停止当前播放
      if (this.howlInstance) {
        this.howlInstance.unload()
        this.howlInstance = null
      }

      this.currentTrack = track

      // 构建流 URL
      const streamUrl = `/api/v1/tracks/${track.id}/stream`

      // 创建 Howl 实例
      this.howlInstance = new Howl({
        src: [streamUrl],
        html5: true, // 使用 HTML5 Audio 支持流式传输
        format: [track.file_format || 'mp3'],
        volume: this.muted ? 0 : this.volume,
        autoplay: playImmediately,
        onload: () => {
          this.isLoading = false
          console.log('Audio loaded:', track.title)
        },
        onplay: () => {
          this.isPlaying = true
          this.startProgressTimer()
          this.addToHistory(track)
        },
        onpause: () => {
          this.isPlaying = false
          this.stopProgressTimer()
        },
        onstop: () => {
          this.isPlaying = false
          this.stopProgressTimer()
          this.progress = 0
        },
        onend: () => {
          this.isPlaying = false
          this.stopProgressTimer()
          // 处理循环模式
          this.handleTrackEnd()
        },
        onseek: () => {
          // 进度更新在 timer 中处理
        },
      })
    },

    /**
     * 播放/暂停切换
     */
    togglePlay() {
      if (!this.howlInstance) return

      if (this.isPlaying) {
        this.howlInstance.pause()
      } else {
        this.howlInstance.play()
      }
    },

    /**
     * 暂停
     */
    pause() {
      if (this.howlInstance) {
        this.howlInstance.pause()
      }
    },

    /**
     * 停止
     */
    stop() {
      if (this.howlInstance) {
        this.howlInstance.stop()
      }
      this.isPlaying = false
      this.stopProgressTimer()
      this.progress = 0
    },

    /**
     * 下一首
     */
    next() {
      if (!this.hasNext) {
        // 循环模式
        if (this.repeatMode === 'all' && this.queue.length > 0) {
          this.queueIndex = 0
          this.playTrack(this.queue[0])
        } else {
          this.stop()
        }
        return
      }

      this.queueIndex++

      if (this.shuffle) {
        // 随机播放
        const randomIndex = Math.floor(Math.random() * this.queue.length)
        this.queueIndex = randomIndex
      }

      const nextTrack = this.queue[this.queueIndex]
      this.playTrack(nextTrack)
    },

    /**
     * 上一首
     */
    previous() {
      if (!this.hasPrevious) {
        // 循环到最后一首
        if (this.repeatMode === 'all' && this.queue.length > 0) {
          this.queueIndex = this.queue.length - 1
          const lastTrack = this.queue[this.queueIndex]
          this.playTrack(lastTrack)
        } else {
          // 回到当前曲目开头
          this.seek(0)
        }
        return
      }

      this.queueIndex--
      const prevTrack = this.queue[this.queueIndex]
      this.playTrack(prevTrack)
    },

    /**
     * 跳转到指定位置
     */
    seek(seconds: number) {
      if (this.howlInstance) {
        this.howlInstance.seek(seconds)
        this.progress = seconds
      }
    },

    /**
     * 设置音量
     */
    setVolume(volume: number) {
      this.volume = Math.max(0, Math.min(1, volume))
      if (this.howlInstance) {
        this.howlInstance.volume(this.muted ? 0 : this.volume)
      }
    },

    /**
     * 切换静音
     */
    toggleMute() {
      this.muted = !this.muted
      if (this.howlInstance) {
        this.howlInstance.volume(this.muted ? 0 : this.volume)
      }
    },

    /**
     * 设置循环模式
     */
    setRepeatMode(mode: 'off' | 'one' | 'all') {
      this.repeatMode = mode
    },

    /**
     * 切换随机播放
     */
    toggleShuffle() {
      this.shuffle = !this.shuffle
    },

    /**
     * 设置播放队列
     */
    setQueue(tracks: Track[], startIndex = 0) {
      this.queue = [...tracks]
      this.queueIndex = startIndex
    },

    /**
     * 添加曲目到队列
     */
    addToQueue(tracks: Track[]) {
      this.queue.push(...tracks)
    },

    /**
     * 从队列移除曲目
     */
    removeFromQueue(trackId: number) {
      const index = this.queue.findIndex(t => t.id === trackId)
      if (index !== -1) {
        this.queue.splice(index, 1)
        // 调整当前索引
        if (index < this.queueIndex) {
          this.queueIndex--
        }
      }
    },

    /**
     * 清空队列
     */
    clearQueue() {
      this.queue = []
      this.queueIndex = -1
    },

    /**
     * 添加到历史记录
     */
    addToHistory(track: Track) {
      // 移除重复
      this.history = this.history.filter(t => t.id !== track.id)
      // 添加到开头
      this.history.unshift(track)
      // 最多保留 100 条
      if (this.history.length > 100) {
        this.history = this.history.slice(0, 100)
      }
      // 持久化到 localStorage
      this.saveHistory()
    },

    /**
     * 清空历史记录
     */
    clearHistory() {
      this.history = []
      this.saveHistory()
    },

    /**
     * 处理曲目结束
     */
    handleTrackEnd() {
      switch (this.repeatMode) {
        case 'one':
          // 单曲循环
          if (this.currentTrack) {
            this.playTrack(this.currentTrack)
          }
          break
        case 'all':
        case 'off':
        default:
          // 列表循环或无循环
          this.next()
          break
      }
    },

    /**
     * 启动进度定时器
     */
    startProgressTimer() {
      this.stopProgressTimer()

      this.progressTimer = setInterval(() => {
        if (this.howlInstance && this.isPlaying) {
          this.progress = this.howlInstance.seek() as number
          this.duration = this.howlInstance.duration()
        }
      }, 1000) // 每秒更新一次
    },

    /**
     * 停止进度定时器
     */
    stopProgressTimer() {
      if (this.progressTimer) {
        clearInterval(this.progressTimer)
        this.progressTimer = null
      }
    },

    /**
     * 保存历史记录到 localStorage
     */
    saveHistory() {
      try {
        localStorage.setItem('player_history', JSON.stringify(this.history))
      } catch (e) {
        console.error('Failed to save history:', e)
      }
    },

    /**
     * 从 localStorage 加载历史记录
     */
    loadHistory() {
      try {
        const saved = localStorage.getItem('player_history')
        if (saved) {
          this.history = JSON.parse(saved)
        }
      } catch (e) {
        console.error('Failed to load history:', e)
      }
    },

    /**
     * 持久化播放器状态
     */
    saveState() {
      try {
        const state = {
          volume: this.volume,
          muted: this.muted,
          repeatMode: this.repeatMode,
          shuffle: this.shuffle,
          currentTrackId: this.currentTrack?.id,
          queueIndex: this.queueIndex,
          queue: this.queue,
        }
        localStorage.setItem('player_state', JSON.stringify(state))
      } catch (e) {
        console.error('Failed to save player state:', e)
      }
    },

    /**
     * 恢复播放器状态
     */
    loadState() {
      try {
        const saved = localStorage.getItem('player_state')
        if (saved) {
          const state = JSON.parse(saved)
          this.volume = state.volume ?? 1.0
          this.muted = state.muted ?? false
          this.repeatMode = state.repeatMode ?? 'off'
          this.shuffle = state.shuffle ?? false
          this.queueIndex = state.queueIndex ?? -1
          this.queue = state.queue ?? []
        }
      } catch (e) {
        console.error('Failed to load player state:', e)
      }
    },
  },
})

// 自动加载历史记录
export const playerStore = usePlayerStore()
playerStore.loadHistory()
playerStore.loadState()