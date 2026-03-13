<template>
  <div class="organize-view">
    <n-page-header title="文件整理">
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

    <!-- 整理统计 -->
    <n-card class="stats-card">
      <n-space justify="space-around">
        <n-statistic label="总任务数" :value="stats.total" />
        <n-statistic label="已完成" :value="stats.completed" />
        <n-statistic label="处理中" :value="stats.processing" />
        <n-statistic label="失败" :value="stats.failed" />
      </n-space>
    </n-card>

    <!-- 整理任务列表 -->
    <n-card>
      <n-data-table
        :columns="columns"
        :data="tasks"
        :loading="loading"
        :pagination="{ pageSize: 20 }"
        row-key="id"
      />
      <n-empty v-if="!loading && tasks.length === 0" description="没有整理任务" />
    </n-card>
  </div>
</template>

<script setup lang="ts">
import { ref, onMounted, h } from 'vue'
import {
  NPageHeader,
  NCard,
  NSpace,
  NButton,
  NIcon,
  NDataTable,
  NEmpty,
  NStatistic,
  NTag,
  useMessage,
  type DataTableColumns,
} from 'naive-ui'
import { Refresh as RefreshIcon, RefreshOutline } from '@vicons/ionicons5'
import { organizeApi, type OrganizeTask } from '@/api/modules/organizeApi'

const message = useMessage()
const loading = ref(false)
const tasks = ref<OrganizeTask[]>([])

const stats = ref({
  total: 0,
  completed: 0,
  processing: 0,
  failed: 0,
})

const columns: DataTableColumns<OrganizeTask> = [
  {
    title: 'ID',
    key: 'id',
    width: 60,
  },
  {
    title: '源路径',
    key: 'source_path',
    ellipsis: { tooltip: true },
  },
  {
    title: '目标路径',
    key: 'target_path',
    ellipsis: { tooltip: true },
  },
  {
    title: '状态',
    key: 'status',
    render: (row) => {
      const statusMap: Record<string, { type: any; text: string }> = {
        pending: { type: 'default', text: '等待中' },
        processing: { type: 'info', text: '处理中' },
        completed: { type: 'success', text: '已完成' },
        failed: { type: 'error', text: '失败' },
      }
      const status = statusMap[row.status] || { type: 'default', text: row.status }
      return h(NTag, { type: status.type }, () => status.text)
    },
  },
  {
    title: '创建时间',
    key: 'created_at',
    render: (row) => row.created_at ? formatDate(row.created_at) : '-',
  },
  {
    title: '操作',
    key: 'actions',
    width: 100,
    render: (row) => {
      if (row.status === 'failed') {
        return h(NButton, { size: 'small', onClick: () => retryTask(row.id) }, {
          default: () => [h(NIcon, null, { default: () => h(RefreshOutline) }), '重试']
        })
      }
      return null
    },
  },
]

const fetchTasks = async () => {
  loading.value = true
  try {
    const data = await organizeApi.getTasks()
    tasks.value = data

    // 计算统计
    stats.value = {
      total: data.length,
      completed: data.filter(t => t.status === 'completed').length,
      processing: data.filter(t => t.status === 'processing' || t.status === 'pending').length,
      failed: data.filter(t => t.status === 'failed').length,
    }
  } catch (error) {
    message.error('获取整理任务失败')
  } finally {
    loading.value = false
  }
}

const retryTask = async (id: number) => {
  try {
    await organizeApi.retryTask(id)
    message.success('已重新开始整理')
    await fetchTasks()
  } catch (error) {
    message.error('重试失败')
  }
}

const refresh = async () => {
  await fetchTasks()
  message.success('刷新成功')
}

const formatDate = (dateStr: string): string => {
  const date = new Date(dateStr)
  return date.toLocaleString('zh-CN')
}

onMounted(fetchTasks)
</script>

<style scoped>
.organize-view {
  padding: 20px;
}

.stats-card {
  margin-bottom: 20px;
}
</style>