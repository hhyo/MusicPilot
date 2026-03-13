<template>
  <div class="playlist-detail-view">
    <n-page-header :title="playlist?.name || '播放列表详情'" @back="goBack">
      <template #extra>
        <n-space>
          <n-button v-if="playlist?.type === 'smart'" size="small" @click="refreshSmartPlaylist">
            <template #icon>
              <n-icon><RefreshIcon /></n-icon>
            </template>
            刷新
          </n-button>
          <n-button v-if="playlist?.type === 'normal'" size="small" @click="showAddTrackModal = true">
            <template #icon>
              <n-icon><AddIcon /></n-icon>
            </template>
            添加曲目
          </n-button>
          <n-button size="small" @click="playPlaylist">
            <template #icon>
              <n-icon><PlayIcon /></n-icon>
            </template>
            播放全部
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
              <n-space>
                <n-button v-if="playlist?.type === 'normal'" size="small" quaternary @click="toggleDragMode">
                  <template #icon>
                    <n-icon><MenuIcon /></n-icon>
                  </template>
                  {{ dragMode ? '完成排序' : '排序' }}
                </n-button>
                <n-button size="small" quaternary @click="shufflePlay">
                  <template #icon>
                    <n-icon><ShuffleIcon /></n-icon>
                  </template>
                  随机播放
                </n-button>
              </n-space>
            </div>
          </template>

          <Loading :loading="tracksLoading" description="加载曲目中...">
            <n-empty v-if="!tracksLoading && !tracks.length" description="暂无曲目" />
            <TrackList
              v-else
              :tracks="tracks"
              :draggable="dragMode"
              :selectable="true"
              :show-batch-actions="true"
              @play="handleTrackPlay"
              @reorder="handleReorder"
              @remove="handleRemoveTracks"
              @add-to-queue="handleAddToQueue"
            />
          </Loading>
        </n-card>

        <!-- 播放列表统计 -->
        <n-card style="margin-top: 16px">
          <n-descriptions :column="3" bordered>
            <n-descriptions-item label="曲目数量">
              {{ tracks.length }}
            </n-descriptions-item>
            <n-descriptions-item label="总时长">
              {{ totalDuration }}
            </n-descriptions-item>
            <n-descriptions-item label="类型">
              {{ playlist?.type === 'smart' ? '智能播放列表' : '普通播放列表' }}
            </n-descriptions-item>
          </n-descriptions>
        </n-card>
      </div>
    </Loading>

    <!-- 添加曲目对话框 -->
    <n-modal v-model:show="showAddTrackModal" preset="dialog" title="添加曲目">
      <n-form ref="addTrackFormRef" :model="addTrackForm" :rules="addTrackRules">
        <n-form-item label="选择方式" path="mode">
          <n-radio-group v-model:value="addTrackForm.mode">
            <n-radio value="artist">按艺术家</n-radio>
            <n-radio value="album">按专辑</n-radio>
            <n-radio value="track">单首曲目</n-radio>
          </n-radio-group>
        </n-form-item>
        <!-- TODO: 根据选择方式显示不同的选择界面 -->
      </n-form>
      <template #action>
        <n-button @click="showAddTrackModal = false">取消</n-button>
        <n-button type="primary" @click="handleAddTracks">确定</n-button>
      </template>
    </n-modal>
  </div>
</template>

<script setup lang="ts">
import { ref, onMounted, computed } from 'vue'
import { useRouter, useRoute } from 'vue-router'
import { NPageHeader, NEmpty, NCard, NSpace, NButton, NIcon, NDescriptions, NDescriptionsItem, NModal, NForm, NFormItem, NRadioGroup, NRadio } from 'naive-ui'
import {
  RefreshOutline as RefreshIcon,
  AddOutline as AddIcon,
  PlayOutline as PlayIcon,
  Menu as MenuIcon,
  ShuffleOutline as ShuffleIcon,
} from '@vicons/ionicons5'
import TrackList from '@/components/audio/TrackList.vue'
import Loading from '@/components/common/Loading.vue'
import { usePlayerStore } from '@/store/player'

const router = useRouter()
const route = useRoute()
const playerStore = usePlayerStore()

const loading = ref(false)
const tracksLoading = ref(false)
const playlist = ref<any>(null)
const tracks = ref<any[]>([])
const dragMode = ref(false)
const showAddTrackModal = ref(false)

const addTrackForm = ref({
  mode: 'track',
})
const addTrackRules = {}

const playlistId = computed(() => Number(route.params.id))

// 计算总时长
const totalDuration = computed(() => {
  const totalMs = tracks.value.reduce((sum, track) => sum + (track.duration || 0), 0)
  const totalSeconds = Math.floor(totalMs / 1000)
  const hours = Math.floor(totalSeconds / 3600)
  const mins = Math.floor((totalSeconds % 3600) / 60)
  if (hours > 0) {
    return `${hours}:${mins.toString().padStart(2, '0')}:00`
  }
  return `${mins}:00`
})

onMounted(async () => {
  await loadPlaylist()
  await loadTracks()
})

async function loadPlaylist() {
  loading.value = true
  try {
    // TODO: 调用 playlistApi.getById(playlistId.value)
    playlist.value = {
      id: playlistId.value,
      name: '示例播放列表',
      type: 'normal',
      description: '这是一个示例播放列表',
    }
  } finally {
    loading.value = false
  }
}

async function loadTracks() {
  tracksLoading.value = true
  try {
    // TODO: 调用 playlistApi.getTracks(playlistId.value)
    tracks.value = [
      // 示例数据
      { id: 1, title: '示例曲目 1', artist: '艺术家 A', album: '专辑 A', duration: 180000 },
      { id: 2, title: '示例曲目 2', artist: '艺术家 B', album: '专辑 B', duration: 210000 },
    ]
  } finally {
    tracksLoading.value = false
  }
}

function goBack() {
  router.back()
}

// 播放曲目
function handleTrackPlay(track: any) {
  // 设置播放队列并播放
  playerStore.setQueue(tracks.value, tracks.value.findIndex(t => t.id === track.id))
}

// 播放整个播放列表
function playPlaylist() {
  if (tracks.value.length === 0) return
  playerStore.setQueue(tracks.value, 0)
  playerStore.playTrack(tracks.value[0])
}

// 随机播放
function shufflePlay() {
  if (tracks.value.length === 0) return
  const shuffled = [...tracks.value].sort(() => Math.random() - 0.5)
  playerStore.setQueue(shuffled, 0)
  playerStore.setRepeatMode('all')
  playerStore.toggleShuffle()
  playerStore.playTrack(shuffled[0])
}

// 切换拖拽排序模式
function toggleDragMode() {
  dragMode.value = !dragMode.value
}

// 处理曲目重排序
function handleReorder(reorderedTracks: any[]) {
  tracks.value = reorderedTracks
  // TODO: 调用 API 保存新顺序
}

// 移除曲目
function handleRemoveTracks(trackIds: number[]) {
  tracks.value = tracks.value.filter(t => !trackIds.includes(t.id))
  // TODO: 调用 API 删除曲目
}

// 添加到队列
function handleAddToQueue(newTracks: any[]) {
  playerStore.addToQueue(newTracks)
}

// 刷新智能播放列表
function refreshSmartPlaylist() {
  // TODO: 调用 API 刷新智能播放列表
  loadTracks()
}

// 添加曲目
function handleAddTracks() {
  // TODO: 调用 API 添加曲目
  showAddTrackModal.value = false
}
</script>

<style scoped>
.playlist-detail-view {
  padding: 20px;
}
</style>