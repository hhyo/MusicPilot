<template>
  <div class="site-view">
    <n-page-header title="站点管理" @back="handleBack">
      <template #extra>
        <n-button type="primary" @click="showCreateModal = true">
          <template #icon>
            <n-icon><PlusOutlined /></n-icon>
          </template>
          添加站点
        </n-button>
      </template>
    </n-page-header>

    <n-spin :show="loading">
      <n-empty v-if="!loading && !sites.length" description="暂无站点" />
      <n-list v-else>
        <n-list-item v-for="site in sites" :key="site.id">
          <template #prefix>
            <n-icon
              :size="24"
              :color="site.enabled ? '#18a058' : '#d03050'"
            >
              <CloudServerOutlined v-if="site.enabled" />
              <StopOutlined v-else />
            </n-icon>
          </template>

          <div class="site-item">
            <div class="site-info">
              <div class="site-name">{{ site.name }}</div>
              <div class="site-domain">{{ site.domain || site.url }}</div>
              <div class="site-meta">
                <n-tag size="small" type="info">{{ site.downloader }}</n-tag>
                <n-tag size="small" :type="site.site_type === 'resource' ? 'success' : 'default'">
                  {{ site.site_type === 'resource' ? '资源站点' : '其他' }}
                </n-tag>
                <n-tag size="small">优先级 {{ site.priority }}</n-tag>
              </div>
            </div>

            <div class="site-actions">
              <n-button-group>
                <n-button size="small" @click="handleEdit(site)">
                  编辑
                </n-button>
                <n-button
                  size="small"
                  @click="handleTest(site.id)"
                  :loading="testingSiteId === site.id"
                >
                  测试
                </n-button>
                <n-button
                  size="small"
                  @click="handleToggle(site)"
                  :type="site.enabled ? 'warning' : 'success'"
                >
                  {{ site.enabled ? '禁用' : '启用' }}
                </n-button>
                <n-button
                  size="small"
                  type="error"
                  @click="handleDelete(site)"
                >
                  删除
                </n-button>
              </n-button-group>
            </div>
          </div>
        </n-list-item>
      </n-list>
    </n-spin>

    <!-- 创建/编辑站点对话框 -->
    <n-modal
      v-model:show="showCreateModal"
      preset="dialog"
      :title="editingSite ? '编辑站点' : '添加站点'"
      positive-text="确定"
      negative-text="取消"
      @positive-click="handleSaveSite"
    >
      <n-form
        ref="formRef"
        :model="formData"
        :rules="formRules"
        label-placement="left"
        label-width="120px"
        require-mark-placement="right-hanging"
      >
        <n-form-item label="站点名称" path="name">
          <n-input v-model:value="formData.name" placeholder="请输入站点名称" />
        </n-form-item>

        <n-form-item label="站点 URL" path="url">
          <n-input v-model:value="formData.url" placeholder="https://example.com" />
        </n-form-item>

        <n-form-item label="域名" path="domain">
          <n-input v-model:value="formData.domain" placeholder="example.com" />
        </n-form-item>

        <n-form-item label="用户名" path="username">
          <n-input v-model:value="formData.username" placeholder="请输入用户名" />
        </n-form-item>

        <n-form-item label="密码" path="password">
          <n-input
            v-model:value="formData.password"
            type="password"
            show-password-on="click"
            placeholder="请输入密码"
          />
        </n-form-item>

        <n-form-item label="Passkey" path="passkey">
          <n-input v-model:value="formData.passkey" placeholder="请输入 Passkey" />
        </n-form-item>

        <n-form-item label="Cookie" path="cookie">
          <n-input
            v-model:value="formData.cookie"
            type="textarea"
            placeholder="请输入 Cookie"
            :rows="3"
          />
        </n-form-item>

        <n-form-item label="代理" path="proxy">
          <n-input v-model:value="formData.proxy" placeholder="http://proxy:port" />
        </n-form-item>

        <n-form-item label="下载器" path="downloader">
          <n-select
            v-model:value="formData.downloader"
            :options="downloaderOptions"
            placeholder="选择下载器"
          />
        </n-form-item>

        <n-form-item label="优先级" path="priority">
          <n-input-number v-model:value="formData.priority" :min="1" :max="10" />
        </n-form-item>

        <n-form-item label="启用站点" path="enabled">
          <n-switch v-model:value="formData.enabled" />
        </n-form-item>
      </n-form>
    </n-modal>

    <!-- 删除确认对话框 -->
    <n-modal
      v-model:show="showDeleteModal"
      preset="dialog"
      title="确认删除"
      content="确定要删除该站点吗？"
      positive-text="删除"
      negative-text="取消"
      @positive-click="confirmDelete"
    />
  </div>
</template>

<script setup lang="ts">
import { ref, onMounted, h } from 'vue'
import { useRouter } from 'vue-router'
import {
  NPageHeader,
  NButton,
  NIcon,
  NSpin,
  NEmpty,
  NList,
  NListItem,
  NTag,
  NButtonGroup,
  NModal,
  NForm,
  NFormItem,
  NInput,
  NInputNumber,
  NSelect,
  NSwitch,
  NCard,
  NDivider,
  useDialog,
  useMessage
} from 'naive-ui'
import {
  PlusOutlined,
  CloudServerOutlined,
  StopOutlined,
  EditOutlined,
  DeleteOutlined,
  CheckCircleOutlined,
  CloseCircleOutlined
} from '@vicons/antd'
import { useSiteStore, type Site, type SiteCreate, type SiteUpdate } from '@/store/site'
import type { FormInst, FormRules } from 'naive-ui'

const router = useRouter()
const dialog = useDialog()
const message = useMessage()
const siteStore = useSiteStore()

const { sites, loading, total } = siteStore
const showCreateModal = ref(false)
const showDeleteModal = ref(false)
const editingSite = ref<Site | null>(null)
const siteToDelete = ref<Site | null>(null)
const testingSiteId = ref<number | null>(null)

const formRef = ref<FormInst | null>(null)
const formData = ref<SiteCreate>({
  name: '',
  url: '',
  domain: '',
  username: '',
  password: '',
  passkey: '',
  cookie: '',
  proxy: '',
  downloader: 'qbittorrent',
  priority: 1,
  enabled: true,
  site_type: 'resource',
  timeout: 30,
  rss_interval: 60,
})

const downloaderOptions = [
  { label: 'qBittorrent', value: 'qbittorrent' },
  { label: 'Transmission', value: 'transmission' },
]

const formRules: FormRules = {
  name: [
    { required: true, message: '请输入站点名称', trigger: 'blur' }
  ],
  url: [
    { required: true, message: '请输入站点 URL', trigger: 'blur' },
    { type: 'url', message: '请输入有效的 URL', trigger: 'blur' }
  ],
  downloader: [
    { required: true, message: '请选择下载器', trigger: 'change' }
  ],
}

const handleBack = () => {
  router.back()
}

const handleEdit = (site: Site) => {
  editingSite.value = site
  formData.value = {
    name: site.name,
    url: site.url,
    domain: site.domain,
    username: site.username,
    password: site.password,
    passkey: site.passkey,
    cookie: site.cookie,
    proxy: site.proxy,
    downloader: site.downloader,
    priority: site.priority,
    enabled: site.enabled,
    site_type: site.site_type,
    timeout: site.timeout,
    rss_interval: site.rss_interval,
  }
  showCreateModal.value = true
}

const handleTest = async (id: number) => {
  testingSiteId.value = id
  try {
    const response = await siteStore.testSite(id)
    dialog.success({
      title: '测试结果',
      content: response.message,
      positiveText: '确定',
    })
  } finally {
    testingSiteId.value = null
  }
}

const handleToggle = async (site: Site) => {
  await siteStore.toggleSite(site.id)
}

const handleDelete = (site: Site) => {
  siteToDelete.value = site
  showDeleteModal.value = true
}

const confirmDelete = async () => {
  if (siteToDelete.value) {
    await siteStore.deleteSite(siteToDelete.value.id)
    showDeleteModal.value = false
    siteToDelete.value = null
  }
}

const handleSaveSite = async () => {
  try {
    await formRef.value?.validate()

    if (editingSite.value) {
      // 更新站点
      await siteStore.updateSite(editingSite.value.id, formData.value)
    } else {
      // 创建站点
      await siteStore.createSite(formData.value)
    }

    showCreateModal.value = false
    editingSite.value = null
    resetForm()
  } catch (error) {
    // 表单验证失败，不关闭对话框
  }
}

const resetForm = () => {
  formData.value = {
    name: '',
    url: '',
    domain: '',
    username: '',
    password: '',
    passkey: '',
    cookie: '',
    proxy: '',
    downloader: 'qbittorrent',
    priority: 1,
    enabled: true,
    site_type: 'resource',
    timeout: 30,
    rss_interval: 60,
  }
}

onMounted(() => {
  siteStore.fetchSites()
})
</script>

<style scoped>
.site-view {
  padding: 20px;
}

.site-item {
  display: flex;
  justify-content: space-between;
  align-items: center;
  width: 100%;
}

.site-info {
  flex: 1;
}

.site-name {
  font-size: 16px;
  font-weight: 500;
  margin-bottom: 4px;
}

.site-domain {
  font-size: 14px;
  color: var(--n-text-color-2);
  margin-bottom: 8px;
}

.site-meta {
  display: flex;
  gap: 8px;
}

.site-actions {
  margin-left: 16px;
}
</style>