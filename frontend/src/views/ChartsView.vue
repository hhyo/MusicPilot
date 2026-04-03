<template>
  <div class="charts-view">
    <section class="hero-panel">
      <div>
        <p class="hero-panel__eyebrow">Discovery</p>
        <h2>榜单发现与订阅入口</h2>
        <p class="hero-panel__description">
          当前榜单来自 local seed / mock chart source，只用于发现入口、榜单项下钻和创建订阅。
          还没有真实榜单抓取、增量对比或自动刷新。
        </p>
      </div>
      <el-tag type="warning" effect="plain">mock chart source / subscribe boundary</el-tag>
    </section>

    <el-alert
      title="Phase 4 只提供最小榜单入口：可查看 mock chart items 并创建订阅，但不会自动监控真实榜单变化。"
      type="warning"
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
        description="当前筛选条件下没有可展示的 mock 榜单。"
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
            <el-tag effect="plain">{{ chart.chart_type }}</el-tag>
          </div>

          <p class="chart-card__meta">
            {{ chart.category || 'discovery' }} · {{ chart.region || 'global' }}
          </p>
          <p class="chart-card__note">{{ chart.note }}</p>

          <div class="chart-card__footer">
            <span>{{ chart.item_count }} items</span>
            <el-button type="primary" plain @click="openChart(chart.id)">
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

      <div v-else class="entry-list">
        <article v-for="item in selectedChart.items" :key="item.item_id" class="entry-card">
          <div class="entry-card__rank">#{{ item.rank }}</div>
          <div class="entry-card__body">
            <h4>{{ item.target_name }}</h4>
            <p>{{ item.subtitle || '暂无补充说明' }}</p>
            <div class="entry-card__tags">
              <el-tag size="small" effect="plain">{{ item.item_type }}</el-tag>
              <el-tag size="small" effect="plain">{{ item.chart_source }}</el-tag>
              <el-tag size="small" effect="plain">{{ item.source_type }}</el-tag>
            </div>
          </div>
          <el-button
            type="primary"
            plain
            :loading="subscribingItemId === item.item_id"
            @click="handleSubscribe(item)"
          >
            创建订阅
          </el-button>
        </article>
      </div>
    </section>
  </div>
</template>

<script setup lang="ts">
import axios from 'axios';
import { computed, onMounted, ref } from 'vue';
import { ElMessage } from 'element-plus';

import {
  fetchChartDetail,
  fetchChartProviders,
  fetchCharts,
  subscribeFromChartEntry,
} from '@/services/orchestration';
import type {
  ChartDetailData,
  ChartEntryInfo,
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

const providerOptions = computed(() => [
  { value: 'all', label: '全部' },
  ...providers.value.map((item) => ({ value: item.chart_source, label: item.display_name })),
]);

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
      selectedChart.value = null;
    }
  } catch (error) {
    charts.value = [];
    selectedChart.value = null;
    chartsError.value = resolveErrorMessage(error, '榜单列表加载失败，请确认后端已启动。');
  } finally {
    loadingCharts.value = false;
  }
}

async function openChart(chartId: string) {
  loadingDetail.value = true;
  detailError.value = '';

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

async function handleSubscribe(item: ChartEntryInfo) {
  if (!selectedChart.value) {
    return;
  }

  subscribingItemId.value = item.item_id;
  try {
    const response = await subscribeFromChartEntry(selectedChart.value.chart.id, {
      chart_item_id: item.item_id,
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

function changeProvider(nextProvider: string) {
  providerFilter.value = nextProvider;
  void loadCharts();
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
.entry-list {
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
.chart-card__note {
  margin-top: 0.7rem;
}

.chart-card__footer {
  margin-top: 1rem;
  align-items: center;
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
  .entry-card {
    flex-direction: column;
  }

  .chart-grid {
    grid-template-columns: 1fr;
  }
}
</style>
