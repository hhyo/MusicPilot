<template>
  <div class="chart-view">
    <n-page-header title="音乐榜单">
      <template #extra>
        <n-space>
          <n-button @click="refresh" :loading="loading">
            <template #icon>
              <n-icon><RefreshIcon /></n-icon>
            </template>
            刷新
          </n-button>
        </n-space>
      </template>
    </n-page-header>

    <!-- 榜单类型选择 -->
    <n-card class="chart-types-card">
      <n-space justify="space-around">
        <n-button
          v-for="chart in chartTypes"
          :key="chart.value"
          :type="selectedChartType === chart.value ? 'primary' : 'default'"
          @click="selectedChartType = chart.value"
        >
          {{ chart.label }}
        </n-button>
      </n-space>
    </n-card>

    <!-- 榜单数据展示 -->
    <ChartDisplay :chart-type="selectedChartType" />
  </div>
</template>

<script setup lang="ts">
import { ref } from 'vue'
import { NPageHeader, NCard, NSpace, NButton, NIcon } from 'naive-ui'
import { Refresh as RefreshIcon } from '@vicons/ionicons5'
import ChartDisplay from '@/components/chart/ChartDisplay.vue'

const loading = ref(false)

const chartTypes = [
  { label: '新歌榜', value: 'new_songs' },
  { label: '热歌榜', value: 'hot_songs' },
  { label: '飙升榜', value: 'soaring' },
]

const selectedChartType = ref('new_songs')

const refresh = () => {
  // 刷新逻辑 - 通过 key 强制重新渲染组件
  window.location.reload()
}
</script>

<style scoped>
.chart-view {
  padding: 20px;
}

.chart-types-card {
  margin-bottom: 20px;
}
</style>