<template>
  <n-layout-sider
    bordered
    collapse-mode="width"
    :collapsed-width="64"
    :width="240"
    show-trigger="bar"
  >
    <n-menu :options="menuOptions" @update:value="handleMenuSelect" />
  </n-layout-sider>
</template>

<script setup lang="ts">
import { useRouter } from 'vue-router'
import { NLayoutSider, NMenu, type MenuOption } from 'naive-ui'
import {
  HomeOutline,
  LibraryOutline,
  PersonOutline,
  DiscOutline,
  ListOutline,
  DownloadOutline,
  HeartOutline,
  ServerOutline,
  SettingsOutline,
} from '@vicons/ionicons5'

const router = useRouter()

const menuOptions: MenuOption[] = [
  {
    label: '首页',
    key: 'home',
    icon: () => h(HomeOutline),
  },
  {
    label: '音乐库',
    key: 'library',
    icon: () => h(LibraryOutline),
  },
  {
    label: '艺术家',
    key: 'artists',
    icon: () => h(PersonOutline),
  },
  {
    label: '专辑',
    key: 'albums',
    icon: () => h(DiscOutline),
  },
  {
    label: '播放列表',
    key: 'playlists',
    icon: () => h(ListOutline),
  },
  {
    label: '下载',
    key: 'download',
    icon: () => h(DownloadOutline),
  },
  {
    label: '订阅',
    key: 'subscribe',
    icon: () => h(HeartOutline),
  },
  {
    label: '媒体服务器',
    key: 'media',
    icon: () => h(ServerOutline),
  },
  {
    label: '系统设置',
    key: 'system',
    icon: () => h(SettingsOutline),
  },
]

function handleMenuSelect(key: string) {
  router.push({ name: key.charAt(0).toUpperCase() + key.slice(1) })
}
</script>

<script lang="ts">
import { h } from 'vue'
export default {}
</script>