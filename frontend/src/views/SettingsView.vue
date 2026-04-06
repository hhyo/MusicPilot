<template>
  <div class="settings-view">
    <section class="hero-panel">
      <div>
        <p class="hero-panel__eyebrow">Settings</p>
        <h2>Provider settings 与 RSS Feed 配置</h2>
        <p class="hero-panel__description">
          这里仅维护当前真实可用的 provider settings。页面会直接读取并保存
          `/settings/providers`，不做表格化 CRUD，也不把 feed 变成单条表单。
        </p>
      </div>

      <div class="hero-panel__tags">
        <el-tag effect="plain">{{ providerModeLabel }}</el-tag>
        <el-tag type="info" effect="plain">metadata: {{ metadataProviderModeLabel }}</el-tag>
      </div>
    </section>

    <el-alert
      v-if="feedbackMessage"
      data-test="settings-feedback"
      :title="feedbackMessage"
      :type="feedbackType"
      :closable="false"
      show-icon
    />

    <section class="settings-grid">
      <article class="panel">
        <header class="panel__header">
          <div>
            <p class="panel__eyebrow">Chart Provider Mode</p>
            <h3>榜单发现主模式</h3>
          </div>
          <el-tag effect="plain">runtime discovery</el-tag>
        </header>

        <p class="panel__description">
          当前可选 provider mode 为 `mock`、`listenbrainz` 和 `rss_feed`。`metadata_provider_mode` 只展示，不在这里编辑。
        </p>

        <label class="field">
          <span class="field__label">Chart Provider Mode</span>
          <select v-model="providerMode" data-test="chart-provider-mode" class="field__control">
            <option v-for="option in providerModeOptions" :key="option.value" :value="option.value">
              {{ option.label }}
            </option>
          </select>
        </label>

        <div class="detail-grid">
          <article class="detail-card">
            <span>Metadata Provider</span>
            <strong data-test="metadata-provider-mode">{{ metadataProviderModeLabel }}</strong>
            <p>只读展示，避免在 settings 页混入与榜单发现无关的配置。</p>
          </article>
          <article class="detail-card">
            <span>Current Provider Mode</span>
            <strong>{{ providerModeLabel }}</strong>
            <p>family 由后端按当前 provider mode 自动识别，不需要手工选择。</p>
          </article>
        </div>
      </article>

      <article class="panel">
        <header class="panel__header">
          <div>
            <p class="panel__eyebrow">RSS Feed JSON</p>
            <h3>结构化 feed 配置</h3>
          </div>
          <el-tag type="warning" effect="plain">array payload</el-tag>
        </header>

        <p class="panel__description">
          仅编辑 JSON 数组。保存后会直接影响榜单页 discovery 读取的 feed 来源和排序结果。
        </p>

        <label class="field field--textarea">
          <span class="field__label">chart_rss_feeds</span>
          <textarea
            v-model="rssFeedsJson"
            data-test="rss-feed-json"
            class="field__control field__control--textarea"
            spellcheck="false"
          />
        </label>

        <p class="field__hint">
          保存前会先做 JSON 解析检查。空数组 `[]` 会原样保存，不会被前端兜底改写。
        </p>
      </article>

      <article class="panel panel--wide">
        <header class="panel__header">
          <div>
            <p class="panel__eyebrow">Discovery Notes</p>
            <h3>当前范围说明</h3>
          </div>
        </header>

        <div class="notes-grid">
          <article class="note-card">
            <h4>Provider Mode 范围</h4>
            <p>
              当前 settings 页只提供 provider mode 选择，不提供 family 手工选择。后端会依据 `chart_provider_mode` 和 feed 元数据自动决定 discovery 语义。
            </p>
          </article>
          <article class="note-card">
            <h4>RSS Family 范围</h4>
            <p>
              本轮 RSS discovery 支持的 family 仅包括：`netease_playlist_tracks`、`netease_artist_songs`、`netease_artist_albums`、`youtube_top_songs`、`youtube_top_artists`。
            </p>
          </article>
          <article class="note-card">
            <h4>对榜单页的影响</h4>
            <p>
              保存成功后，榜单页会按新的 provider settings 读取 discovery 结果，直接影响可见榜单与订阅入口。
            </p>
          </article>
        </div>
      </article>
    </section>

    <footer class="actions-bar">
      <p class="actions-bar__hint">
        修改只会原样提交给 `/settings/providers`。最终生效结果以后端运行时优先级和 fallback 规则为准。
      </p>
      <el-button v-if="loadErrorMessage" text data-test="retry-load-provider-settings" @click="loadProviderSettings">
        重试加载
      </el-button>
      <el-button
        type="primary"
        :loading="saving"
        :disabled="loading || saving || !canSave"
        data-test="save-provider-settings"
        @click="saveProviderSettings"
      >
        保存设置
      </el-button>
    </footer>
  </div>
</template>

<script setup lang="ts">
import axios from 'axios';
import { computed, onMounted, ref } from 'vue';
import { ElMessage } from 'element-plus';

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
const canSave = ref(false);
const loadErrorMessage = ref('');
const feedbackMessage = ref('');
const feedbackType = ref<'success' | 'info' | 'warning' | 'error'>('info');

const providerModeLabel = computed(() => providerMode.value);

const metadataProviderModeLabel = computed(() => metadataProviderMode.value || '未配置');

onMounted(() => {
  void loadProviderSettings();
});

async function loadProviderSettings() {
  loading.value = true;
  loadErrorMessage.value = '';
  feedbackMessage.value = '';

  try {
    const response = await fetchProviderSettings();

    if (!response.success) {
      throw new Error(response.message);
    }

    applyProviderSettings(response.data);
    canSave.value = true;
    feedbackType.value = 'info';
    feedbackMessage.value = '已加载当前 provider settings。';
  } catch (error) {
    loadErrorMessage.value = resolveErrorMessage(error, '加载 provider settings 失败。');
    feedbackType.value = 'error';
    feedbackMessage.value = loadErrorMessage.value;
    ElMessage.error(feedbackMessage.value);
  } finally {
    loading.value = false;
  }
}

async function saveProviderSettings() {
  const parsedFeeds = parseFeedsJson();
  if (!parsedFeeds) {
    return;
  }

  saving.value = true;
  feedbackMessage.value = '';

  try {
    const response = await updateProviderSettings({
      chart_provider_mode: providerMode.value,
      chart_rss_feeds: parsedFeeds,
    });

    if (!response.success) {
      throw new Error(resolveResponseErrorMessage(response, '保存 provider settings 失败。'));
    }

    applyProviderSettings(response.data);
    feedbackType.value = 'success';
    feedbackMessage.value = '保存成功，settings 已同步到后端。';
    ElMessage.success(feedbackMessage.value);
  } catch (error) {
    feedbackType.value = 'error';
    feedbackMessage.value = resolveErrorMessage(error, '保存 provider settings 失败。');
    ElMessage.error(feedbackMessage.value);
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
    feedbackMessage.value =
      error instanceof Error ? `RSS Feed JSON 解析失败：${error.message}` : 'RSS Feed JSON 解析失败。';
    ElMessage.error(feedbackMessage.value);
    return null;
  }
}

function resolveResponseErrorMessage(response: Record<string, unknown>, fallback: string) {
  const detail = response.detail;
  if (Array.isArray(detail) && detail.length > 0) {
    const summary = detail
      .map((item) => summarizeValidationIssue(item))
      .filter((item): item is string => Boolean(item))
      .join('; ');

    if (summary) {
      const message = typeof response.message === 'string' && response.message ? response.message : fallback;
      return `${message}: ${summary}`;
    }
  }

  return typeof response.message === 'string' && response.message ? response.message : fallback;
}

function summarizeValidationIssue(issue: unknown) {
  if (!issue || typeof issue !== 'object') {
    return '';
  }

  const record = issue as { loc?: unknown; msg?: unknown };
  const location = Array.isArray(record.loc) ? record.loc.filter((item) => typeof item === 'string').join('.') : '';
  const message = typeof record.msg === 'string' ? record.msg : '';

  if (!location && !message) {
    return '';
  }

  if (!location) {
    return message;
  }

  if (!message) {
    return location;
  }

  return `${location}: ${message}`;
}

function resolveErrorMessage(error: unknown, fallback: string) {
  if (axios.isAxiosError(error)) {
    const responseData = error.response?.data as Record<string, unknown> | undefined;
    if (error.response?.status === 422 && responseData) {
      return resolveResponseErrorMessage(responseData, fallback);
    }

    return responseData?.message as string | undefined ?? error.message ?? fallback;
  }

  if (error instanceof Error) {
    return error.message;
  }

  return fallback;
}
</script>

<style scoped lang="scss">
.settings-view {
  display: grid;
  gap: 1.25rem;
}

.hero-panel,
.panel,
.actions-bar {
  border: 1px solid var(--mp-line);
  border-radius: 28px;
  background: rgba(255, 255, 255, 0.82);
  box-shadow: 0 18px 40px rgba(52, 37, 122, 0.06);
}

.hero-panel {
  display: flex;
  align-items: flex-start;
  justify-content: space-between;
  gap: 1rem;
  padding: 1.35rem;
}

.hero-panel__eyebrow,
.panel__eyebrow {
  margin: 0;
  color: var(--mp-accent);
  font-size: 0.82rem;
  font-weight: 700;
  letter-spacing: 0.08em;
  text-transform: uppercase;
}

.hero-panel h2,
.panel__header h3 {
  margin: 0.35rem 0 0;
}

.hero-panel__description,
.panel__description,
.field__hint,
.note-card p,
.detail-card p,
.actions-bar__hint {
  margin: 0;
  color: var(--mp-muted);
  line-height: 1.75;
}

.hero-panel__tags {
  display: flex;
  gap: 0.6rem;
  flex-wrap: wrap;
}

.settings-grid {
  display: grid;
  grid-template-columns: repeat(2, minmax(0, 1fr));
  gap: 1rem;
}

.panel {
  display: grid;
  gap: 1rem;
  padding: 1.25rem;
}

.panel--wide {
  grid-column: 1 / -1;
}

.panel__header {
  display: flex;
  align-items: flex-start;
  justify-content: space-between;
  gap: 1rem;
}

.field {
  display: grid;
  gap: 0.55rem;
}

.field__label {
  font-size: 0.92rem;
  font-weight: 700;
}

.field__control {
  width: 100%;
  min-height: 44px;
  padding: 0.8rem 0.9rem;
  border: 1px solid var(--mp-line);
  border-radius: 16px;
  background: #fff;
  color: var(--mp-text);
  font: inherit;
}

.field--textarea {
  min-height: 100%;
}

.field__control--textarea {
  min-height: 320px;
  resize: vertical;
  line-height: 1.6;
  font-family: ui-monospace, SFMono-Regular, Menlo, Monaco, Consolas, 'Liberation Mono', monospace;
}

.detail-grid,
.notes-grid {
  display: grid;
  grid-template-columns: repeat(2, minmax(0, 1fr));
  gap: 0.85rem;
}

.detail-card,
.note-card {
  padding: 1rem;
  border: 1px solid var(--mp-line);
  border-radius: 20px;
  background: linear-gradient(180deg, rgba(248, 246, 255, 0.82), #fff);
}

.detail-card span {
  color: var(--mp-muted);
  font-size: 0.88rem;
}

.detail-card strong {
  display: block;
  margin-top: 0.45rem;
  font-size: 1.05rem;
}

.note-card h4 {
  margin: 0 0 0.45rem;
}

.actions-bar {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 1rem;
  padding: 1rem 1.25rem;
}

@media (max-width: 960px) {
  .settings-grid,
  .detail-grid,
  .notes-grid {
    grid-template-columns: 1fr;
  }

  .hero-panel,
  .actions-bar {
    flex-direction: column;
    align-items: stretch;
  }
}
</style>
