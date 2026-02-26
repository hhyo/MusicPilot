<template>
  <div class="download-view">
    <n-page-header title="下载管理" />
    <n-card>
      <n-tabs type="line">
        <n-tab-pane name="downloading" tab="下载中">
          <n-empty description="没有正在下载的任务" />
        </n-tab-pane>
        <n-tab-pane name="completed" tab="已完成">
          <n-empty description="没有已完成的下载" />
        </n-tab-pane>
        <n-tab-pane name="failed" tab="下载失败">
          <n-empty description="没有失败的下载" />
        </n-tab-pane>
      </n-tabs>
    </n-card>
  </div>
</template>

<script setup lang="ts">
import { NPageHeader, NCard, NTabs, NTabPane, NEmpty } from 'naive-ui'
// TODO: 实现下载管理页面
</script>

<style scoped>
.download-view {
  padding: 20px;
}
</style>