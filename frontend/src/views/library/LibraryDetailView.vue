<template>
  <div class="library-detail-view">
    <n-page-header :title="library?.name || '音乐库详情'" @back="goBack" />
    <n-spin :show="loading">
      <n-empty v-if="!loading && !library" description="音乐库不存在" />
      <div v-else-if="library" class="library-detail">
        <n-card :title="library.name">
          <n-descriptions :column="1">
            <n-descriptions-item label="路径">{{ library.path }}</n-descriptions-item>
            <n-descriptions-item label="曲目">{{ library.trackCount || 0 }} 首</n-descriptions-item>
            <n-descriptions-item label="专辑">{{ library.albumCount || 0 }} 张</n-descriptions-item>
            <n-descriptions-item label="艺术家">{{ library.artistCount || 0 }} 位</n-descriptions-item>
            <n-descriptions-item label="最后扫描">{{ library.lastScanTime || '未扫描' }}</n-descriptions-item>
            <n-descriptions-item label="自动扫描">{{ library.autoScan ? '开启' : '关闭' }}</n-descriptions-item>
          </n-descriptions>
          <template #footer>
            <n-space>
              <n-button type="primary" @click="handleScan" :loading="scanning">
                <template #icon>
                  <n-icon><RefreshIcon /></n-icon>
                </template>
                扫描音乐库
              </n-button>
            </n-space>
          </template>
        </n-card>

        <n-card title="曲目列表" style="margin-top: 16px">
          <Loading :loading="tracksLoading" description="加载曲目中...">
            <n-empty v-if="!tracksLoading && !tracks.length" description="暂无曲目" />
            <TrackList v-else :tracks="tracks" />
            <Pagination
              v-if="tracks.length"
              v-model:page="currentPage"
              v-model:page-size="pageSize"
              :total-items="totalTracks"
            />
          </Loading>
        </n-card>
      </div>
    </n-spin>
  </div>
</template>

<script setup lang="ts">
import { ref, onMounted, computed } from 'vue'
import { useRouter, useRoute } from 'vue-router'
import {
  NPageHeader,
  NSpin,
  NEmpty,
  NCard,
  NDescriptions,
  NDescriptionsItem,
  NButton,
  NSpace,
  NIcon,
} from 'naive-ui'
import { RefreshOutline as RefreshIcon } from '@vicons/ionicons5'
import TrackList from '@/components/audio/TrackList.vue'
import Pagination from '@/components/common/Pagination.vue'
import Loading from '@/components/common/Loading.vue'

const router = useRouter()
const route = useRoute()

const loading = ref(false)
const scanning = ref(false)
const library = ref<any>(null)
const tracksLoading = ref(false)
const tracks = ref<any[]>([])
const currentPage = ref(1)
const pageSize = ref(20)
const totalTracks = ref(0)

const libraryId = computed(() => Number(route.params.id))

onMounted(async () => {
  await loadLibrary()
  await loadTracks()
})

async function loadLibrary() {
  loading.value = true
  try {
    // TODO: 调用 libraryApi.getById(libraryId.value)
  } finally {
    loading.value = false
  }
}

async function loadTracks() {
  tracksLoading.value = true
  try {
    // TODO: 调用 trackApi.getByLibrary()
  } finally {
    tracksLoading.value = false
  }
}

async function handleScan() {
  scanning.value = true
  try {
    // TODO: 调用 libraryApi.scan(libraryId.value)
  } finally {
    scanning.value = false
    await loadLibrary()
    await loadTracks()
  }
}

function goBack() {
  router.back()
}
</script>

<style scoped>
.library-detail-view {
  padding: 20px;
}
</style>