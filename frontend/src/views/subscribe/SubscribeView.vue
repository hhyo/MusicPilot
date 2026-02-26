<template>
  <div class="subscribe-view">
    <n-page-header title="订阅管理">
      <template #extra>
        <n-button type="primary">
          <template #icon>
            <n-icon><AddIcon /></n-icon>
          </template>
          添加订阅
        </n-button>
      </template>
    </n-page-header>

    <n-card>
      <n-tabs type="line">
        <n-tab-pane name="artist" tab="艺术家">
          <n-empty description="暂无艺术家订阅" />
        </n-tab-pane>
        <n-tab-pane name="album" tab="专辑">
          <n-empty description="暂无专辑订阅" />
        </n-tab-pane>
      </n-tabs>
    </n-card>
  </div>
</template>

<script setup lang="ts">
import { NPageHeader, NCard, NButton, NTabs, NTabPane, NEmpty, NIcon } from 'naive-ui'
import { AddOutline as AddIcon } from '@vicons/ionicons5'
// TODO: 实现订阅管理页面
</script>

<style scoped>
.subscribe-view {
  padding: 20px;
}
</style>