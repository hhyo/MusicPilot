<template>
  <div class="chart-display">
    <!-- 榜单来源选择 -->
    <div class="flex items-center justify-between mb-4">
      <div class="flex items-center gap-2">
        <span class="text-white/60">数据来源:</span>
        <div class="flex gap-1">
          <button
            v-for="source in sources"
            :key="source.value"
            class="px-3 py-1.5 rounded-lg text-sm transition-all duration-200"
            :class="selectedSource === source.value 
              ? 'bg-accent text-white' 
              : 'glass text-white/60 hover:text-white'"
            @click="selectedSource = source.value"
          >
            {{ source.label }}
          </button>
        </div>
      </div>
      <span class="text-white/40 text-sm">更新时间: {{ updatedAt }}</span>
    </div>

    <!-- 加载状态 -->
    <div v-if="loading" class="flex items-center justify-center py-20">
      <div class="w-8 h-8 border-2 border-accent border-t-transparent rounded-full animate-spin"></div>
    </div>

    <!-- 歌曲列表 -->
    <GlassCard v-else padding>
      <div class="overflow-x-auto">
        <table class="w-full">
          <thead>
            <tr class="text-white/40 text-sm border-b border-white/10">
              <th class="text-left py-3 px-4 w-16">#</th>
              <th class="text-left py-3 px-4">歌曲</th>
              <th class="text-left py-3 px-4 hidden md:table-cell">艺术家</th>
              <th class="text-left py-3 px-4 hidden lg:table-cell">专辑</th>
              <th class="text-right py-3 px-4 w-32">操作</th>
            </tr>
          </thead>
          <tbody>
            <tr 
              v-for="entry in chartData.entries" 
              :key="entry.rank"
              class="border-b border-white/5 hover:bg-white/5 transition-all duration-200 group"
            >
              <td class="py-3 px-4">
                <span 
                  class="font-bold"
                  :class="{
                    'text-yellow-400': entry.rank === 1,
                    'text-gray-300': entry.rank === 2,
                    'text-amber-600': entry.rank === 3,
                    'text-white/40': entry.rank > 3
                  }"
                >
                  {{ entry.rank }}
                </span>
              </td>
              <td class="py-3 px-4">
                <div class="flex items-center gap-3">
                  <div class="w-10 h-10 rounded-lg bg-gradient-to-br from-accent/20 to-accent/10 flex items-center justify-center shrink-0">
                    🎵
                  </div>
                  <span class="font-medium truncate">{{ entry.title }}</span>
                </div>
              </td>
              <td class="py-3 px-4 hidden md:table-cell">
                <span class="text-white/60 truncate">{{ entry.artist }}</span>
              </td>
              <td class="py-3 px-4 hidden lg:table-cell">
                <span class="text-white/40 truncate">{{ entry.album }}</span>
              </td>
              <td class="py-3 px-4">
                <div class="flex items-center justify-end gap-2 opacity-0 group-hover:opacity-100 transition-opacity">
                  <button 
                    class="btn-ghost p-2 text-sm"
                    title="播放"
                    @click="playSong(entry)"
                  >
                    ▶️
                  </button>
                  <button 
                    class="btn-ghost p-2 text-sm"
                    title="订阅"
                    @click="subscribe(entry)"
                  >
                    ➕
                  </button>
                </div>
              </td>
            </tr>
          </tbody>
        </table>
      </div>

      <!-- 空状态 -->
      <div v-if="!chartData.entries.length" class="text-center py-12">
        <div class="text-4xl mb-2">📊</div>
        <p class="text-white/40">暂无数据</p>
      </div>
    </GlassCard>
  </div>
</template>

<script setup lang="ts">
import { ref, watch, onMounted } from 'vue'
import GlassCard from '@/components/ui/GlassCard.vue'

interface ChartEntry {
  rank: number
  title: string
  artist: string
  album: string
}

interface ChartData {
  source: string
  chart_type: string
  updated_at: string
  entries: ChartEntry[]
}

const props = defineProps<{
  chartType: string
}>()

const loading = ref(false)
const selectedSource = ref('netease')
const updatedAt = ref('')
const chartData = ref<ChartData>({
  source: '',
  chart_type: '',
  updated_at: '',
  entries: []
})

const sources = [
  { label: '网易云', value: 'netease' },
  { label: 'QQ音乐', value: 'qq_music' },
]

// 模拟数据
const mockChartData: ChartData = {
  source: 'netease',
  chart_type: 'hot_songs',
  updated_at: new Date().toLocaleString('zh-CN'),
  entries: [
    { rank: 1, title: '孤星如故', artist: '徐佳莹', album: '日久生情' },
    { rank: 2, title: '纯纯的回忆', artist: '告五人', album: '带你飞' },
    { rank: 3, title: '离别总是那么突然', artist: '林俊杰', album: '重拾_快乐' },
    { rank: 4, title: '达尔文', artist: '林俊杰', album: '她说' },
    { rank: 5, title: '那些你很冒险的梦', artist: '林俊杰', album: '那些你很冒险的梦' },
    { rank: 6, title: '不为谁而作的歌', artist: '林俊杰', album: '实验概念专辑' },
    { rank: 7, title: '起风了', artist: '周深', album: '深的深' },
    { rank: 8, title: '大鱼', artist: '周深', album: '大鱼' },
    { rank: 9, title: '光亮', artist: '周深', album: '深的深' },
    { rank: 10, title: '化身孤岛的鲸', artist: '周深', album: '深的深' },
  ]
}

const fetchChart = async () => {
  loading.value = true
  try {
    // TODO: 调用 API 获取榜单数据
    // const data = await chartApi.getChart(selectedSource.value, props.chartType, 50)
    // chartData.value = data
    
    // 模拟数据
    await new Promise(resolve => setTimeout(resolve, 500))
    chartData.value = { ...mockChartData, chart_type: props.chartType }
    updatedAt.value = new Date().toLocaleString('zh-CN')
  } catch (error) {
    console.error('获取榜单失败:', error)
  } finally {
    loading.value = false
  }
}

const playSong = (entry: ChartEntry) => {
  console.log('播放:', entry.title)
}

const subscribe = (entry: ChartEntry) => {
  console.log('订阅:', entry.title)
}

watch([selectedSource, () => props.chartType], fetchChart, { immediate: true })
</script>

<style scoped>
.chart-display {
  min-height: 100%;
}
</style>