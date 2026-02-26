<template>
  <div class="subscribe-list">
    <n-space vertical>
      <n-space justify="space-between">
        <n-space>
          <n-button quaternary @click="$emit('refresh')">
            <template #icon>
              <n-icon><RefreshIcon /></n-icon>
            </template>
            刷新
          </n-button>
        </n-space>
        <n-space v-if="subscribes.length > 0">
          <n-text depth="3">共 {{ subscribes.length }} 个订阅</n-text>
        </n-space>
      </n-space>

      <n-spin :show="loading">
        <n-empty v-if="!loading && subscribes.length === 0" :description="emptyDescription" />

        <n-list v-else>
          <n-list-item v-for="subscribe in subscribes" :key="subscribe.id">
            <template #prefix>
              <n-icon size="24" :color="getIconColor()">
                <component :is="getIcon()" />
              </n-icon>
            </template>

            <n-list-item-header>
              <n-space align="center">
                <n-text strong>{{ subscribe.name }}</n-text>
                <n-tag v-if="!subscribe.state || subscribe.state === 'active'" type="success" size="small">启用</n-tag>
                <n-tag v-else type="default" size="small">暂停</n-tag>
                <n-tag v-if="subscribe.auto_download" type="info" size="small">自动下载</n-tag>
              </n-space>
            </n-list-item-header>

            <n-list-item-meta v-if="subscribe.description">
              {{ subscribe.description }}
            </n-list-item-meta>

            <template #suffix>
              <n-space>
                <n-button
                  text
                  size="small"
                  :type="subscribe.state === 'paused' ? 'success' : 'default'"
                  @click="toggleState(subscribe)"
                >
                  {{ subscribe.state === 'paused' ? '启用' : '暂停' }}
                </n-button>
                <n-button text size="small" @click="$emit('edit', subscribe)">编辑</n-button>
                <n-button text size="small" type="error" @click="$emit('delete', subscribe)">删除</n-button>
              </n-space>
            </template>
          </n-list-item>
        </n-list>
      </n-spin>
    </n-space>
  </div>
</template>

<script setup lang="ts">
import { ref, computed } from 'vue'
import { NList, NListItem, NListItemHeader, NListItemMeta, NSpace, NButton, NTag, NIcon, NText, NSpin, NEmpty, useMessage } from 'naive-ui'
import { RefreshOutline as RefreshIcon, PersonOutline as ArtistIcon, AlbumOutline as AlbumIcon, MusicalNotesOutline as PlaylistIcon, RibbonOutline as ChartIcon } from '@vicons/ionicons5'
import * as subscribeApi from '@/api/subscribe'

interface Props {
  type: string
  subscribes: any[]
}

const props = defineProps<Props>()

defineEmits<{
  refresh: []
  edit: [subscribe: any]
  delete: [subscribe: any]
}>()

const message = useMessage()
const loading = ref(false)

const emptyDescription = computed(() => {
  switch (props.type) {
    case 'artist':
      return '暂无艺术家订阅'
    case 'album':
      return '暂无专辑订阅'
    case 'playlist':
      return '暂无歌单订阅'
    case 'chart':
      return '暂无榜单订阅'
    default:
      return '暂无订阅'
  }
})

const getIcon = () => {
  switch (props.type) {
    case 'artist':
      return ArtistIcon
    case 'album':
      return AlbumIcon
    case 'playlist':
      return PlaylistIcon
    case 'chart':
      return ChartIcon
    default:
      return PlaylistIcon
  }
}

const getIconColor = () => {
  switch (props.type) {
    case 'artist':
      return '#18a058'
    case 'album':
      return '#2080f0'
    case 'playlist':
      return '#f0a020'
    case 'chart':
      return '#d03050'
    default:
      return '#909399'
  }
}

const toggleState = async (subscribe: any) => {
  const newState = subscribe.state === 'paused' ? 'active' : 'paused'
  const action = newState === 'active' ? '启用' : '暂停'

  try {
    await subscribeApi.updateSubscribe(subscribe.id, { state: newState })
    message.success(`${action}成功`)
    emit('refresh')
  } catch (error) {
    message.error(`${action}失败`)
  }
}
</script>

<style scoped>
.subscribe-list {
  padding: 10px 0;
}
</style>