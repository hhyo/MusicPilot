<template>
  <div class="chart-view p-4 md:p-6 lg:p-8">
    <!-- 页面标题 -->
    <div class="flex items-center justify-between mb-6">
      <div>
        <h1 class="text-3xl font-bold mb-1">音乐榜单</h1>
        <p class="text-white/50">实时更新的热门音乐排行</p>
      </div>
      <button class="btn-secondary flex items-center gap-2" @click="refresh" :disabled="loading">
        <span :class="{ 'animate-spin': loading }">🔄</span>
        <span>刷新</span>
      </button>
    </div>

    <!-- 榜单类型选择 -->
    <div class="flex flex-wrap gap-2 mb-6 p-2 glass rounded-2xl">
      <button
        v-for="chart in chartTypes"
        :key="chart.value"
        class="flex-1 min-w-[120px] py-3 px-4 rounded-xl transition-all duration-300 font-medium"
        :class="selectedChartType === chart.value 
          ? 'bg-accent text-white shadow-lg shadow-accent/25' 
          : 'text-white/60 hover:text-white hover:bg-white/10'"
        @click="selectedChartType = chart.value"
      >
        {{ chart.label }}
      </button>
    </div>

    <!-- 榜单数据展示 -->
    <ChartDisplay :chart-type="selectedChartType" :key="refreshKey" />
  </div>
</template>

<script setup lang="ts">
import { ref } from 'vue'
import ChartDisplay from '@/components/chart/ChartDisplay.vue'

const loading = ref(false)
const refreshKey = ref(0)

const chartTypes = [
  { label: '新歌榜', value: 'new_songs' },
  { label: '热歌榜', value: 'hot_songs' },
  { label: '飙升榜', value: 'soaring' },
  { label: '网易云音乐', value: 'netEase' },
  { label: 'QQ音乐', value: 'qq' },
]

const selectedChartType = ref('new_songs')

const refresh = () => {
  loading.value = true
  refreshKey.value++
  setTimeout(() => {
    loading.value = false
  }, 1000)
}
</script>

<style scoped>
.chart-view {
  min-height: 100%;
}
</style>