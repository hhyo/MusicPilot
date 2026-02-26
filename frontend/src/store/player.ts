import { defineStore } from 'pinia'
import { ref } from 'vue'

export interface Track {
  id: number
  title: string
  artist?: string
  album?: string
  duration?: number
  path?: string
}

export const usePlayerStore = defineStore('player', () => {
  const currentTrack = ref<Track | null>(null)
  const isPlaying = ref(false)
  const progress = ref(0)
  const duration = ref(0)
  const volume = ref(1.0)
  const repeatMode = ref<'off' | 'one' | 'all'>('off')
  const shuffle = ref(false)
  const playlist = ref<Track[]>([])
  const history = ref<Track[]>([])

  function playTrack(track: Track) {
    if (currentTrack.value) {
      history.value.push(currentTrack.value)
    }
    currentTrack.value = track
    isPlaying.value = true
    progress.value = 0
  }

  function pause() {
    isPlaying.value = false
  }

  function stop() {
    isPlaying.value = false
    currentTrack.value = null
    progress.value = 0
  }

  function next() {
    if (!playlist.value.length) return
    const currentIndex = playlist.value.findIndex(t => t.id === currentTrack.value?.id)
    if (currentIndex === -1) return

    const nextIndex = shuffle.value
      ? Math.floor(Math.random() * playlist.value.length)
      : (currentIndex + 1) % playlist.value.length

    playTrack(playlist.value[nextIndex])
  }

  function prev() {
    if (!playlist.value.length) return
    const currentIndex = playlist.value.findIndex(t => t.id === currentTrack.value?.id)
    if (currentIndex === -1) return

    const prevIndex = shuffle.value
      ? Math.floor(Math.random() * playlist.value.length)
      : (currentIndex - 1 + playlist.value.length) % playlist.value.length

    playTrack(playlist.value[prevIndex])
  }

  function seek(position: number) {
    progress.value = position
  }

  function setVolume(vol: number) {
    volume.value = vol
  }

  function setRepeatMode(mode: 'off' | 'one' | 'all') {
    repeatMode.value = mode
  }

  function toggleShuffle() {
    shuffle.value = !shuffle.value
  }

  function setPlaylist(tracks: Track[]) {
    playlist.value = tracks
  }

  return {
    currentTrack,
    isPlaying,
    progress,
    duration,
    volume,
    repeatMode,
    shuffle,
    playlist,
    history,
    playTrack,
    pause,
    stop,
    next,
    prev,
    seek,
    setVolume,
    setRepeatMode,
    toggleShuffle,
    setPlaylist,
  }
})