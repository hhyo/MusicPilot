<template>
  <div class="track-list">
    <!-- 批量操作栏 -->
    <div v-if="showBatchActions && selectedTracks.size > 0" class="batch-actions">
      <span class="selected-count">已选择 {{ selectedTracks.size }} 首</span>
      <n-space>
        <n-button size="small" type="primary" @click="addToQueue">
          加入播放队列
        </n-button>
        <n-button size="small" @click="removeSelected">
          移除
        </n-button>
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
                'playing': isCurrentTrack(track),
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
              <div class="track-index">
                <n-icon v-if="isCurrentTrack(track) && playerStore.isPlaying">
                  <VolumeHighIcon />
                </n-icon>
                <span v-else>{{ index + 1 }}</span>
              </div>

              <!-- 封面 -->
              <div class="track-cover">
                <img v-if="track.cover" :src="track.cover" alt="封面" />
                <div v-else class="cover-placeholder">
                  <n-icon><MusicalNoteIcon /></n-icon>
                </div>
              </div>

              <!-- 信息 -->
              <div class="track-info">
                <div class="track-title">{{ track.title }}</div>
                <div class="track-meta">
                  <span class="artist">{{ track.artist }}</span>
                  <span v-if="track.album" class="separator">·</span>
                  <span v-if="track.album" class="album">{{ track.album }}</span>
                </div>
              </div>

              <!-- 时长 -->
              <div v-if="track.duration" class="track-duration">
                {{ formatDuration(track.duration) }}
              </div>

              <!-- 操作按钮 -->
              <div class="track-actions">
                <n-button quaternary circle size="small" @click.stop="playTrack(track)">
                  <template #icon>
                    <n-icon><PlayIcon /></n-icon>
                  </template>
                </n-button>
                <n-button quaternary circle size="small" @click.stop="toggleFavorite(track)">
                  <template #icon>
                    <n-icon :color="isFavorite(track) ? '#ff6b6b' : undefined">
                      {{ isFavorite(track) ? HeartIcon : HeartOutlineIcon }}
                    </n-icon>
                  </template>
                </n-button>
                <n-dropdown :options="getMenuOptions(track)" placement="bottom-end" @select="(key) => handleMenuAction(key, track)">
                  <n-button quaternary circle size="small">
                    <template #icon>
                      <n-icon><EllipsisVerticalIcon /></n-icon>
                    </template>
                  </n-button>
                </n-dropdown>
              </div>
            </div>
          </n-list-item>
        </template>
      </draggable>
    </n-list>
  </div>
</template>

<script setup lang="ts">
import { ref, computed, watch } from 'vue'
import { NList, NListItem, NButton, NIcon, NCheckbox, NSpace, NDropdown, DropdownOption } from 'naive-ui'
import { MusicalNotesOutline as MusicalNoteIcon, PlayOutline as PlayIcon, HeartOutline as HeartOutlineIcon, Heart as HeartIcon, Menu as MenuIcon, VolumeHighOutline as VolumeHighIcon, EllipsisVerticalOutline as EllipsisVerticalIcon } from '@vicons/ionicons5'
import draggable from 'vuedraggable'
import { usePlayerStore } from '@/store/player'

interface Track {
  id: number
  title: string
  artist?: string
  album?: string
  cover?: string
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
  showBatchActions: true,
})

const emit = defineEmits<{
  play: [track: Track]
  reorder: [tracks: Track[]]
  remove: [trackIds: number[]]
  addToQueue: [tracks: Track[]]
}>()

const playerStore = usePlayerStore()
const trackList = ref<Track[]>([...props.tracks])
const selectedTracks = ref<Set<number>>(new Set())
const favorites = ref<Set<number>>(new Set())

// 监听 tracks 变化
watch(() => props.tracks, (newTracks) => {
  trackList.value = [...newTracks]
}, { deep: true })

// 是否是当前播放曲目
function isCurrentTrack(track: Track): boolean {
  return playerStore.currentTrack?.id === track.id
}

// 播放曲目
function playTrack(track: Track) {
  emit('play', track)
  playerStore.playTrack(track)
}

// 切换选择
function toggleSelection(track: Track) {
  if (selectedTracks.value.has(track.id)) {
    selectedTracks.value.delete(track.id)
  } else {
    selectedTracks.value.add(track.id)
  }
}

// 清空选择
function clearSelection() {
  selectedTracks.value.clear()
}

// 拖拽结束
function onDragEnd() {
  emit('reorder', trackList.value)
}

// 添加到播放队列
function addToQueue() {
  const tracks = trackList.value.filter(t => selectedTracks.value.has(t.id))
  emit('addToQueue', tracks)
  playerStore.addToQueue(tracks)
  clearSelection()
}

// 移除选中的曲目
function removeSelected() {
  const trackIds = Array.from(selectedTracks.value)
  emit('remove', trackIds)
  clearSelection()
}

// 切换收藏
function toggleFavorite(track: Track) {
  if (favorites.value.has(track.id)) {
    favorites.value.delete(track.id)
  } else {
    favorites.value.add(track.id)
  }
}

// 是否收藏
function isFavorite(track: Track): boolean {
  return favorites.value.has(track.id)
}

// 格式化时长
function formatDuration(ms: number): string {
  const seconds = Math.floor(ms / 1000)
  const mins = Math.floor(seconds / 60)
  const secs = seconds % 60
  return `${mins}:${secs.toString().padStart(2, '0')}`
}

// 获取菜单选项
function getMenuOptions(track: Track): DropdownOption[] {
  return [
    {
      label: '下一首播放',
      key: 'playNext',
      icon: () => h(NIcon, null, { default: () => h(PlayIcon) }),
    },
    {
      label: '添加到队列',
      key: 'addToQueue',
      icon: () => h(NIcon, null, { default: () => h(PlayIcon) }),
    },
    { type: 'divider' },
    {
      label: '添加到播放列表',
      key: 'addToPlaylist',
    },
    {
      label: '从列表移除',
      key: 'remove',
      icon: () => h(NIcon, null, { default: () => h(HeartOutlineIcon) }),
    },
  ]
}

// 处理菜单操作
function handleMenuAction(key: string, track: Track) {
  switch (key) {
    case 'playNext':
      // TODO: 实现下一首播放
      break
    case 'addToQueue':
      playerStore.addToQueue([track])
      break
    case 'addToPlaylist':
      // TODO: 打开选择播放列表对话框
      break
    case 'remove':
      emit('remove', [track.id])
      break
  }
}

import { h } from 'vue'
</script>

<style scoped>
.batch-actions {
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: 12px 16px;
  background: var(--n-color);
  border-bottom: 1px solid var(--n-border-color);
}

.selected-count {
  font-size: 14px;
  color: var(--n-text-color-2);
}

.track-item {
  display: flex;
  align-items: center;
  gap: 12px;
  padding: 8px 0;
  border-radius: 4px;
}

.track-item:hover {
  background: var(--n-color);
}

.track-item.selected {
  background: var(--n-color-hover);
}

.track-item.playing {
  color: var(--n-primary-color);
}

.drag-handle {
  cursor: move;
  color: var(--n-text-color-3);
  opacity: 0;
}

.track-item:hover .drag-handle {
  opacity: 1;
}

.track-index {
  width: 32px;
  text-align: center;
  color: var(--n-text-color-2);
  font-size: 14px;
}

.track-item.playing .track-index {
  color: var(--n-primary-color);
}

.track-cover {
  width: 48px;
  height: 48px;
  border-radius: 4px;
  overflow: hidden;
  flex-shrink: 0;
}

.track-cover img {
  width: 100%;
  height: 100%;
  object-fit: cover;
}

.cover-placeholder {
  width: 100%;
  height: 100%;
  display: flex;
  align-items: center;
  justify-content: center;
  background: var(--n-color);
  color: var(--n-text-color-3);
}

.track-info {
  flex: 1;
  min-width: 0;
}

.track-title {
  font-size: 14px;
  font-weight: 500;
  margin-bottom: 4px;
  white-space: nowrap;
  overflow: hidden;
  text-overflow: ellipsis;
}

.track-item.playing .track-title {
  color: var(--n-primary-color);
}

.track-meta {
  font-size: 12px;
  color: var(--n-text-color-2);
}

.separator {
  margin: 0 4px;
}

.track-duration {
  width: 50px;
  text-align: right;
  font-size: 12px;
  color: var(--n-text-color-2);
}

.track-actions {
  display: flex;
  gap: 4px;
  opacity: 0;
}

.track-item:hover .track-actions {
  opacity: 1;
}
</style>