<template>
  <div class="page-shell">
    <VCard class="hero-card">
      <VCardText class="pa-6">
        <p class="eyebrow">Settings</p>
        <h2 class="section-title">运行时 provider 与 RSS feed 配置</h2>
        <p class="section-note">
          设置页只维护当前真实可用的 provider settings。这里直接读写
          `/settings/providers`，不再保留旧的占位说明页，也不做表格化 feed CRUD。
        </p>
      </VCardText>
    </VCard>

    <VAlert
      v-if="feedbackMessage"
      :type="feedbackType"
      variant="tonal"
      density="comfortable"
      :text="feedbackMessage"
    />

    <div class="split-layout">
      <VCard class="panel-card">
        <VCardText class="stack pa-6">
          <div>
            <p class="eyebrow">Providers</p>
            <h3 class="section-title">榜单发现主模式</h3>
            <p class="section-note">
              family 由后端自动识别。这里先只编辑 `chart_provider_mode` 和 `chart_rss_feeds`。
            </p>
          </div>

          <VSelect
            v-model="providerMode"
            :items="providerModeOptions"
            item-title="label"
            item-value="value"
            label="Chart Provider Mode"
          />

          <div class="meta-pairs">
            <div class="meta-pair">
              <span class="meta-pair__label">Current Mode</span>
              <span class="meta-pair__value">{{ providerMode }}</span>
            </div>
            <div class="meta-pair">
              <span class="meta-pair__label">Metadata Provider</span>
              <span class="meta-pair__value">{{ metadataProviderMode || '未配置' }}</span>
            </div>
          </div>

          <div class="soft-block">
            <p class="eyebrow">说明</p>
            <p class="section-note">
              保存后会直接影响 Discovery 页面读取的榜单源和默认顺序。当前不提供 family 手工编辑，也不在这里改 metadata provider。
            </p>
          </div>
        </VCardText>
      </VCard>

      <VCard class="panel-card">
        <VCardText class="stack pa-6">
          <div>
            <p class="eyebrow">RSS Feed JSON</p>
            <h3 class="section-title">结构化 feed 列表</h3>
            <p class="section-note">
              保持数组结构。空数组会原样提交，不会被前端偷偷补默认值。
            </p>
          </div>

          <VTextarea
            v-model="rssFeedsJson"
            label="chart_rss_feeds"
            rows="18"
            auto-grow
            spellcheck="false"
          />

          <div class="metadata-drawer__actions">
            <VBtn variant="tonal" :disabled="loading || saving" @click="loadProviderSettings">
              重新加载
            </VBtn>
            <VBtn color="primary" :loading="saving" :disabled="loading || saving" @click="saveProviderSettings">
              保存设置
            </VBtn>
          </div>
        </VCardText>
      </VCard>
    </div>
  </div>
</template>

<script setup lang="ts">
import { onMounted, ref } from 'vue';

import { fetchProviderSettings, updateProviderSettings } from '@/services/settings';
import type {
  ChartProviderMode,
  ChartRssFeedSettings,
  ProviderSettingsResponseData,
} from '@/types/settings';

const providerModeOptions: Array<{ value: ChartProviderMode; label: string }> = [
  { value: 'mock', label: 'mock' },
  { value: 'listenbrainz', label: 'listenbrainz' },
  { value: 'rss_feed', label: 'rss_feed' },
];

const providerMode = ref<ChartProviderMode>('mock');
const metadataProviderMode = ref<string | null>(null);
const rssFeedsJson = ref('[]');
const loading = ref(false);
const saving = ref(false);
const feedbackMessage = ref('');
const feedbackType = ref<'success' | 'info' | 'warning' | 'error'>('info');

onMounted(() => {
  void loadProviderSettings();
});

async function loadProviderSettings() {
  loading.value = true;
  feedbackMessage.value = '';
  try {
    const response = await fetchProviderSettings();
    applyProviderSettings(response.data);
    feedbackType.value = 'info';
    feedbackMessage.value = '已加载当前 provider settings。';
  } catch (error) {
    feedbackType.value = 'error';
    feedbackMessage.value = resolveErrorMessage(error, '加载 provider settings 失败。');
  } finally {
    loading.value = false;
  }
}

async function saveProviderSettings() {
  const parsedFeeds = parseFeedsJson();
  if (!parsedFeeds) return;

  saving.value = true;
  feedbackMessage.value = '';
  try {
    const response = await updateProviderSettings({
      chart_provider_mode: providerMode.value,
      chart_rss_feeds: parsedFeeds,
    });
    applyProviderSettings(response.data);
    feedbackType.value = 'success';
    feedbackMessage.value = '保存成功，运行时 settings 已更新。';
  } catch (error) {
    feedbackType.value = 'error';
    feedbackMessage.value = resolveErrorMessage(error, '保存 provider settings 失败。');
  } finally {
    saving.value = false;
  }
}

function applyProviderSettings(data: ProviderSettingsResponseData) {
  providerMode.value = data.chart_provider_mode;
  metadataProviderMode.value = data.metadata_provider_mode;
  rssFeedsJson.value = JSON.stringify(data.chart_rss_feeds ?? [], null, 2);
}

function parseFeedsJson(): ChartRssFeedSettings[] | null {
  try {
    const parsed = JSON.parse(rssFeedsJson.value);
    if (!Array.isArray(parsed)) {
      throw new Error('RSS Feed JSON 必须是数组。');
    }
    return parsed as ChartRssFeedSettings[];
  } catch (error) {
    feedbackType.value = 'error';
    feedbackMessage.value = resolveErrorMessage(error, 'RSS Feed JSON 解析失败。');
    return null;
  }
}

function resolveErrorMessage(error: unknown, fallback: string) {
  if (error instanceof Error && error.message) return error.message;
  return fallback;
}
</script>
