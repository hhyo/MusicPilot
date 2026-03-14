<template>
  <div class="track-list">
    <!-- 批量操作栏 -->
    <div v-if="showBatchActions && selectedTracks.size > 0" class="batch-actions">
      <span class="selected-count">已选择 {{ selectedTracks.size }} 首</span>
      <n-space>
        <n-button size="small" @click="clearSelection">
          取消选择
        </n-button>
      </n-space>
    </div>

    <n-list bordered>
      <draggable
        v-model="trackList"
        item-key="id"
        :disabled="!draggable"
        handle=".drag-handle"
        @end="onDragEnd"
      >
        <template #item="{ element: track, index }">
          <n-list-item>
            <div
              class="track-item"
              :class="{
                'selected': selectedTracks.has(track.id),
              }"
            >
              <!-- 拖拽手柄 -->
              <div v-if="draggable" class="drag-handle">
                <n-icon><MenuIcon /></n-icon>
              </div>

              <!-- 选择框 -->
              <n-checkbox
                v-if="selectable"
                :checked="selectedTracks.has(track.id)"
                @update:checked="toggleSelection(track)"
              />

              <!-- 序号 -->
              <div class="track-index">{{ index + 1 }}</div>

              <!-- 曲目信息 -->
              <div class="track-info">
                <div class="track-title">{{ track.title }}</div>
                <div class="track-meta">
                  <span>{{ track.artist }}</span>
                  <span v-if="track.album"> · {{ track.album }}</span>
                </div>
              </div>

              <!-- 时长 -->
              <div v-if="track.duration" class="track-duration">
                {{ formatDuration(track.duration) }}
              </div>

              <!-- 操作 -->
              <div class="track-actions">
                <n-button size="small" quaternary @click="handleAction('detail', track)">
                  <template #icon>
                    <n-icon><InformationIcon /></n-icon>
                  </template>
                </n-button>
              </div>
            </div>
          </n-list-item>
        </template>
      </draggable>
    </n-list>
  </div>
</template>

<script setup lang="ts">
import { ref, computed } from 'vue'
import { NList, NListItem, NSpace, NButton, NIcon, NCheckbox } from 'naive-ui'
import { Menu as MenuIcon, InformationCircleOutline as InformationIcon } from '@vicons/ionicons5'
import draggable from 'vuedraggable'

interface Track {
  id: number
  title: string
  artist: string
  album?: string
  duration?: number
}

const props = withDefaults(defineProps<{
  tracks: Track[]
  draggable?: boolean
  selectable?: boolean
  showBatchActions?: boolean
}>(), {
  draggable: false,
  selectable: false,
  showBatchActions: false,
})

const emit = defineEmits<{
  reorder: [tracks: Track[]]
  action: [type: string, track: Track]
}>()

const trackList = computed({
  get: () => props.tracks,
  set: (val) => emit('reorder', val)
})

const selectedTracks = ref<Set<number>>(new Set())

// 切换选择
function toggleSelection(track: Track) {
  if (selectedTracks.value.has(track.id)) {
    selectedTracks.value.delete(track.id)
  } else {
    selectedTracks.value.add(track.id)
  }
}

// 清除选择
function clearSelection() {
  selectedTracks.value.clear()
}

// 拖拽结束
function onDragEnd() {
  emit('reorder', trackList.value)
}

// 处理操作
function handleAction(type: string, track: Track) {
  emit('action', type, track)
}

// 格式化时长
function formatDuration(ms: number): string {
  const seconds = Math.floor(ms / 1000)
  const mins = Math.floor(seconds / 60)
  const secs = seconds % 60
  return `${mins}:${secs.toString().padStart(2, '0')}`
}
</script>

<style scoped>
.track-list {
  width: 100%;
}

.batch-actions {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 12px 16px;
  background: var(--n-color-embedded);
  border-radius: 4px;
  margin-bottom: 12px;
}

.selected-count {
  font-weight: 500;
}

.track-item {
  display: flex;
  align-items: center;
  gap: 12px;
  padding: 8px 0;
  cursor: pointer;
  transition: background-color 0.2s;
}

.track-item:hover {
  background-color: var(--n-color-hover);
}

.track-item.selected {
  background-color: var(--n-color-pressed);
}

.drag-handle {
  cursor: grab;
  color: var(--n-text-color-3);
}

.drag-handle:active {
  cursor: grabbing;
}

.track-index {
  width: 32px;
  text-align: center;
  color: var(--n-text-color-3);
  font-size: 14px;
}

.track-info {
  flex: 1;
  min-width: 0;
}

.track-title {
  font-weight: 500;
  margin-bottom: 4px;
}

.track-meta {
  font-size: 12px;
  color: var(--n-text-color-3);
}

.track-duration {
  color: var(--n-text-color-3);
  font-size: 14px;
  min-width: 50px;
  text-align: right;
}

.track-actions {
  display: flex;
  gap: 4px;
}
</style>
