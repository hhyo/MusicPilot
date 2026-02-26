<template>
  <div class="artist-detail-view">
    <n-page-header title="艺术家详情" @back="goBack" />
    <Loading :loading="loading" description="加载中...">
      <n-empty v-if="!loading && !artist" description="艺术家不存在" />
      <div v-else-if="artist">
        <div class="artist-header">
          <ArtistAvatar :avatar-url="artist.image_url" :name="artist.name" size="large" />
          <div class="artist-info">
            <h1 class="artist-name">{{ artist.name }}</h1>
            <p v-if="artist.biography" class="artist-bio">{{ artist.biography }}</p>
            <div class="artist-tags">
              <n-tag v-for="genre in (artist.genres || [])" :key="genre">{{ genre }}</n-tag>
            </div>
          </div>
        </div>

        <n-card title="专辑" style="margin-top: 24px">
          <Loading :loading="albumsLoading" description="加载专辑中...">
            <n-empty v-if="!albumsLoading && !albums.length" description="暂无专辑" />
            <n-grid v-else x-gap="16" y-gap="16" :cols="responsiveCols">
              <n-grid-item v-for="album in albums" :key="album.id">
                <div class="album-item" @click="goToAlbum(album.id)">
                  <AlbumCover :cover-url="album.cover_url" :title="album.title" />
                  <div class="album-info">
                    <div class="album-title">{{ album.title }}</div>
                    <div class="album-year">{{ album.release_date?.substring(0, 4) }}</div>
                  </div>
                </div>
              </n-grid-item>
            </n-grid>
          </Loading>
        </n-card>

        <n-card title="热门曲目" style="margin-top: 16px">
          <Loading :loading="tracksLoading" description="加载曲目中...">
            <TrackList v-if="tracks.length" :tracks="tracks" />
          </Loading>
        </n-card>
      </div>
    </Loading>
  </div>
</template>

<script setup lang="ts">
import { ref, onMounted, computed } from 'vue'
import { useRouter, useRoute } from 'vue-router'
import { NPageHeader, NEmpty, NCard, NTag, NGrid, NGridItem } from 'naive-ui'
import ArtistAvatar from '@/components/audio/ArtistAvatar.vue'
import AlbumCover from '@/components/audio/AlbumCover.vue'
import TrackList from '@/components/audio/TrackList.vue'
import Loading from '@/components/common/Loading.vue'

const router = useRouter()
const route = useRoute()

const loading = ref(false)
const albumsLoading = ref(false)
const tracksLoading = ref(false)
const artist = ref<any>(null)
const albums = ref<any[]>([])
const tracks = ref<any[]>([])

const responsiveCols = computed(() => ({
  xs: 2,
  sm: 3,
  md: 4,
  lg: 5,
  xl: 6,
}))

const artistId = computed(() => Number(route.params.id))

onMounted(async () => {
  await loadArtist()
  await loadAlbums()
  await loadTracks()
})

async function loadArtist() {
  loading.value = true
  try {
    // TODO: 调用 artistApi.getById(artistId.value)
  } finally {
    loading.value = false
  }
}

async function loadAlbums() {
  albumsLoading.value = true
  try {
    // TODO: 调用 artist 的专辑 API
  } finally {
    albumsLoading.value = false
  }
}

async function loadTracks() {
  tracksLoading.value = true
  try {
    // TODO: 调用 trackApi.getByArtistId()
  } finally {
    tracksLoading.value = false
  }
}

function goToAlbum(id: number) {
  router.push({ name: 'AlbumDetail', params: { id } })
}

function goBack() {
  router.back()
}
</script>

<style scoped>
.artist-detail-view {
  padding: 20px;
}

.artist-header {
  display: flex;
  gap: 24px;
  margin-bottom: 24px;
}

.artist-info {
  flex: 1;
}

.artist-name {
  font-size: 32px;
  font-weight: 600;
  margin: 0 0 12px 0;
}

.artist-bio {
  color: var(--n-text-color-2);
  margin: 0 0 16px 0;
  line-height: 1.6;
}

.artist-tags {
  display: flex;
  gap: 8px;
  flex-wrap: wrap;
}

.album-item {
  cursor: pointer;
}

.album-info {
  text-align: center;
  padding: 12px 0;
}

.album-title {
  font-size: 14px;
  font-weight: 500;
  margin-bottom: 4px;
  white-space: nowrap;
  overflow: hidden;
  text-overflow: ellipsis;
}

.album-year {
  font-size: 12px;
  color: var(--n-text-color-2);
}
</style>