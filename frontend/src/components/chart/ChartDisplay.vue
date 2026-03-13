<template>
  <div class="chart-display">
    <n-card>
      <template #header>
        <div class="chart-header">
          <span>{{ chartTitle }}</span>
          <n-radio-group v-model:value="selectedSource" size="small">
            <n-radio-button value="netease">网易云</n-radio-button>
            <n-radio-button value="qq_music">QQ音乐</n-radio-button>
          </n-radio-group>
        </div>
      </template>

      <n-data-table
        :columns="columns"
        :data="chartData.entries"
        :loading="loading"
        :pagination="{ pageSize: 20 }"
        row-key="rank"
      />
    </n-card>
  </div>
</template>

<script setup lang="ts">
import { ref, computed, watch, h } from 'vue'
import { NCard, NRadioGroup, NRadioButton, NDataTable, NButton, NIcon, useMessage, type DataTableColumns } from 'naive-ui'
import { chartApi, type ChartData } from '@/api/modules/chartApi'
import { AddOutline } from '@vicons/ionicons5'

const props = defineProps<{
  chartType: string
}>()

const message = useMessage()
const loading = ref(false)
const selectedSource = ref('netease')
const chartData = ref<ChartData>({
  source: '',
  chart_type: '',
  updated_at: '',
  entries: []
})

const chartTitle = computed(() => {
  const titles: Record<string, string> = {
    new_songs: '新歌榜',
    hot_songs: '热歌榜',
    soaring: '飙升榜'
  }
  return titles[props.chartType] || props.chartType
})

const columns: DataTableColumns<any> = [
  {
    title: '#',
    key: 'rank',
    width: 60,
  },
  {
    title: '歌曲',
    key: 'title',
  },
  {
    title: '艺术家',
    key: 'artist',
  },
  {
    title: '专辑',
    key: 'album',
  },
  {
    title: '操作',
    key: 'actions',
    width: 100,
    render: (row) => {
      return h(NButton, { size: 'small', onClick: () => subscribe(row) }, () => '订阅')
    },
  },
]

const fetchChart = async () => {
  loading.value = true
  try {
    const data = await chartApi.getChart(
      selectedSource.value,
      props.chartType,
      50
    )
    chartData.value = data
  } catch (error) {
    message.error('获取榜单失败')
  } finally {
    loading.value = false
  }
}

const subscribe = (entry: any) => {
  // 实现订阅逻辑
  message.info(`订阅: ${entry.title} - ${entry.artist}`)
}

watch([selectedSource, () => props.chartType], fetchChart, { immediate: true })
</script>

<style scoped>
.chart-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
}
</style>