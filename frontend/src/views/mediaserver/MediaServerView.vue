<template>
  <div class="mediaserver-view">
    <n-page-header title="媒体服务器">
      <template #extra>
        <n-space>
          <n-button @click="refresh" :loading="loading">
            <template #icon>
              <n-icon><RefreshIcon /></n-icon>
            </template>
            刷新
          </n-button>
          <n-button type="primary" @click="showAddModal = true">
            <template #icon>
              <n-icon><AddIcon /></n-icon>
            </template>
            添加服务器
          </n-button>
          <n-button @click="notifyAll" :loading="notifying">
            通知所有服务器
          </n-button>
        </n-space>
      </template>
    </n-page-header>

    <!-- 媒体服务器列表 -->
    <n-card>
      <n-data-table
        :columns="columns"
        :data="servers"
        :loading="loading"
        :pagination="{ pageSize: 10 }"
        row-key="name"
      />
      <n-empty v-if="!loading && servers.length === 0" description="没有配置媒体服务器" />
    </n-card>

    <!-- 添加服务器弹窗 -->
    <n-modal v-model:show="showAddModal" preset="card" title="添加媒体服务器" style="width: 500px">
      <n-form ref="formRef" :model="form" label-placement="left" label-width="80">
        <n-form-item label="类型" path="type" :rule="{ required: true, message: '请选择类型' }">
          <n-select
            v-model:value="form.type"
            :options="typeOptions"
            placeholder="选择服务器类型"
          />
        </n-form-item>

        <n-form-item label="名称" path="name" :rule="{ required: true, message: '请输入名称' }">
          <n-input v-model:value="form.name" placeholder="服务器名称" />
        </n-form-item>

        <n-form-item label="地址" path="url" :rule="{ required: true, message: '请输入地址' }">
          <n-input v-model:value="form.url" placeholder="http://192.168.1.100:8096" />
        </n-form-item>

        <n-form-item label="API Key" path="api_key" :rule="{ required: true, message: '请输入 API Key' }">
          <n-input v-model:value="form.api_key" type="password" placeholder="API Key" />
        </n-form-item>
      </n-form>

      <template #footer>
        <n-space justify="end">
          <n-button @click="showAddModal = false">取消</n-button>
          <n-button type="primary" @click="handleAdd" :loading="adding">添加</n-button>
        </n-space>
      </template>
    </n-modal>
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
  NModal,
  NForm,
  NFormItem,
  NInput,
  NSelect,
  NSwitch,
  NTag,
  useMessage,
  type DataTableColumns,
  type FormInst,
} from 'naive-ui'
import { Refresh as RefreshIcon, AddOutline } from '@vicons/ionicons5'
import { mediaServerApi, type MediaServer } from '@/api/modules/mediaServerApi'

const message = useMessage()
const loading = ref(false)
const adding = ref(false)
const notifying = ref(false)
const showAddModal = ref(false)
const servers = ref<MediaServer[]>([])

const formRef = ref<FormInst | null>(null)
const form = ref({
  type: 'jellyfin' as 'jellyfin' | 'plex',
  name: '',
  url: '',
  api_key: '',
})

const typeOptions = [
  { label: 'Jellyfin', value: 'jellyfin' },
  { label: 'Plex', value: 'plex' },
]

const columns: DataTableColumns<MediaServer> = [
  {
    title: '名称',
    key: 'name',
  },
  {
    title: '类型',
    key: 'type',
    render: (row) => h(NTag, { type: row.type === 'jellyfin' ? 'info' : 'warning' }, () => row.type.toUpperCase()),
  },
  {
    title: '地址',
    key: 'url',
  },
  {
    title: '状态',
    key: 'enabled',
    render: (row) => h(NTag, { type: row.enabled ? 'success' : 'default' }, () => row.enabled ? '启用' : '禁用'),
  },
  {
    title: '操作',
    key: 'actions',
    render: (row) => {
      return h(NSpace, null, {
        default: () => [
          h(NButton, { size: 'small', onClick: () => refreshLibrary(row.name) }, () => '刷新媒体库'),
        ]
      })
    },
  },
]

const fetchServers = async () => {
  loading.value = true
  try {
    const data = await mediaServerApi.getServers()
    servers.value = data
  } catch (error) {
    message.error('获取媒体服务器失败')
  } finally {
    loading.value = false
  }
}

const handleAdd = async () => {
  try {
    await formRef.value?.validate()
    adding.value = true

    await mediaServerApi.addServer(form.value)
    message.success('添加成功')
    showAddModal.value = false

    // 重置表单
    form.value = {
      type: 'jellyfin',
      name: '',
      url: '',
      api_key: '',
    }

    await fetchServers()
  } catch (error: any) {
    if (error.errors) return
    message.error(error.message || '添加失败')
  } finally {
    adding.value = false
  }
}

const refreshLibrary = async (serverId: string) => {
  try {
    await mediaServerApi.refreshLibrary(serverId)
    message.success('已发送刷新请求')
  } catch (error) {
    message.error('刷新失败')
  }
}

const notifyAll = async () => {
  notifying.value = true
  try {
    await mediaServerApi.notifyAll()
    message.success('已通知所有服务器')
  } catch (error) {
    message.error('通知失败')
  } finally {
    notifying.value = false
  }
}

const refresh = async () => {
  await fetchServers()
  message.success('刷新成功')
}

onMounted(fetchServers)
</script>

<style scoped>
.mediaserver-view {
  padding: 20px;
}
</style>