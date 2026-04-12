<template>
  <div class="page-shell">
    <VCard class="hero-card">
      <VCardText class="pa-6 stack">
        <div class="charts-view__hero">
          <div>
            <p class="eyebrow">Discovery</p>
            <h2 class="section-title">榜单发现与媒体识别</h2>
            <p class="section-note">
              页面直接展示榜单条目的 `music_media_input / music_meta_base / recognition_assessment`，
              不再使用旧的 discovery target 转换语义。
            </p>
          </div>
          <VChip color="primary" variant="tonal">{{ providerFilter || 'all providers' }}</VChip>
        </div>

        <div class="charts-view__filters">
          <VChipGroup v-model="providerFilter" mandatory>
            <VChip
              v-for="option in providerOptions"
              :key="option.value"
              :value="option.value"
              filter
              variant="outlined"
            >
              {{ option.label }}
            </VChip>
          </VChipGroup>
          <VBtn variant="tonal" color="secondary" @click="loadCharts">刷新榜单</VBtn>
        </div>
      </VCardText>
    </VCard>

    <VAlert
      v-if="chartsError"
      type="error"
      variant="tonal"
      density="comfortable"
      :text="chartsError"
    />

    <div class="split-layout">
      <VCard class="panel-card">
        <VCardText class="pa-6 stack">
          <div class="charts-view__section-head">
            <div>
              <p class="eyebrow">Charts</p>
              <h3 class="section-title">榜单列表</h3>
            </div>
            <VChip variant="tonal" color="secondary">{{ charts.length }} charts</VChip>
          </div>

          <template v-if="loadingCharts">
            <VSkeletonLoader type="article, article, article" />
          </template>

          <template v-else-if="charts.length === 0">
            <VAlert
              type="info"
              variant="tonal"
              density="comfortable"
              text="当前筛选条件下没有可展示的榜单。"
            />
          </template>

          <div v-else class="stack">
            <VCard
              v-for="chart in charts"
              :key="chart.id"
              class="charts-view__chart-card"
              :class="{ 'charts-view__chart-card--active': selectedChart?.chart.id === chart.id }"
              rounded="xl"
              elevation="0"
              @click="openChart(chart.id)"
            >
              <VCardText class="stack">
                <div class="charts-view__section-head">
                  <div>
                    <p class="eyebrow">{{ chart.chart_source }}</p>
                    <h4 class="charts-view__chart-title">{{ chart.chart_name }}</h4>
                  </div>
                  <VChip variant="outlined">{{ chart.chart_group || chart.chart_type }}</VChip>
                </div>
                <p class="section-note">{{ chart.summary || chart.note }}</p>
                <div class="charts-view__chips">
                  <VChip variant="outlined">{{ chart.region || 'global' }}</VChip>
                  <VChip variant="outlined">{{ chart.item_count }} items</VChip>
                  <VChip variant="outlined">{{ chart.freshness_label || 'live' }}</VChip>
                </div>
              </VCardText>
            </VCard>
          </div>
        </VCardText>
      </VCard>

      <VCard class="panel-card">
        <VCardText class="pa-6 stack">
          <div class="charts-view__section-head">
            <div>
              <p class="eyebrow">Chart Detail</p>
              <h3 class="section-title">{{ selectedChart?.chart.chart_name || '选择一个榜单' }}</h3>
            </div>
            <VChip v-if="selectedChart" variant="tonal" color="primary">
              {{ selectedChart.integration_point }}
            </VChip>
          </div>

          <VAlert
            v-if="detailError"
            type="error"
            variant="tonal"
            density="comfortable"
            :text="detailError"
          />

          <template v-else-if="loadingDetail">
            <VSkeletonLoader type="article, article, article" />
          </template>

          <template v-else-if="!selectedChart">
            <VAlert
              type="info"
              variant="tonal"
              density="comfortable"
              text="选择榜单后，这里会显示榜单条目的识别状态和订阅入口。"
            />
          </template>

          <template v-else>
            <div class="meta-pairs">
              <div class="meta-pair">
                <span class="meta-pair__label">Items</span>
                <span class="meta-pair__value">{{ selectedChart.summary_stats.items ?? selectedChart.item_count }}</span>
              </div>
              <div class="meta-pair">
                <span class="meta-pair__label">Ready</span>
                <span class="meta-pair__value">{{ selectedChart.recognition_summary.ready ?? 0 }}</span>
              </div>
              <div class="meta-pair">
                <span class="meta-pair__label">Partial</span>
                <span class="meta-pair__value">{{ selectedChart.recognition_summary.partial ?? 0 }}</span>
              </div>
              <div class="meta-pair">
                <span class="meta-pair__label">Insufficient</span>
                <span class="meta-pair__value">{{ selectedChart.recognition_summary.insufficient ?? 0 }}</span>
              </div>
            </div>

            <VCard
              v-if="selectedChart.hero_entry"
              class="charts-view__hero-entry"
              rounded="xl"
              elevation="0"
              @click="openDiscoveryEntryDetail(selectedChart.hero_entry)"
            >
              <VCardText class="stack">
                <p class="eyebrow">Featured Entry</p>
                <h4 class="charts-view__chart-title">{{ selectedChart.hero_entry.entry.target_name }}</h4>
                <p class="section-note">{{ selectedChart.hero_entry.entry_summary }}</p>
                <div class="charts-view__chips">
                  <VChip color="primary" variant="tonal">
                    {{ selectedChart.hero_entry.recognition_assessment.state }}
                  </VChip>
                  <VChip
                    v-for="badge in selectedChart.hero_entry.badges"
                    :key="badge"
                    variant="outlined"
                  >
                    {{ badge }}
                  </VChip>
                </div>
              </VCardText>
            </VCard>

            <div class="stack">
              <VCard
                v-for="group in selectedChart.entry_groups"
                :key="group.group_key"
                class="charts-view__group-card"
                rounded="xl"
                elevation="0"
              >
                <VCardText class="stack">
                  <div class="charts-view__section-head">
                    <div>
                      <p class="eyebrow">Entry Group</p>
                      <h4 class="charts-view__chart-title">{{ group.group_label }}</h4>
                    </div>
                    <VChip variant="outlined">{{ group.items.length }} items</VChip>
                  </div>

                  <VCard
                    v-for="item in group.items"
                    :key="item.entry.item_id"
                    class="charts-view__entry-card"
                    rounded="xl"
                    elevation="0"
                    @click="openDiscoveryEntryDetail(item)"
                  >
                    <VCardText class="stack">
                      <div class="charts-view__section-head">
                        <div>
                          <p class="eyebrow">#{{ item.entry.rank }}</p>
                          <h5 class="charts-view__entry-title">{{ item.entry.target_name }}</h5>
                        </div>
                        <VChip color="primary" variant="tonal">
                          {{ item.recognition_assessment.state }}
                        </VChip>
                      </div>

                      <p class="section-note">{{ item.entry_summary }}</p>
                      <div class="charts-view__chips">
                        <VChip variant="outlined">{{ item.entry.item_type }}</VChip>
                        <VChip
                          v-for="badge in item.badges"
                          :key="badge"
                          variant="outlined"
                        >
                          {{ badge }}
                        </VChip>
                      </div>

                      <div class="charts-view__actions">
                        <VBtn color="primary" variant="flat" @click.stop="openDiscoveryEntryDetail(item)">
                          打开详情
                        </VBtn>
                        <VBtn
                          color="secondary"
                          variant="tonal"
                          :loading="subscribingItemId === item.entry.item_id"
                          @click.stop="handleSubscribe(item)"
                        >
                          创建订阅
                        </VBtn>
                      </div>
                    </VCardText>
                  </VCard>
                </VCardText>
              </VCard>
            </div>
          </template>
        </VCardText>
      </VCard>
    </div>

    <MetadataDetailDrawer
      :model-value="metadataDrawerOpen"
      :loading="metadataDetailLoading"
      :detail="metadataDetail"
      :error-message="metadataDetailError"
      :meta-base="activeMetaBase"
      :assessment="activeAssessment"
      :media-info="activeMediaInfo"
      @update:model-value="metadataDrawerOpen = $event"
      @create-subscription="createSubscriptionFromDetail"
      @search-resources="createSearchJobFromDetail"
    />
  </div>
</template>

<script setup lang="ts">
import { computed, onMounted, ref } from 'vue';

import MetadataDetailDrawer from '@/components/MetadataDetailDrawer.vue';
import { createSearchJob } from '@/services/acquisition';
import { fetchChartDetail, fetchChartProviders, fetchCharts, subscribeFromChartEntry } from '@/services/discovery';
import { resolveMusicMediaDetail } from '@/services/music-media';
import {
  buildChartEntryResolveInput,
  buildSearchJobPayload,
  buildSubscriptionPayloadFromMetadataDetail,
} from '@/services/music-media-mappers';
import { createSubscription } from '@/services/subscriptions';
import type { MetadataDetail } from '@/types/metadata';
import type { MusicMediaInfo, MusicMetaBase, MusicRecognitionAssessment } from '@/types/music-media';
import type { ChartDetailData, ChartInfo, DiscoveryEntryView } from '@/types/orchestration';

const loadingCharts = ref(false);
const chartsError = ref('');
const charts = ref<ChartInfo[]>([]);
const providerFilter = ref('all');
const providerOptions = ref<Array<{ value: string; label: string }>>([{ value: 'all', label: '全部' }]);

const loadingDetail = ref(false);
const detailError = ref('');
const selectedChart = ref<ChartDetailData | null>(null);
const subscribingItemId = ref('');

const metadataDrawerOpen = ref(false);
const metadataDetailLoading = ref(false);
const metadataDetailError = ref('');
const metadataDetail = ref<MetadataDetail | null>(null);
const activeMetaBase = ref<MusicMetaBase | null>(null);
const activeMediaInfo = ref<MusicMediaInfo | null>(null);
const activeAssessment = ref<MusicRecognitionAssessment | null>(null);

onMounted(() => {
  void initialize();
});

async function initialize() {
  await Promise.all([loadProviders(), loadCharts()]);
}

async function loadProviders() {
  try {
    const response = await fetchChartProviders();
    providerOptions.value = [
      { value: 'all', label: '全部' },
      ...response.data.map((item) => ({ value: item.id, label: item.display_name })),
    ];
  } catch {
    providerOptions.value = [{ value: 'all', label: '全部' }];
  }
}

async function loadCharts() {
  loadingCharts.value = true;
  chartsError.value = '';
  try {
    const response = await fetchCharts(providerFilter.value === 'all' ? undefined : { provider: providerFilter.value });
    charts.value = response.data.items;
    if (charts.value.length > 0 && !selectedChart.value) {
      await openChart(charts.value[0].id);
    }
  } catch (error) {
    chartsError.value = error instanceof Error ? error.message : '榜单加载失败。';
  } finally {
    loadingCharts.value = false;
  }
}

async function openChart(chartId: string) {
  loadingDetail.value = true;
  detailError.value = '';
  try {
    const response = await fetchChartDetail(chartId);
    selectedChart.value = response.data;
  } catch (error) {
    detailError.value = error instanceof Error ? error.message : '榜单详情加载失败。';
  } finally {
    loadingDetail.value = false;
  }
}

async function openDiscoveryEntryDetail(entry: DiscoveryEntryView) {
  metadataDrawerOpen.value = true;
  metadataDetailLoading.value = true;
  metadataDetailError.value = '';
  activeMetaBase.value = entry.meta_base;
  activeAssessment.value = entry.recognition_assessment;
  activeMediaInfo.value = null;
  try {
    const response = await resolveMusicMediaDetail(buildChartEntryResolveInput(entry));
    metadataDetail.value = response.data.detail;
    activeMetaBase.value = response.data.base;
    activeAssessment.value = response.data.assessment;
    activeMediaInfo.value = response.data.media;
  } catch (error) {
    metadataDetail.value = null;
    metadataDetailError.value = error instanceof Error ? error.message : '媒体详情解析失败。';
  } finally {
    metadataDetailLoading.value = false;
  }
}

async function handleSubscribe(entry: DiscoveryEntryView) {
  subscribingItemId.value = entry.entry.item_id;
  try {
    await subscribeFromChartEntry(entry.entry.chart_id, {
      chart_item_id: entry.entry.item_id,
      mode: 'manual',
    });
  } finally {
    subscribingItemId.value = '';
  }
}

async function createSubscriptionFromDetail(detail: MetadataDetail) {
  await createSubscription(buildSubscriptionPayloadFromMetadataDetail(detail));
}

async function createSearchJobFromDetail(detail: MetadataDetail) {
  const response = await createSearchJob(
    buildSearchJobPayload({
      entity_hint: detail.entity_type,
      source_kind: 'metadata_detail',
      title: detail.title,
      subtitle: detail.note,
      artist_names: detail.artist_name ? [detail.artist_name] : [],
      album_title: detail.album_title || null,
      album_artist_names: detail.artist_name ? [detail.artist_name] : [],
      release_date: null,
      year: detail.year ?? null,
      track_number: null,
      disc_number: null,
      external_refs: detail.external_ids || {},
      source_context: {
        provider: detail.provider,
        source_type: detail.source_type,
        metadata_id: detail.id,
      },
      raw_context: {
        metadata_detail: detail,
      },
    }),
  );
  metadataDetailError.value = `已创建搜索任务 ${response.data.id}`;
}
</script>

<style scoped lang="scss">
.charts-view__hero,
.charts-view__filters,
.charts-view__section-head,
.charts-view__actions {
  display: flex;
  align-items: flex-start;
  justify-content: space-between;
  gap: 0.75rem;
}

.charts-view__filters,
.charts-view__chips,
.charts-view__actions {
  flex-wrap: wrap;
}

.charts-view__chart-card,
.charts-view__hero-entry,
.charts-view__group-card,
.charts-view__entry-card {
  border: 1px solid var(--mp-line);
  background: var(--mp-panel-soft);
}

.charts-view__chart-card--active {
  border-color: var(--mp-line-strong);
}

.charts-view__chart-title,
.charts-view__entry-title {
  margin: 0.25rem 0 0;
}

.charts-view__entry-title {
  font-size: 1rem;
}
</style>
