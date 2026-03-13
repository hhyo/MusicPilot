<template>
  <div class="media-view">
    <n-page-header title="媒体服务器">
      <template #extra>
        <n-button type="primary">
          <template #icon>
            <n-icon><AddIcon /></n-icon>
          </template>
          添加服务器
        </n-button>
      </template>
    </n-page-header>

    <n-card>
      <n-empty description="暂无配置的媒体服务器" />
    </n-card>
  </div>
</template>

<script setup lang="ts">
import { NPageHeader, NCard, NButton, NEmpty, NIcon } from 'naive-ui'
import { AddOutline as AddIcon } from '@vicons/ionicons5'
// TODO: 实现媒体服务器页面
</script>

<style scoped>
.media-view {
  padding: 20px;
}
</style>