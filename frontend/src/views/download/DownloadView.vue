<template>
  <div class="download-view">
    <n-page-header title="下载管理">
      <template #extra>
        <n-space>
          <n-button @click="refresh" :loading="loading">
            <template #icon>
              <n-icon><RefreshIcon /></n-icon>
            </template>
            刷新
          </n-button>
          <n-button type="primary" @click="showSearchModal = true">
            <template #icon>
              <n-icon><DownloadIcon /></n-icon>
            </template>
            添加下载
          </n-button>
        </n-space>
      </template>
    </n-page-header>

    <!-- 下载统计 -->
    <n-card class="stats-card" title="下载统计">
      <n-space justify="space-around">
        <n-statistic label="总下载量" :value="stats.total" />
        <n-statistic label="成功" :value="stats.completed" />
        <n-statistic label="失败" :value="stats.failed" />
        <n-statistic label="成功率" :value="successRate + '%'" />
      </n-space>
    </n-card>

    <!-- 下载任务列表 -->
    <n-card>
      <template #header-extra>
        <n-radio-group v-model:value="activeTab" size="small">
          <n-radio-button value="downloading">下载中</n-radio-button>
          <n-radio-button value="completed">已完成</n-radio-button>
          <n-radio-button value="failed">下载失败</n-radio-button>
          <n-radio-button value="history">历史记录</n-radio-button>
        </n-radio-group>
      </template>

      <!-- 下载中 -->
      <template v-if="activeTab === 'downloading'">
        <n-data-table
          :columns="downloadingColumns"
          :data="activeDownloads"
          :loading="loading"
          :pagination="{ pageSize: 10 }"
          row-key="task_id"
        />
        <n-empty v-if="!loading && activeDownloads.length === 0" description="没有正在下载的任务" />
      </template>

      <!-- 已完成 -->
      <template v-else-if="activeTab === 'completed'">
        <n-data-table
          :columns="completedColumns"
          :data="completedDownloads"
          :loading="loading"
          :pagination="{ pageSize: 10 }"
          row-key="task_id"
        />
        <n-empty v-if="!loading && completedDownloads.length === 0" description="没有已完成的下载" />
      </template>

      <!-- 下载失败 -->
      <template v-else-if="activeTab === 'failed'">
        <n-data-table
          :columns="failedColumns"
          :data="failedDownloads"
          :loading="loading"
          :pagination="{ pageSize: 10 }"
          row-key="task_id"
        />
        <n-empty v-if="!loading && failedDownloads.length === 0" description="没有失败的下载" />
      </template>

      <!-- 历史记录 -->
      <template v-else>
        <n-data-table
          :columns="historyColumns"
          :data="downloadHistory"
          :loading="loading"
          :pagination="{ pageSize: 20 }"
          row-key="source_id"
        />
        <n-empty v-if="!loading && downloadHistory.length === 0" description="没有下载历史" />
      </template>
    </n-card>

    <!-- 搜索下载弹窗 -->
    <n-modal v-model:show="showSearchModal" preset="card" title="搜索并下载" style="width: 600px">
      <n-form ref="searchFormRef" :model="searchForm" label-placement="left" label-width="80">
        <n-form-item label="关键词" path="keyword" :rule="{ required: true, message: '请输入关键词' }">
          <n-input v-model:value="searchForm.keyword" placeholder="歌曲名、艺术家或专辑" />
        </n-form-item>

        <n-form-item label="来源" path="source">
          <n-select
            v-model:value="searchForm.source"
            :options="sourceOptions"
            placeholder="选择下载来源"
          />
        </n-form-item>

        <n-form-item label="音质" path="quality">
          <n-select
            v-model:value="searchForm.quality"
            :options="qualityOptions"
            placeholder="选择音质"
          />
        </n-form-item>

        <n-form-item label="数量" path="limit">
          <n-input-number
            v-model:value="searchForm.limit"
            :min="1"
            :max="20"
            placeholder="下载数量"
          />
        </n-form-item>
      </n-form>

      <template #footer>
        <n-space justify="end">
          <n-button @click="showSearchModal = false">取消</n-button>
          <n-button type="primary" @click="handleSearchAndDownload" :loading="searching">
            搜索并下载
          </n-button>
        </n-space>
      </template>
    </n-modal>

    <!-- URL 下载弹窗 -->
    <n-modal v-model:show="showUrlModal" preset="card" title="通过 URL 下载" style="width: 600px">
      <n-form ref="urlFormRef" :model="urlForm" label-placement="left" label-width="80">
        <n-form-item label="URL" path="url" :rule="{ required: true, message: '请输入 URL' }">
          <n-input v-model:value="urlForm.url" placeholder="音乐 URL 或 ID" />
        </n-form-item>

        <n-form-item label="来源" path="source">
          <n-select
            v-model:value="urlForm.source"
            :options="sourceOptions"
            placeholder="选择下载来源"
          />
        </n-form-item>

        <n-form-item label="音质" path="quality">
          <n-select
            v-model:value="urlForm.quality"
            :options="qualityOptions"
            placeholder="选择音质"
          />
        </n-form-item>

        <n-form-item label="标题" path="title">
          <n-input v-model:value="urlForm.title" placeholder="可选，覆盖自动识别的标题" />
        </n-form-item>

        <n-form-item label="艺术家" path="artist">
          <n-input v-model:value="urlForm.artist" placeholder="可选，覆盖自动识别的艺术家" />
        </n-form-item>

        <n-form-item label="专辑" path="album">
          <n-input v-model:value="urlForm.album" placeholder="可选，覆盖自动识别的专辑" />
        </n-form-item>
      </n-form>

      <template #footer>
        <n-space justify="end">
          <n-button @click="showUrlModal = false">取消</n-button>
          <n-button type="primary" @click="handleUrlDownload" :loading="downloadingByUrl">
            开始下载
          </n-button>
        </n-space>
      </template>
    </n-modal>
  </div>
</template>

<script setup lang="ts">
import { ref, computed, onMounted, onUnmounted, h } from 'vue'
import {
  NPageHeader,
  NCard,
  NSpace,
  NButton,
  NIcon,
  NTabs,
  NTabPane,
  NDataTable,
  NEmpty,
  NModal,
  NForm,
  NFormItem,
  NInput,
  NInputNumber,
  NSelect,
  NStatistic,
  NTag,
  NProgress,
  useMessage,
  useDialog,
  type FormInst,
  type DataTableColumns,
} from 'naive-ui'
import { Refresh, DownloadOutline, PlayCircleOutline, RefreshOutline } from '@vicons/ionicons5'

const RefreshIcon = Refresh
const DownloadIcon = DownloadOutline
const PlayIcon = PlayCircleOutline
const RetryIcon = RefreshOutline

const message = useMessage()
const dialog = useDialog()

// 状态
const loading = ref(false)
const searching = ref(false)
const downloadingByUrl = ref(false)
const showSearchModal = ref(false)
const showUrlModal = ref(false)
const activeTab = ref('downloading')

// 下载任务
const activeDownloads = ref<any[]>([])
const completedDownloads = ref<any[]>([])
const failedDownloads = ref<any[]>([])
const downloadHistory = ref<any[]>([])

// 统计
const stats = ref({
  total: 0,
  completed: 0,
  failed: 0,
})

// 计算成功率
const successRate = computed(() => {
  const total = stats.value.completed + stats.value.failed
  return total > 0 ? Math.round((stats.value.completed / total) * 100) : 0
})

// 表单引用
const searchFormRef = ref<FormInst | null>(null)
const urlFormRef = ref<FormInst | null>(null)

// 搜索表单
const searchForm = ref({
  keyword: '',
  source: 'netease',
  quality: 'standard',
  limit: 1,
})

// URL 表单
const urlForm = ref({
  url: '',
  source: 'netease',
  quality: 'standard',
  title: '',
  artist: '',
  album: '',
})

// 选项
const sourceOptions = [
  { label: '网易云音乐', value: 'netease' },
  // TODO: 添加其他来源
]

const qualityOptions = [
  { label: '标准 (128kbps)', value: 'standard' },
  { label: '高品质 (320kbps)', value: 'high' },
  { label: '无损 (FLAC)', value: 'lossless' },
]

// 表格列定义（使用 h 函数代替 JSX）
const downloadingColumns: DataTableColumns<any> = [
  {
    title: '标题',
    key: 'title',
    render: (row) => row.title || row.task_id,
  },
  {
    title: '艺术家',
    key: 'artist',
    render: (row) => row.artist || '-',
  },
  {
    title: '专辑',
    key: 'album',
    render: (row) => row.album || '-',
  },
  {
    title: '音质',
    key: 'quality',
    render: (row) => {
      const qualityMap: Record<string, string> = {
        standard: '标准',
        high: '高品质',
        lossless: '无损',
      }
      return qualityMap[row.quality] || row.quality
    },
  },
  {
    title: '进度',
    key: 'progress',
    render: (row) => {
      const percentage = (row.progress || 0) * 100
      return h(NProgress, { percentage, indicatorPlacement: 'inside', processing: true })
    },
  },
  {
    title: '状态',
    key: 'status',
    render: () => h(NTag, { type: 'info' }, () => '下载中'),
  },
  {
    title: '操作',
    key: 'actions',
    render: (row) => {
      return h(NSpace, null, {
        default: () => h(NButton, { size: 'small', onClick: () => cancelDownload(row.task_id) }, () => '取消')
      })
    },
  },
]

const completedColumns: DataTableColumns<any> = [
  {
    title: '标题',
    key: 'title',
    render: (row) => row.title || row.task_id,
  },
  {
    title: '艺术家',
    key: 'artist',
    render: (row) => row.artist || '-',
  },
  {
    title: '专辑',
    key: 'album',
    render: (row) => row.album || '-',
  },
  {
    title: '音质',
    key: 'quality',
    render: (row) => {
      const qualityMap: Record<string, string> = {
        standard: '标准',
        high: '高品质',
        lossless: '无损',
      }
      return qualityMap[row.quality] || row.quality
    },
  },
  {
    title: '文件大小',
    key: 'file_size',
    render: (row) => row.total_bytes ? formatFileSize(row.total_bytes) : '-',
  },
  {
    title: '文件路径',
    key: 'file_path',
    render: (row) => row.file_path || '-',
  },
  {
    title: '操作',
    key: 'actions',
    render: (row) => {
      return h(NSpace, null, {
        default: () => h(NButton, { size: 'small', type: 'primary', onClick: () => playTrack(row.file_path) }, {
          default: () => [h(NIcon, null, { default: () => h(PlayIcon) }), '播放']
        })
      })
    },
  },
]

const failedColumns: DataTableColumns<any> = [
  {
    title: '标题',
    key: 'title',
    render: (row) => row.title || row.task_id,
  },
  {
    title: '艺术家',
    key: 'artist',
    render: (row) => row.artist || '-',
  },
  {
    title: '专辑',
    key: 'album',
    render: (row) => row.album || '-',
  },
  {
    title: '错误信息',
    key: 'error_message',
    render: (row) => row.error_message || '-',
  },
  {
    title: '操作',
    key: 'actions',
    render: (row) => {
      return h(NSpace, null, {
        default: () => h(NButton, { size: 'small', onClick: () => retryDownload(row) }, {
          default: () => [h(NIcon, null, { default: () => h(RetryIcon) }), '重试']
        })
      })
    },
  },
]

const historyColumns: DataTableColumns<any> = [
  {
    title: '标题',
    key: 'title',
    render: (row) => row.title || '-',
  },
  {
    title: '艺术家',
    key: 'artist',
    render: (row) => row.artist || '-',
  },
  {
    title: '专辑',
    key: 'album',
    render: (row) => row.album || '-',
  },
  {
    title: '来源',
    key: 'source',
    render: (row) => {
      const sourceMap: Record<string, string> = {
        netease: '网易云音乐',
      }
      return sourceMap[row.source] || row.source
    },
  },
  {
    title: '状态',
    key: 'status',
    render: (row) => {
      const statusMap: Record<string, { type: any; text: string }> = {
        pending: { type: 'default', text: '等待中' },
        downloading: { type: 'info', text: '下载中' },
        completed: { type: 'success', text: '已完成' },
        failed: { type: 'error', text: '失败' },
        cancelled: { type: 'warning', text: '已取消' },
      }
      const status = statusMap[row.status] || { type: 'default', text: row.status }
      return h(NTag, { type: status.type }, () => status.text)
    },
  },
  {
    title: '时间',
    key: 'created_at',
    render: (row) => row.created_at ? formatDate(row.created_at) : '-',
  },
]

// 方法
const refresh = async () => {
  loading.value = true
  try {
    await Promise.all([
      fetchActiveDownloads(),
      fetchCompletedDownloads(),
      fetchFailedDownloads(),
      fetchDownloadHistory(),
      fetchStats(),
    ])
    message.success('刷新成功')
  } catch (error) {
    message.error('刷新失败')
  } finally {
    loading.value = false
  }
}

const fetchActiveDownloads = async () => {
  // TODO: 调用 API 获取活跃下载
  // const response = await api.get('/api/v1/downloads/active')
  // activeDownloads.value = response.data
}

const fetchCompletedDownloads = async () => {
  // TODO: 调用 API 获取已完成下载
  // const response = await api.get('/api/v1/downloads/completed')
  // completedDownloads.value = response.data
}

const fetchFailedDownloads = async () => {
  // TODO: 调用 API 获取失败下载
  // const response = await api.get('/api/v1/downloads/failed')
  // failedDownloads.value = response.data
}

const fetchDownloadHistory = async () => {
  // TODO: 调用 API 获取下载历史
  // const response = await api.get('/api/v1/download/history')
  // downloadHistory.value = response.data
}

const fetchStats = async () => {
  // TODO: 调用 API 获取下载统计
  // const response = await api.get('/api/v1/downloads/stats')
  // stats.value = response.data
}

const handleSearchAndDownload = async () => {
  try {
    await searchFormRef.value?.validate()

    searching.value = true
    // TODO: 调用 API 搜索并下载
    // await api.post('/api/v1/downloads/search-and-download', searchForm.value)

    message.success('下载任务已添加')
    showSearchModal.value = false

    // 刷新下载列表
    await refresh()

    // 重置表单
    searchForm.value = {
      keyword: '',
      source: 'netease',
      quality: 'standard',
      limit: 1,
    }
  } catch (error: any) {
    if (error.errors) {
      // 表单验证错误
      return
    }
    message.error(error.message || '下载失败')
  } finally {
    searching.value = false
  }
}

const handleUrlDownload = async () => {
  try {
    await urlFormRef.value?.validate()

    downloadingByUrl.value = true
    // TODO: 调用 API 通过 URL 下载
    // await api.post('/api/v1/downloads/download-by-url', urlForm.value)

    message.success('下载任务已添加')
    showUrlModal.value = false

    // 刷新下载列表
    await refresh()

    // 重置表单
    urlForm.value = {
      url: '',
      source: 'netease',
      quality: 'standard',
      title: '',
      artist: '',
      album: '',
    }
  } catch (error: any) {
    if (error.errors) {
      return
    }
    message.error(error.message || '下载失败')
  } finally {
    downloadingByUrl.value = false
  }
}

const cancelDownload = async (taskId: string) => {
  dialog.warning({
    title: '取消下载',
    content: '确定要取消这个下载任务吗？',
    positiveText: '确定',
    negativeText: '取消',
    onPositiveClick: async () => {
      try {
        // TODO: 调用 API 取消下载
        // await api.post(`/api/v1/downloads/${taskId}/cancel`)

        message.success('已取消下载')
        await refresh()
      } catch (error) {
        message.error('取消失败')
      }
    },
  })
}

const retryDownload = async (task: any) => {
  try {
    // TODO: 调用 API 重试下载
    // await api.post(`/api/v1/downloads/${task.task_id}/retry`)

    message.success('已重新开始下载')
    await refresh()
  } catch (error) {
    message.error('重试失败')
  }
}

const playTrack = async (filePath: string) => {
  // TODO: 调用播放器播放
  // playerStore.playTrack(filePath)
  message.info('播放功能待实现')
}

const formatFileSize = (bytes: number): string => {
  if (bytes === 0) return '0 B'
  const k = 1024
  const sizes = ['B', 'KB', 'MB', 'GB']
  const i = Math.floor(Math.log(bytes) / Math.log(k))
  return Math.round((bytes / Math.pow(k, i)) * 100) / 100 + ' ' + sizes[i]
}

const formatDate = (dateStr: string): string => {
  const date = new Date(dateStr)
  return date.toLocaleString('zh-CN')
}

// 定时刷新下载状态
let refreshTimer: NodeJS.Timeout | null = null

onMounted(async () => {
  await refresh()

  // 每 5 秒刷新一次活跃下载
  refreshTimer = setInterval(async () => {
    if (activeTab.value === 'downloading') {
      await fetchActiveDownloads()
    }
  }, 5000)
})

onUnmounted(() => {
  if (refreshTimer) {
    clearInterval(refreshTimer)
    refreshTimer = null
  }
})
</script>

<style scoped>
.download-view {
  padding: 20px;
}

.stats-card {
  margin-bottom: 20px;
}
</style>