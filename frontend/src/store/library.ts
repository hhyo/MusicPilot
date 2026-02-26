import { defineStore } from 'pinia'
import { ref } from 'vue'

export interface Library {
  id: number
  name: string
  path: string
  trackCount?: number
  albumCount?: number
  artistCount?: number
}

export const useLibraryStore = defineStore('library', () => {
  const libraries = ref<Library[]>([])
  const currentLibrary = ref<Library | null>(null)
  const loading = ref(false)

  function setLibraries(libs: Library[]) {
    libraries.value = libs
  }

  function setCurrentLibrary(lib: Library) {
    currentLibrary.value = lib
  }

  function clearCurrentLibrary() {
    currentLibrary.value = null
  }

  return {
    libraries,
    currentLibrary,
    loading,
    setLibraries,
    setCurrentLibrary,
    clearCurrentLibrary,
  }
})