<template>
  <div class="system-view">
    <n-page-header title="系统设置" />
    <n-tabs type="line">
      <n-tab-pane name="general" tab="常规">
        <n-card title="基本信息">
          <n-form :label-width="120">
            <n-form-item label="应用名称">
              <n-input v-model:value="settings.appName" />
            </n-form-item>
            <n-form-item label="API 地址">
              <n-input v-model:value="settings.apiUrl" />
            </n-form-item>
          </n-form>
          <template #footer>
            <n-button type="primary" @click="saveSettings">保存</n-button>
          </template>
        </n-card>
      </n-tab-pane>
      <n-tab-pane name="stats" tab="统计信息">
        <n-card title="系统统计">
          <n-statistic label="艺术家" :value="stats.artistCount" />
          <n-statistic label="专辑" :value="stats.albumCount" />
          <n-statistic label="曲目" :value="stats.trackCount" />
          <n-statistic label="播放列表" :value="stats.playlistCount" />
        </n-card>
      </n-tab-pane>
      <n-tab-pane name="logs" tab="日志">
        <n-card title="系统日志">
          <n-log :log="logs" :rows="20" />
        </n-card>
      </n-tab-pane>
    </n-tabs>
  </div>
</template>

<script setup lang="ts">
import { ref } from 'vue'
import { NPageHeader, NTabs, NTabPane, NCard, NForm, NFormItem, NInput, NButton, NStatistic, NLog } from 'naive-ui'

const settings = ref({
  appName: 'MusicPilot',
  apiUrl: 'http://localhost:8000',
})

const stats = ref({
  artistCount: 0,
  albumCount: 0,
  trackCount: 0,
  playlistCount: 0,
})

const logs = ref([
  '[2026-02-26 12:00:00] 系统启动',
  '[2026-02-26 12:00:01] 数据库连接成功',
])

// TODO: 实现设置保存、统计加载、日志获取
function saveSettings() {
  console.log('保存设置:', settings.value)
}
</script>

<style scoped>
.system-view {
  padding: 20px;
}

.n-statistic {
  margin-bottom: 16px;
}
</style>