<template>
  <div class="page-shell">
    <VCard class="hero-card">
      <VCardText class="pa-6">
        <div class="home-view__hero">
          <div>
            <p class="eyebrow">MusicPilot Home</p>
            <h2 class="section-title">统一音乐工作台</h2>
            <p class="section-note">
              当前前端基线围绕统一音乐媒体解析链、榜单发现、订阅执行与获取链路重建，
              不再使用旧的过渡态页面语义。
            </p>
          </div>
          <div class="home-view__hero-actions">
            <VBtn color="primary" to="/charts">打开 Discovery</VBtn>
            <VBtn variant="tonal" color="secondary" to="/search">打开 Metadata</VBtn>
          </div>
        </div>
      </VCardText>
    </VCard>

    <VAlert
      v-if="loadError"
      type="warning"
      variant="tonal"
      density="comfortable"
      :text="loadError"
    />

    <div class="stats-grid">
      <VCard
        v-for="item in dashboardStats"
        :key="item.label"
        class="metric-card"
      >
        <VCardText class="pa-5">
          <p class="eyebrow">{{ item.label }}</p>
          <h3 class="home-view__metric-value">{{ item.value }}</h3>
          <p class="section-note">{{ item.note }}</p>
        </VCardText>
      </VCard>
    </div>

    <div class="surface-grid home-view__modules">
      <VCard class="panel-card">
        <VCardText class="pa-6 stack">
          <div>
            <p class="eyebrow">Primary Modules</p>
            <h3 class="section-title">主要工作入口</h3>
          </div>
          <div class="surface-grid home-view__module-grid">
            <ModuleEntryCard
              v-for="module in featureModules"
              :key="module.key"
              :module="module"
            />
          </div>
        </VCardText>
      </VCard>

      <VCard class="panel-card">
        <VCardText class="pa-6 stack">
          <div>
            <p class="eyebrow">Runtime Notes</p>
            <h3 class="section-title">当前运行状态</h3>
          </div>
          <div class="soft-block">
            <p class="section-note">
              Health: {{ healthSummary }}
            </p>
          </div>
          <div class="soft-block">
            <p class="section-note">
              Dashboard summary:
              {{ dashboardSummaryText }}
            </p>
          </div>
        </VCardText>
      </VCard>
    </div>
  </div>
</template>

<script setup lang="ts">
import { computed, onMounted, ref } from 'vue';

import ModuleEntryCard from '@/components/ModuleEntryCard.vue';
import { fetchChartProviders } from '@/services/discovery';
import { fetchProviderSettings } from '@/services/settings';
import { fetchSubscriptions } from '@/services/subscriptions';
import { fetchDashboardSummary, fetchHealth } from '@/services/runtime';
import { navigationModules } from '@/types/module';

const healthSummary = ref('加载中');
const dashboardSummaryText = ref('加载中');
const subscriptionCount = ref<number | null>(null);
const chartProviderCount = ref<number | null>(null);
const rssFeedCount = ref<number | null>(null);
const providerMode = ref<string | null>(null);
const loadError = ref('');

const featureModules = computed(() => navigationModules.filter((item) => item.key !== 'home'));

const dashboardStats = computed(() => [
  {
    label: 'Subscriptions',
    value: subscriptionCount.value == null ? '--' : String(subscriptionCount.value),
    note: '当前已落库的订阅数量。',
  },
  {
    label: 'Chart Providers',
    value: chartProviderCount.value == null ? '--' : String(chartProviderCount.value),
    note: '当前后端可见的榜单 provider。',
  },
  {
    label: 'RSS Feeds',
    value: rssFeedCount.value == null ? '--' : String(rssFeedCount.value),
    note: 'settings 中的结构化 RSS feed 数量。',
  },
  {
    label: 'Provider Mode',
    value: providerMode.value || '--',
    note: '当前运行时 discovery 主模式。',
  },
]);

onMounted(() => {
  void loadDashboard();
});

async function loadDashboard() {
  loadError.value = '';
  try {
    const [health, dashboard, subscriptions, providers, settings] = await Promise.all([
      fetchHealth(),
      fetchDashboardSummary(),
      fetchSubscriptions(),
      fetchChartProviders(),
      fetchProviderSettings(),
    ]);

    healthSummary.value = `${health.data.status} · ${health.data.version}`;
    dashboardSummaryText.value = dashboard.note || dashboard.message;
    subscriptionCount.value = subscriptions.data.total;
    chartProviderCount.value = providers.data.length;
    rssFeedCount.value = settings.data.chart_rss_feeds.length;
    providerMode.value = settings.data.chart_provider_mode;
  } catch (error) {
    loadError.value = error instanceof Error ? error.message : '首页摘要加载失败。';
  }
}
</script>

<style scoped lang="scss">
.home-view__hero,
.home-view__hero-actions {
  display: flex;
  align-items: flex-start;
  justify-content: space-between;
  gap: 1rem;
}

.home-view__hero-actions {
  flex-wrap: wrap;
}

.home-view__metric-value {
  margin: 0.4rem 0 0;
  font-size: 1.8rem;
}

.home-view__modules {
  grid-template-columns: minmax(0, 1.4fr) minmax(280px, 0.8fr);
}

.home-view__module-grid {
  grid-template-columns: repeat(auto-fit, minmax(220px, 1fr));
}

@media (max-width: 1100px) {
  .home-view__modules {
    grid-template-columns: 1fr;
  }
}

@media (max-width: 720px) {
  .home-view__hero {
    flex-direction: column;
  }
}
</style>
