<template>
  <div class="charts-view">
    <section class="hero-panel">
      <div>
        <p class="hero-panel__eyebrow">Discovery</p>
        <h2>榜单发现与订阅入口</h2>
        <p class="hero-panel__description">
          当前榜单页用于发现入口、榜单项下钻和创建订阅。
          实际榜单来源与刷新能力取决于后端当前启用的 chart provider。
        </p>
      </div>
      <el-tag :type="hasLiveCharts ? 'success' : 'warning'" effect="plain">
        {{ hasLiveCharts ? 'live chart source / subscribe entry' : 'local chart source / subscribe entry' }}
      </el-tag>
    </section>

    <el-alert
      :title="
        hasLiveCharts
          ? '当前榜单页已接入真实 chart provider，可查看真实榜单项并创建订阅；自动刷新与增量监控仍待后续接入。'
          : '当前榜单页只提供本地发现入口：可查看 chart items 并创建订阅，但不会自动监控真实榜单变化。'
      "
      :type="hasLiveCharts ? 'info' : 'warning'"
      :closable="false"
      show-icon
    />

    <section class="filters-panel">
      <div class="filters-panel__group">
        <span>榜单源</span>
        <div class="pill-row">
          <button
            v-for="item in providerOptions"
            :key="item.value"
            type="button"
            class="pill-button"
            :class="{ 'pill-button--active': providerFilter === item.value }"
            @click="changeProvider(item.value)"
          >
            {{ item.label }}
          </button>
        </div>
      </div>
    </section>

    <el-alert
      v-if="createdSubscription"
      :title="`已创建订阅：${createdSubscription.target_name}（${createdSubscription.subscription_type}）`"
      type="success"
      :closable="false"
      show-icon
    />

    <section class="charts-panel">
      <header class="section-header">
        <div>
          <p class="section-header__eyebrow">Charts</p>
          <h3>榜单列表</h3>
        </div>
        <el-button text @click="loadCharts">刷新</el-button>
      </header>

      <el-alert
        v-if="chartsError"
        :title="chartsError"
        type="error"
        :closable="false"
        show-icon
      />

      <div v-else-if="loadingCharts" class="loading-grid">
        <el-skeleton v-for="index in 4" :key="index" animated :rows="4" />
      </div>

      <el-empty
        v-else-if="charts.length === 0"
        :description="hasLiveCharts ? '当前筛选条件下没有可展示的真实榜单。' : '当前筛选条件下没有可展示的本地榜单。'"
      />

      <div v-else class="chart-grid">
        <article
          v-for="chart in charts"
          :key="chart.id"
          class="chart-card"
          :class="{ 'chart-card--active': selectedChart?.chart.id === chart.id }"
        >
          <div class="chart-card__header">
            <div>
              <p class="chart-card__source">{{ chart.chart_source }}</p>
              <h4>{{ chart.chart_name }}</h4>
            </div>
            <el-tag effect="plain">{{ chart.chart_group || chart.chart_type }}</el-tag>
          </div>

          <p class="chart-card__meta">
            {{ chart.chart_scope || chart.category || 'discovery' }} · {{ chart.region || 'global' }}
          </p>
          <p class="chart-card__summary">{{ chart.summary || chart.note }}</p>
          <div class="chart-card__tags">
            <el-tag size="small" effect="plain">{{ chart.freshness_label || chart.refresh_hint || 'live' }}</el-tag>
            <el-tag size="small" effect="plain">{{ chart.item_count }} items</el-tag>
          </div>

          <div class="chart-card__footer">
            <span>{{ chart.note }}</span>
            <el-button type="primary" plain :data-test="`open-chart-${chart.id}`" @click="openChart(chart.id)">
              查看榜单项
            </el-button>
          </div>
        </article>
      </div>
    </section>

    <section class="chart-detail-panel">
      <header class="section-header">
        <div>
          <p class="section-header__eyebrow">Chart Detail</p>
          <h3>{{ selectedChart?.chart.chart_name || '榜单项详情' }}</h3>
        </div>
        <el-tag v-if="selectedChart" type="info" effect="plain">
          {{ selectedChart.integration_point }}
        </el-tag>
      </header>

      <el-alert
        v-if="detailError"
        :title="detailError"
        type="error"
        :closable="false"
        show-icon
      />

      <div v-else-if="loadingDetail" class="loading-grid">
        <el-skeleton v-for="index in 3" :key="index" animated :rows="4" />
      </div>

      <el-empty
        v-else-if="!selectedChart"
        description="选择一个榜单后，这里会展示榜单项并支持从单项创建订阅。"
      />

      <div v-else class="detail-stack">
        <el-alert
          v-if="discoveryWarningMessage"
          :title="discoveryWarningMessage"
          type="warning"
          :closable="false"
          show-icon
        />

        <section
          v-if="selectedChart.hero_entry"
          class="hero-entry-card"
          :class="{ 'hero-entry-card--active': activeDiscoveryEntryId === selectedChart.hero_entry.entry.item_id }"
          data-test="discovery-hero-entry"
          role="button"
          tabindex="0"
          @click="void openDiscoveryEntryDetail(selectedChart.hero_entry)"
          @keydown.enter.prevent="void openDiscoveryEntryDetail(selectedChart.hero_entry)"
          @keydown.space.prevent="void openDiscoveryEntryDetail(selectedChart.hero_entry)"
        >
          <div>
            <p class="hero-entry-card__eyebrow">Featured Entry</p>
            <h4>{{ renderEntryTitle(selectedChart.hero_entry) }}</h4>
            <p>{{ selectedChart.hero_entry.entry_summary }}</p>
            <p class="hero-entry-card__conversion">
              {{ renderRecognitionStatus(selectedChart.hero_entry) }}
            </p>
          </div>
          <div class="entry-card__tags">
            <el-tag
              v-for="badge in selectedChart.hero_entry.badges"
              :key="badge"
              size="small"
              effect="plain"
            >
              {{ badge }}
            </el-tag>
          </div>
        </section>

        <section class="detail-summary-grid">
          <article class="detail-summary-card">
            <p class="detail-summary-card__label">Entries</p>
            <h4>{{ selectedChart.summary_stats.items ?? selectedChart.item_count }}</h4>
          </article>
          <article class="detail-summary-card">
            <p class="detail-summary-card__label">Metadata Ready</p>
            <h4>{{ selectedChart.recognition_summary.ready ?? 0 }}</h4>
          </article>
          <article class="detail-summary-card">
            <p class="detail-summary-card__label">Needs Follow-up</p>
            <h4>{{ selectedChart.recognition_summary.not_ready ?? 0 }}</h4>
          </article>
        </section>

        <section
          v-for="group in displayEntryGroups"
          :key="group.group_key"
          class="entry-group"
        >
          <header class="entry-group__header">
            <div>
              <p class="section-header__eyebrow">Entry Group</p>
              <h4>{{ group.group_label }}</h4>
            </div>
            <el-tag effect="plain">{{ group.items.length }} items</el-tag>
          </header>

          <div class="entry-list">
            <article
              v-for="item in group.items"
              :key="item.entry.item_id"
              class="entry-card"
              :class="{ 'entry-card--active': activeDiscoveryEntryId === item.entry.item_id }"
              :data-test="`discovery-entry-${item.entry.item_id}`"
              role="button"
              tabindex="0"
              @click="void openDiscoveryEntryDetail(item)"
              @keydown.enter.prevent="void openDiscoveryEntryDetail(item)"
              @keydown.space.prevent="void openDiscoveryEntryDetail(item)"
            >
              <div class="entry-card__rank">#{{ item.entry.rank }}</div>
              <div class="entry-card__body">
                <h4>{{ renderEntryTitle(item) }}</h4>
                <p>{{ item.entry_summary }}</p>
                <p class="entry-card__conversion">
                  {{ renderRecognitionStatus(item) }}
                </p>
                <div class="entry-card__tags">
                  <el-tag size="small" effect="plain">{{ item.media_input.entity_hint || item.entry.item_type }}</el-tag>
                  <el-tag size="small" effect="plain">{{ renderEntryProvider(item) }}</el-tag>
                  <el-tag
                    v-for="badge in item.badges"
                    :key="badge"
                    size="small"
                    effect="plain"
                  >
                    {{ badge }}
                  </el-tag>
                </div>
              </div>
              <el-button
                type="primary"
                plain
                :disabled="!isEntrySubscribable(item)"
                :loading="subscribingItemId === item.entry.item_id"
                :data-test="`subscribe-entry-${item.entry.item_id}`"
                @click.stop="handleSubscribe(item)"
              >
                创建订阅
              </el-button>
            </article>
          </div>
        </section>
      </div>
    </section>

    <MetadataDetailDrawer
      :model-value="metadataDrawerOpen"
      :loading="metadataDetailLoading"
      :detail="metadataDetail"
      :error-message="metadataDetailError"
      @update:model-value="handleMetadataDrawerVisibility"
      @create-subscription="createSubscriptionFromDetail"
      @search-resources="createAndRunSearchJobFromDetail"
    />
  </div>
</template>

<script setup lang="ts">
import axios from 'axios';
import { computed, onMounted, ref } from 'vue';
import { ElMessage } from 'element-plus';

import MetadataDetailDrawer from '@/components/MetadataDetailDrawer.vue';
import { createSearchJob, executeSearchJob } from '@/services/acquisition';
import { buildMusicMediaInputFromMetadataDetail, resolveMusicMediaDetail } from '@/services/music-media';
import {
  createSubscription,
  fetchChartDetail,
  fetchChartProviders,
  fetchCharts,
  subscribeFromChartEntry,
} from '@/services/orchestration';
import type { MetadataDetail } from '@/types/metadata';
import type {
  ChartDetailData,
  ChartEntryInfo,
  DiscoveryEntryView,
  DiscoveryEntryGroup,
  ChartProviderInfo,
  ChartInfo,
  SubscriptionSummary,
} from '@/types/orchestration';

const loadingCharts = ref(false);
const loadingDetail = ref(false);
const chartsError = ref('');
const detailError = ref('');
const providers = ref<ChartProviderInfo[]>([]);
const charts = ref<ChartInfo[]>([]);
const selectedChart = ref<ChartDetailData | null>(null);
const providerFilter = ref('all');
const subscribingItemId = ref('');
const createdSubscription = ref<SubscriptionSummary | null>(null);
const metadataDrawerOpen = ref(false);
const metadataDetailLoading = ref(false);
const metadataDetailError = ref('');
const metadataDetail = ref<MetadataDetail | null>(null);
const activeDiscoveryEntryId = ref('');
const discoveryWarningMessage = ref('');

const providerOptions = computed(() => [
  { value: 'all', label: '全部' },
  ...providers.value.map((item) => ({ value: item.chart_source, label: item.display_name })),
]);

const hasLiveCharts = computed(() => providers.value.some((item) => !item.mock));
const displayEntryGroups = computed<DiscoveryEntryGroup[]>(() => selectedChart.value?.entry_groups ?? []);

onMounted(() => {
  void loadProviders();
  void loadCharts();
});

async function loadProviders() {
  try {
    const response = await fetchChartProviders();
    if (!response.success) {
      throw new Error(response.message);
    }
    providers.value = response.data;
  } catch (error) {
    chartsError.value = resolveErrorMessage(error, '榜单源加载失败。');
  }
}

async function loadCharts() {
  loadingCharts.value = true;
  chartsError.value = '';

  try {
    const response = await fetchCharts({
      provider: providerFilter.value === 'all' ? undefined : providerFilter.value,
    });

    if (!response.success) {
      throw new Error(response.message);
    }

    charts.value = response.data.items;

    if (response.data.items.length > 0) {
      const nextChartId = selectedChart.value?.chart.id ?? response.data.items[0].id;
      await openChart(nextChartId);
    } else {
      resetDiscoveryDetailState();
      selectedChart.value = null;
    }
  } catch (error) {
    charts.value = [];
    resetDiscoveryDetailState();
    selectedChart.value = null;
    chartsError.value = resolveErrorMessage(error, '榜单列表加载失败，请确认后端已启动。');
  } finally {
    loadingCharts.value = false;
  }
}

async function openChart(chartId: string) {
  loadingDetail.value = true;
  detailError.value = '';
  resetDiscoveryDetailState();

  try {
    const response = await fetchChartDetail(chartId);
    if (!response.success) {
      throw new Error(response.message);
    }
    selectedChart.value = response.data;
  } catch (error) {
    detailError.value = resolveErrorMessage(error, '榜单详情加载失败。');
  } finally {
    loadingDetail.value = false;
  }
}

async function openDiscoveryEntryDetail(item: DiscoveryEntryView) {
  activeDiscoveryEntryId.value = item.entry.item_id;
  discoveryWarningMessage.value = '';

  if (!isEntryResolvable(item)) {
    metadataDrawerOpen.value = false;
    metadataDetail.value = null;
    metadataDetailError.value = '';
    metadataDetailLoading.value = false;
    discoveryWarningMessage.value = resolveRecognitionStatusText(item);
    ElMessage.warning(discoveryWarningMessage.value);
    return;
  }

  metadataDrawerOpen.value = true;
  metadataDetailLoading.value = true;
  metadataDetailError.value = '';
  metadataDetail.value = null;

  try {
    const response = await resolveMusicMediaDetail(item.media_input);
    if (!response.success) {
      throw new Error(response.message);
    }
    metadataDetail.value = response.data.detail;
  } catch (error) {
    metadataDetailError.value = resolveErrorMessage(error, 'metadata detail 加载失败。');
  } finally {
    metadataDetailLoading.value = false;
  }
}

async function handleSubscribe(item: DiscoveryEntryView) {
  if (!selectedChart.value) {
    return;
  }
  if (!isEntrySubscribable(item)) {
    const message = resolveRecognitionStatusText(item);
    ElMessage.warning(message);
    return;
  }

  subscribingItemId.value = item.entry.item_id;
  try {
    const response = await subscribeFromChartEntry(selectedChart.value.chart.id, {
      chart_item_id: item.entry.item_id,
      mode: 'manual',
    });

    if (!response.success) {
      throw new Error(response.message);
    }

    createdSubscription.value = response.data;
    ElMessage.success(`已创建 ${response.data.target_name} 的 chart_entry 订阅。`);
  } catch (error) {
    ElMessage.error(resolveErrorMessage(error, '从榜单项创建订阅失败。'));
  } finally {
    subscribingItemId.value = '';
  }
}

async function createSubscriptionFromDetail(detail: MetadataDetail) {
  try {
    const response = await createSubscription({
      subscription_type: detail.entity_type,
      target_id: detail.id,
      target_name: detail.title,
      target_entity_type: detail.entity_type,
      mode: 'manual',
    });

    if (!response.success) {
      throw new Error(response.message);
    }

    createdSubscription.value = response.data;
    ElMessage.success(`已创建 ${response.data.target_name} 的订阅。`);
  } catch (error) {
    ElMessage.error(resolveErrorMessage(error, '创建订阅失败。'));
  }
}

async function createAndRunSearchJobFromDetail(detail: MetadataDetail) {
  try {
    const mediaInput = buildMusicMediaInputFromMetadataDetail(detail, 'discovery', {
      trigger: 'charts_view_detail',
      chart_id: selectedChart.value?.chart.id ?? null,
    });
    const created = await createSearchJob({
      input: mediaInput,
      trigger_source: 'manual',
      mode: 'manual',
    });

    if (!created.success) {
      throw new Error(created.message);
    }

    const executed = await executeSearchJob(created.data.id);
    if (!executed.success) {
      throw new Error(executed.message);
    }

    ElMessage.success(`已创建并执行 ${detail.title} 的搜索任务。`);
  } catch (error) {
    ElMessage.error(resolveErrorMessage(error, '创建搜索任务失败。'));
  }
}

function changeProvider(nextProvider: string) {
  providerFilter.value = nextProvider;
  void loadCharts();
}

function handleMetadataDrawerVisibility(nextValue: boolean) {
  metadataDrawerOpen.value = nextValue;
  if (!nextValue) {
    activeDiscoveryEntryId.value = '';
  }
}

function resetDiscoveryDetailState() {
  metadataDrawerOpen.value = false;
  metadataDetailLoading.value = false;
  metadataDetailError.value = '';
  metadataDetail.value = null;
  activeDiscoveryEntryId.value = '';
  discoveryWarningMessage.value = '';
}

function resolveErrorMessage(error: unknown, fallback: string) {
  if (axios.isAxiosError(error)) {
    return error.response?.data?.message ?? fallback;
  }
  if (error instanceof Error) {
    return error.message;
  }
  return fallback;
}

function renderRecognitionStatus(item: DiscoveryEntryView) {
  return resolveRecognitionStatusText(item);
}

function renderEntryTitle(item: DiscoveryEntryView) {
  return item.entry.target_name;
}

function renderEntryProvider(item: DiscoveryEntryView) {
  const provider = item.media_input.source_context.provider;
  return typeof provider === 'string' && provider ? provider : item.entry.provider;
}

function isEntryResolvable(item: DiscoveryEntryView) {
  return (
    item.recognition_assessment.state === 'direct' || item.recognition_assessment.state === 'ready'
  );
}

function isEntrySubscribable(item: DiscoveryEntryView) {
  return isEntryResolvable(item);
}

function resolveRecognitionStatusText(item: DiscoveryEntryView) {
  if (item.recognition_assessment.state === 'direct') {
    return '已可直接查看详情';
  }
  if (item.recognition_assessment.state === 'ready') {
    return '可进入统一媒体解析';
  }
  if (item.recognition_assessment.state === 'partial') {
    return item.recognition_assessment.note || '解析信息部分可用';
  }
  if (item.recognition_assessment.state === 'insufficient') {
    return '解析信息不足';
  }
  return item.recognition_assessment.note || '当前暂不支持详情下钻';
}
</script>

<style scoped lang="scss">
.charts-view {
  display: grid;
  gap: 1.2rem;
}

.hero-panel,
.filters-panel,
.charts-panel,
.chart-detail-panel {
  padding: 1.4rem;
  border: 1px solid var(--mp-line);
  border-radius: 28px;
  background: rgba(255, 255, 255, 0.82);
  box-shadow: 0 18px 40px rgba(52, 37, 122, 0.06);
}

.hero-panel,
.section-header,
.chart-card__header,
.chart-card__footer,
.entry-card {
  display: flex;
  align-items: flex-start;
  justify-content: space-between;
  gap: 1rem;
}

.hero-panel__eyebrow,
.section-header__eyebrow,
.chart-card__source {
  margin: 0;
  color: var(--mp-accent);
  font-size: 0.82rem;
  font-weight: 700;
  letter-spacing: 0.08em;
  text-transform: uppercase;
}

.hero-panel h2,
.section-header h3,
.chart-card h4,
.entry-card h4,
.hero-panel__description,
.chart-card__meta,
.chart-card__note,
.entry-card p {
  margin: 0;
}

.hero-panel__description,
.chart-card__meta,
.chart-card__note,
.entry-card p {
  color: var(--mp-muted);
  line-height: 1.7;
}

.filters-panel__group {
  display: grid;
  gap: 0.75rem;
}

.filters-panel__group span {
  font-weight: 700;
}

.pill-row {
  display: flex;
  gap: 0.65rem;
  flex-wrap: wrap;
}

.pill-button {
  padding: 0.6rem 0.95rem;
  border: 1px solid var(--mp-line);
  border-radius: 999px;
  background: rgba(255, 255, 255, 0.92);
  color: var(--mp-text);
  cursor: pointer;
}

.pill-button--active {
  border-color: transparent;
  background: var(--mp-accent);
  color: #fff;
}

.chart-grid,
.loading-grid,
.entry-list,
.detail-stack,
.detail-summary-grid {
  display: grid;
  gap: 1rem;
}

.chart-grid {
  grid-template-columns: repeat(2, minmax(0, 1fr));
}

.chart-card,
.entry-card {
  padding: 1rem;
  border: 1px solid var(--mp-line);
  border-radius: 22px;
  background: rgba(255, 255, 255, 0.92);
}

.chart-card--active {
  border-color: rgba(126, 94, 248, 0.4);
  box-shadow: 0 12px 30px rgba(126, 94, 248, 0.12);
}

.chart-card__meta,
.chart-card__summary {
  margin-top: 0.7rem;
}

.chart-card__footer {
  margin-top: 1rem;
  align-items: center;
}

.hero-entry-card,
.detail-summary-card {
  padding: 1rem;
  border: 1px solid var(--mp-line);
  border-radius: 22px;
  background: rgba(255, 255, 255, 0.92);
}

.hero-entry-card {
  display: flex;
  justify-content: space-between;
  gap: 1rem;
  cursor: pointer;
}

.hero-entry-card--active,
.entry-card--active {
  border-color: rgba(126, 94, 248, 0.4);
  box-shadow: 0 12px 30px rgba(126, 94, 248, 0.12);
}

.hero-entry-card__eyebrow,
.detail-summary-card__label {
  margin: 0;
  color: var(--mp-accent);
  font-size: 0.78rem;
  font-weight: 700;
  letter-spacing: 0.08em;
  text-transform: uppercase;
}

.hero-entry-card h4,
.detail-summary-card h4 {
  margin: 0.25rem 0 0;
}

.detail-summary-grid {
  grid-template-columns: repeat(3, minmax(0, 1fr));
}

.entry-group {
  display: grid;
  gap: 0.8rem;
}

.entry-group__header {
  display: flex;
  justify-content: space-between;
  gap: 1rem;
}

.entry-card {
  align-items: center;
}

.entry-card__rank {
  display: inline-flex;
  align-items: center;
  justify-content: center;
  min-width: 3rem;
  min-height: 3rem;
  border-radius: 18px;
  background: rgba(126, 94, 248, 0.12);
  font-weight: 800;
  color: var(--mp-accent);
}

.entry-card__body {
  flex: 1;
  display: grid;
  gap: 0.4rem;
}

.entry-card__conversion {
  font-size: 0.92rem;
}

.entry-card__tags {
  display: flex;
  gap: 0.45rem;
  flex-wrap: wrap;
}

@media (max-width: 920px) {
  .hero-panel,
  .section-header,
  .chart-card__header,
  .chart-card__footer,
  .entry-card,
  .hero-entry-card,
  .entry-group__header {
    flex-direction: column;
  }

  .chart-grid {
    grid-template-columns: 1fr;
  }

  .detail-summary-grid {
    grid-template-columns: 1fr;
  }
}
</style>
