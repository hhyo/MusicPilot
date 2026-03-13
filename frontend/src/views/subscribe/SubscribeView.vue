<template>
  <div class="subscribe-view">
    <n-page-header title="订阅管理">
      <template #extra>
        <n-button type="primary" @click="showCreateModal = true">
          <template #icon>
            <n-icon><AddIcon /></n-icon>
          </template>
          添加订阅
        </n-button>
      </template>
    </n-page-header>

    <n-card>
      <n-tabs v-model:value="activeTab" type="line" @update:value="handleTabChange">
        <n-tab-pane name="artist" tab="艺术家">
          <SubscribeList
            type="artist"
            :subscribes="artistSubscribes"
            @refresh="loadSubscribes"
            @edit="handleEdit"
            @delete="handleDelete"
          />
        </n-tab-pane>
        <n-tab-pane name="album" tab="专辑">
          <SubscribeList
            type="album"
            :subscribes="albumSubscribes"
            @refresh="loadSubscribes"
            @edit="handleEdit"
            @delete="handleDelete"
          />
        </n-tab-pane>
        <n-tab-pane name="playlist" tab="歌单">
          <SubscribeList
            type="playlist"
            :subscribes="playlistSubscribes"
            @refresh="loadSubscribes"
            @edit="handleEdit"
            @delete="handleDelete"
          />
        </n-tab-pane>
        <n-tab-pane name="chart" tab="榜单">
          <SubscribeList
            type="chart"
            :subscribes="chartSubscribes"
            @refresh="loadSubscribes"
            @edit="handleEdit"
            @delete="handleDelete"
          />
        </n-tab-pane>
        <n-tab-pane name="history" tab="发布记录">
          <SubscribeHistory :subscribes="allSubscribes" />
        </n-tab-pane>
      </n-tabs>
    </n-card>

    <!-- 创建/编辑订阅对话框 -->
    <n-modal v-model:show="showCreateModal" :mask-closable="false">
      <n-card
        style="width: 600px"
        :title="editingSubscribe ? '编辑订阅' : '添加订阅'"
        :bordered="false"
        size="huge"
        role="dialog"
        aria-modal="true"
      >
        <n-form :model="form" :rules="rules" ref="formRef">
          <n-form-item label="订阅类型" path="type">
            <n-select v-model:value="form.type" :options="typeOptions" />
          </n-form-item>

          <n-form-item label="来源类型" path="source_type" v-if="form.type !== 'artist' && form.type !== 'album'">
            <n-select v-model:value="form.source_type" :options="sourceTypeOptions" />
          </n-form-item>

          <n-form-item label="ID" path="id" :label="idLabel">
            <n-input v-model:value="form.id" :placeholder="idPlaceholder" />
          </n-form-item>

          <n-form-item label="名称" path="name">
            <n-input v-model:value="form.name" placeholder="订阅名称" />
          </n-form-item>

          <n-form-item label="描述" path="description">
            <n-input
              v-model:value="form.description"
              type="textarea"
              placeholder="订阅描述（可选）"
              :rows="3"
            />
          </n-form-item>

          <n-form-item label="自动下载" path="auto_download">
            <n-switch v-model:value="form.auto_download" />
          </n-form-item>

          <n-form-item label="下载格式" path="download_format" v-if="form.auto_download">
            <n-select v-model:value="form.download_format" :options="formatOptions" />
          </n-form-item>

          <n-form-item label="订阅规则" path="rules" v-if="form.auto_download && (form.type === 'artist' || form.type === 'album')">
            <n-input
              v-model:value="form.rules_json"
              type="textarea"
              placeholder='{"format": "FLAC", "min_bitrate": 320, "max_size": 500000000}'
              :rows="3"
            />
            <template #feedback>
              JSON 格式的订阅规则，支持 format、min_bitrate、max_size 等字段
            </template>
          </n-form-item>
        </n-form>

        <template #footer>
          <n-space justify="end">
            <n-button @click="showCreateModal = false">取消</n-button>
            <n-button type="primary" @click="handleSubmit" :loading="submitting">
              {{ editingSubscribe ? '保存' : '创建' }}
            </n-button>
          </n-space>
        </template>
      </n-card>
    </n-modal>
  </div>
</template>

<script setup lang="ts">
import { ref, computed, onMounted } from 'vue'
import { NPageHeader, NCard, NButton, NTabs, NTabPane, NModal, NForm, NFormItem, NInput, NSelect, NSwitch, NSpace, NIcon, useMessage, useDialog } from 'naive-ui'
import { AddOutline as AddIcon } from '@vicons/ionicons5'
import SubscribeList from './SubscribeList.vue'
import SubscribeHistory from './SubscribeHistory.vue'
import * as subscribeApi from '@/api/subscribe'

const message = useMessage()
const dialog = useDialog()

const activeTab = ref('artist')
const showCreateModal = ref(false)
const submitting = ref(false)
const editingSubscribe = ref<any>(null)
const formRef = ref<any>(null)

const form = ref({
  type: 'artist',
  source_type: 'netease',
  id: '',
  name: '',
  description: '',
  auto_download: true,
  download_format: 'FLAC',
  rules_json: ''
})

const typeOptions = [
  { label: '艺术家', value: 'artist' },
  { label: '专辑', value: 'album' },
  { label: '歌单', value: 'playlist' },
  { label: '榜单', value: 'chart' }
]

const sourceTypeOptions = [
  { label: '网易云音乐', value: 'netease' },
  { label: 'QQ音乐', value: 'qq' }
]

const formatOptions = [
  { label: 'FLAC', value: 'FLAC' },
  { label: 'MP3', value: 'MP3' },
  { label: 'APE', value: 'APE' }
]

const rules = {
  type: { required: true, message: '请选择订阅类型' },
  id: { required: true, message: '请输入 ID' },
  name: { required: true, message: '请输入名称' }
}

const subscribes = ref<any[]>([])
const allSubscribes = computed(() => subscribes.value)

const artistSubscribes = computed(() => subscribes.value.filter(s => s.type === 'artist'))
const albumSubscribes = computed(() => subscribes.value.filter(s => s.type === 'album'))
const playlistSubscribes = computed(() => subscribes.value.filter(s => s.type === 'playlist'))
const chartSubscribes = computed(() => subscribes.value.filter(s => s.type === 'chart'))

const idLabel = computed(() => {
  switch (form.value.type) {
    case 'artist':
    case 'album':
      return 'MusicBrainz ID'
    case 'playlist':
      return '歌单 ID'
    case 'chart':
      return '榜单 ID'
    default:
      return 'ID'
  }
})

const idPlaceholder = computed(() => {
  switch (form.value.type) {
    case 'artist':
      return '例如：d36e608f-5491-4b9f-9657-90e7c7b5b2ad'
    case 'album':
      return '例如：8a2d8f3a-4b3e-4c2d-9a1f-2b3c4d5e6f7g'
    case 'playlist':
      return '例如：3778678'
    case 'chart':
      return '例如：19723756（飙升榜）'
    default:
      return '请输入 ID'
  }
})

const loadSubscribes = async () => {
  try {
    const data = await subscribeApi.listSubscribes()
    subscribes.value = data.items || []
  } catch (error) {
    message.error('加载订阅失败')
  }
}

const handleTabChange = () => {
  // 切换标签时刷新
}

const handleEdit = (subscribe: any) => {
  editingSubscribe.value = subscribe
  form.value = {
    type: subscribe.type,
    source_type: subscribe.source_type,
    id: subscribe.musicbrainz_id || subscribe.playlist_id || '',
    name: subscribe.name,
    description: subscribe.description || '',
    auto_download: subscribe.auto_download,
    download_format: subscribe.download_format,
    rules_json: subscribe.rules ? JSON.stringify(subscribe.rules, null, 2) : ''
  }
  showCreateModal.value = true
}

const handleDelete = (subscribe: any) => {
  dialog.warning({
    title: '确认删除',
    content: `确定要删除订阅 "${subscribe.name}" 吗？`,
    positiveText: '删除',
    negativeText: '取消',
    onPositiveClick: async () => {
      try {
        await subscribeApi.deleteSubscribe(subscribe.id)
        message.success('删除成功')
        await loadSubscribes()
      } catch (error) {
        message.error('删除失败')
      }
    }
  })
}

const handleSubmit = async () => {
  try {
    await formRef.value?.validate()

    submitting.value = true

    const payload: any = {
      type: form.value.type,
      source_type: form.value.source_type,
      name: form.value.name,
      description: form.value.description,
      auto_download: form.value.auto_download,
      download_format: form.value.download_format
    }

    // 设置 ID 字段
    if (form.value.type === 'artist' || form.value.type === 'album') {
      payload.musicbrainz_id = form.value.id
    } else {
      payload.playlist_id = form.value.id
    }

    // 解析规则
    if (form.value.rules_json) {
      try {
        payload.rules = JSON.parse(form.value.rules_json)
      } catch {
        message.error('订阅规则格式错误')
        return
      }
    }

    if (editingSubscribe.value) {
      await subscribeApi.updateSubscribe(editingSubscribe.value.id, payload)
      message.success('更新成功')
    } else {
      await subscribeApi.createSubscribe(payload)
      message.success('创建成功')
    }

    showCreateModal.value = false
    editingSubscribe.value = null
    await loadSubscribes()
  } catch (error: any) {
    if (error?.errorFields) {
      // 表单验证错误
      return
    }
    message.error(editingSubscribe.value ? '更新失败' : '创建失败')
  } finally {
    submitting.value = false
  }
}

const resetForm = () => {
  form.value = {
    type: 'artist',
    source_type: 'netease',
    id: '',
    name: '',
    description: '',
    auto_download: true,
    download_format: 'FLAC',
    rules_json: ''
  }
}

// 监听模态框关闭，重置表单
watch(showCreateModal, (val) => {
  if (!val) {
    resetForm()
    editingSubscribe.value = null
  }
})

onMounted(() => {
  loadSubscribes()
})
</script>

<style scoped>
.subscribe-view {
  padding: 20px;
}
</style>