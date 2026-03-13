<template>
  <div
    class="group cursor-pointer"
    @click="$router.push(`/albums/${album.id}`)"
  >
    <div class="relative aspect-square rounded-xl overflow-hidden mb-3">
      <img
        :src="album.cover || '/default-album.png'"
        :alt="album.title"
        class="w-full h-full object-cover transition-transform duration-300 group-hover:scale-110"
      />
      <div class="absolute inset-0 bg-black/40 opacity-0 group-hover:opacity-100 transition-opacity flex items-center justify-center">
        <button class="w-12 h-12 rounded-full bg-accent text-white flex items-center justify-center hover:scale-110 transition-transform">
          <svg class="w-6 h-6" fill="currentColor" viewBox="0 0 24 24">
            <path d="M8 5v14l11-7z"/>
          </svg>
        </button>
      </div>
    </div>
    <h3 class="font-medium truncate group-hover:text-accent transition-colors">{{ album.title }}</h3>
    <p class="text-sm text-white/60 truncate">{{ album.artist }}</p>
  </div>
</template>

<script setup lang="ts">
interface Album {
  id: number
  title: string
  artist: string
  cover: string
}

defineProps<{
  album: Album
}>()
</script>
