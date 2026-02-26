<template>
  <div class="subscribe-history">
    <n-space vertical>
      <n-space justify="space-between">
        <n-space>
          <n-text strong>发布记录</n-text>
        </n-space>
        <n-space>
          <n-select
            v-model:value="selectedSubscribeId"
            :options="subscribeOptions"
            placeholder="选择订阅"
            style="width: 200px"
            clearable
          />
        </n-space>
      </n-space>

      <n-spin :show="loading">
        <n-empty v-if="!loading && releases.length === 0" description="暂无发布记录" />

        <n-data-table
          v-else
          :columns="columns"
          :data="releases"
          :pagination="pagination"
          :bordered="false"
        />
      </n-spin>
    </n-space>
  </div>
</template>

<script setup lang="ts">
import { ref, computed, h } from 'vue'
import { NSpace, NText, NSelect, NSpin, NEmpty, NDataTable, NTag, NButton, useMessage } from 'naive-ui'
import * as subscribeApi from '@/api/subscribe'

interface Props {
  subscribes: any[]
}

const props = defineProps<Props>()

const message = useMessage()
const loading = ref(false)
const selectedSubscribeId = ref<number | null>(null)
const releases = ref<any[]>([])

const subscribeOptions = computed(() => {
  return props.subscribes.map(s => ({
    label: s.name,
    value: s.id
  }))
})

const columns = [
  {
    title: '订阅',
    key: 'subscribe_name',
    width: 150,
    ellipsis: {
      tooltip: true
    }
  },
  {
    title: '标题',
    key: 'title',
    width: 200,
    ellipsis: {
      tooltip: true
    }
  },
  {
    title: '艺术家',
    key: 'artist',
    width: 150,
    ellipsis: {
      tooltip: true
    }
  },
  {
    title: '类型',
    key: 'release_type',
    width: 80,
    render: (row: any) => {
      const typeMap: Record<string, { text: string, type: any }> = {
        'album': { text: '专辑', type: 'info' },
        'track': { text: '单曲', type: 'default' }
      }
      const type = typeMap[row.release_type] || { text: row.release_type, type: 'default' }
      return h(NTag, { type: type.type, size: 'small' }, { default: () => type.text })
    }
  },
  {
    title: '下载状态',
    key: 'download_status',
    width: 100,
    render: (row: any) => {
      const statusMap: Record<string, { text: string, type: any }> = {
        'pending': { text: '等待中', type: 'default' },
        'downloading': { text: '下载中', type: 'info' },
        'completed': { text: '已完成', type: 'success' },
        'failed': { text: '失败', type: 'error' }
      }
      const status = statusMap[row.download_status] || { text: row.download_status, type: 'default' }
      return h(NTag, { type: status.type, size: 'small' }, { default: () => status.text })
    }
  },
  {
    title: '发布时间',
    key: 'created_at',
    width: 180,
    render: (row: any) => new Date(row.created_at).toLocaleString()
  },
  {
    title: '操作',
    key: 'actions',
    width: 100,
    render: (row: any) => {
      return h(NSpace, {}, {
        default: () => [
          h(NButton, {
            text: true,
            size: 'small',
            onClick: () => viewDetails(row)
          }, { default: () => '详情' })
        ]
      })
    }
  }
]

const pagination = {
  pageSize: 20
}

const loadReleases = async () => {
  loading.value = true
  try {
    let data
    if (selectedSubscribeId.value) {
      data = await subscribeApi.getSubscribeReleases(selectedSubscribeId.value)
    } else {
      // 获取所有发布记录
      data = await subscribeApi.getAllReleases()
    }
    releases.value = data.items || []
  } catch (error) {
    message.error('加载发布记录失败')
  } finally {
    loading.value = false
  }
}

const viewDetails = (release: any) => {
  // 显示详情对话框
  message.info(`详情：${release.title}`)
}

// 监听订阅选择变化
watch(selectedSubscribeId, () => {
  loadReleases()
})

// 初始加载
onMounted(() => {
  loadReleases()
})
</script>

<style scoped>
.subscribe-history {
  padding: 10px 0;
}
</style>