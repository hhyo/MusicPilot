<template>
  <div class="playlist-detail-view">
    <n-page-header :title="playlist?.name || '播放列表详情'" @back="goBack">
      <template #extra>
        <n-space>
          <n-button v-if="playlist?.type === 'smart'" size="small">
            <template #icon>
              <n-icon><RefreshIcon /></n-icon>
            </template>
            刷新
          </n-button>
          <n-button v-if="playlist?.type === 'normal'" size="small">
            <template #icon>
              <n-icon><AddIcon /></n-icon>
            </template>
            添加曲目
          </n-button>
        </n-space>
      </template>
    </n-page-header>

    <Loading :loading="loading" description="加载中...">
      <n-empty v-if="!loading && !playlist" description="播放列表不存在" />
      <div v-else-if="playlist">
        <n-card v-if="playlist.description" style="margin-bottom: 16px">
          <p>{{ playlist.description }}</p>
        </n-card>

        <n-card>
          <template #header>
            <div style="display: flex; justify-content: space-between; align-items: center;">
              <span>曲目列表 ({{ tracks.length }})</span>
              <n-button v-if="playlist?.type === 'normal' && tracks.length" size="small" quaternary>
                <template #icon>
                  <n-icon><ShuffleIcon /></n-icon>
                </template>
                随机播放
              </n-button>
            </div>
          </template>

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
import { NPageHeader, NEmpty, NCard, NSpace, NButton, NIcon } from 'naive-ui'
import {
  RefreshOutline as RefreshIcon,
  AddOutline as AddIcon,
  ShuffleOutline as ShuffleIcon,
} from '@vicons/ionicons5'
import TrackList from '@/components/audio/TrackList.vue'
import Loading from '@/components/common/Loading.vue'

const router = useRouter()
const route = useRoute()

const loading = ref(false)
const tracksLoading = ref(false)
const playlist = ref<any>(null)
const tracks = ref<any[]>([])

const playlistId = computed(() => Number(route.params.id))

onMounted(async () => {
  await loadPlaylist()
  await loadTracks()
})

async function loadPlaylist() {
  loading.value = true
  try {
    // TODO: 调用 playlistApi.getById(playlistId.value)
  } finally {
    loading.value = false
  }
}

async function loadTracks() {
  tracksLoading.value = true
  try {
    // TODO: 调用 playlistApi.getTracks(playlistId.value)
  } finally {
    tracksLoading.value = false
  }
}

function goBack() {
  router.back()
}
</script>

<style scoped>
.playlist-detail-view {
  padding: 20px;
}
</style>