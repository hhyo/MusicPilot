<template>
  <div class="album-detail-view">
    <n-page-header :title="album?.title || '专辑详情'" @back="goBack" />
    <Loading :loading="loading" description="加载中...">
      <n-empty v-if="!loading && !album" description="专辑不存在" />
      <div v-else-if="album">
        <div class="album-header">
          <AlbumCover :cover-url="album.cover_url" :title="album.title" size="large" />
          <div class="album-info">
            <h1 class="album-title">{{ album.title }}</h1>
            <p class="album-artist">{{ album.artistName || '未知艺术家' }}</p>
            <p v-if="album.release_date" class="album-date">{{ album.release_date }}</p>
            <div class="album-tags">
              <n-tag v-for="genre in (album.genres || [])" :key="genre">{{ genre }}</n-tag>
            </div>
            <div v-if="album.rating" class="album-rating">
              <n-rate :value="album.rating" readonly size="small" />
            </div>
          </div>
        </div>

        <n-card title="曲目列表" style="margin-top: 24px">
          <Loading :loading="tracksLoading" description="加载曲目中...">
            <n-empty v-if="!tracksLoading && !tracks.length" description="暂无曲目" />
            <TrackList v-else :tracks="tracks" />
          </Loading>
        </n-card>
      </div>
    </Loading>
  </div>
</template>

<script setup lang="ts">
import { ref, onMounted, computed } from 'vue'
import { useRouter, useRoute } from 'vue-router'
import { NPageHeader, NEmpty, NCard, NTag, NRate } from 'naive-ui'
import AlbumCover from '@/components/audio/AlbumCover.vue'
import TrackList from '@/components/audio/TrackList.vue'
import Loading from '@/components/common/Loading.vue'

const router = useRouter()
const route = useRoute()

const loading = ref(false)
const tracksLoading = ref(false)
const album = ref<any>(null)
const tracks = ref<any[]>([])

const albumId = computed(() => Number(route.params.id))

onMounted(async () => {
  await loadAlbum()
  await loadTracks()
})

async function loadAlbum() {
  loading.value = true
  try {
    // TODO: 调用 albumApi.getById(albumId.value)
  } finally {
    loading.value = false
  }
}

async function loadTracks() {
  tracksLoading.value = true
  try {
    // TODO: 调用 albumApi.getTracks(albumId.value)
  } finally {
    tracksLoading.value = false
  }
}

function goBack() {
  router.back()
}
</script>

<style scoped>
.album-detail-view {
  padding: 20px;
}

.album-header {
  display: flex;
  gap: 24px;
  margin-bottom: 24px;
}

.album-info {
  flex: 1;
}

.album-title {
  font-size: 32px;
  font-weight: 600;
  margin: 0 0 8px 0;
}

.album-artist {
  font-size: 16px;
  color: var(--n-text-color-2);
  margin: 0 0 4px 0;
}

.album-date {
  font-size: 14px;
  color: var(--n-text-color-2);
  margin: 0 0 16px 0;
}

.album-tags {
  display: flex;
  gap: 8px;
  flex-wrap: wrap;
  margin-bottom: 16px;
}

.album-rating {
  margin-top: 16px;
}
</style>