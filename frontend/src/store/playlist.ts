import { defineStore } from 'pinia'
import { ref } from 'vue'

export interface Playlist {
  id: number
  name: string
  type: 'normal' | 'smart'
  description?: string
  trackCount?: number
}

export const usePlaylistStore = defineStore('playlist', () => {
  const playlists = ref<Playlist[]>([])
  const currentPlaylist = ref<Playlist | null>(null)
  const loading = ref(false)

  function setPlaylists(pls: Playlist[]) {
    playlists.value = pls
  }

  function setCurrentPlaylist(pl: Playlist) {
    currentPlaylist.value = pl
  }

  function clearCurrentPlaylist() {
    currentPlaylist.value = null
  }

  return {
    playlists,
    currentPlaylist,
    loading,
    setPlaylists,
    setCurrentPlaylist,
    clearCurrentPlaylist,
  }
})