<template>
  <div class="page-shell">
    <VCard class="hero-card">
      <VCardText class="pa-6">
        <p class="eyebrow">Subscriptions</p>
        <h2 class="section-title">订阅、执行记录与主链结果</h2>
        <p class="section-note">
          当前页面直接回看统一音乐媒体解析链固化后的订阅快照、SearchJob、候选和 organize 状态，
          不再围绕旧的“阶段说明页”来组织。
        </p>
      </VCardText>
    </VCard>

    <VAlert
      v-if="listError"
      type="error"
      variant="tonal"
      density="comfortable"
      :text="listError"
    />

    <div class="split-layout">
      <VCard class="panel-card">
        <VCardText class="pa-6 stack">
          <div class="subscriptions-view__header">
            <div>
              <p class="eyebrow">Subscriptions</p>
              <h3 class="section-title">订阅列表</h3>
            </div>
            <VBtn variant="tonal" color="secondary" @click="loadSubscriptions">刷新</VBtn>
          </div>

          <div class="subscriptions-view__filters">
            <VChipGroup v-model="typeFilter" mandatory>
              <VChip v-for="item in typeOptions" :key="item.value" :value="item.value" filter variant="outlined">
                {{ item.label }}
              </VChip>
            </VChipGroup>

            <VChipGroup v-model="statusFilter" mandatory>
              <VChip v-for="item in statusOptions" :key="item.value" :value="item.value" filter variant="outlined">
                {{ item.label }}
              </VChip>
            </VChipGroup>
          </div>

          <template v-if="listLoading">
            <VSkeletonLoader type="article, article, article" />
          </template>

          <template v-else-if="subscriptions.length === 0">
            <VAlert
              type="info"
              variant="tonal"
              density="comfortable"
              text="当前没有订阅。可以先从 Discovery 或 Search 页面创建。"
            />
          </template>

          <div v-else class="stack">
            <VCard
              v-for="item in subscriptions"
              :key="item.id"
              class="subscriptions-view__item"
              :class="{ 'subscriptions-view__item--active': selectedSubscriptionId === item.id }"
              rounded="xl"
              elevation="0"
              @click="selectSubscription(item.id)"
            >
              <VCardText class="stack">
                <div class="subscriptions-view__header">
                  <div>
                    <p class="eyebrow">{{ item.subscription_type }}</p>
                    <h4 class="subscriptions-view__title">{{ item.target_name }}</h4>
                  </div>
                  <VChip color="primary" variant="tonal">{{ item.status }}</VChip>
                </div>
                <p class="section-note">
                  {{ item.chart_name || item.target_entity_type || 'metadata' }} ·
                  {{ item.latest_run_status || '尚未执行' }}
                </p>
                <div class="subscriptions-view__actions">
                  <VBtn
                    color="primary"
                    variant="flat"
                    :loading="runningSubscriptionId === item.id"
                    @click.stop="handleRun(item.id)"
                  >
                    立即执行
                  </VBtn>
                  <VBtn variant="tonal" @click.stop="toggleSubscriptionStatus(item)">
                    {{ item.status === 'active' ? '暂停' : '启用' }}
                  </VBtn>
                  <VBtn variant="outlined" color="error" @click.stop="handleArchive(item.id)">
                    归档
                  </VBtn>
                </div>
              </VCardText>
            </VCard>
          </div>
        </VCardText>
      </VCard>

      <VCard class="panel-card">
        <VCardText class="pa-6 stack">
          <div class="subscriptions-view__header">
            <div>
              <p class="eyebrow">Execution Detail</p>
              <h3 class="section-title">{{ selectedSubscription?.target_name || '选择一个订阅' }}</h3>
            </div>
            <VBtn
              v-if="selectedSubscriptionId"
              variant="tonal"
              color="secondary"
              @click="refreshSelectedSubscription"
            >
              刷新
            </VBtn>
          </div>

          <VAlert
            v-if="detailError"
            type="error"
            variant="tonal"
            density="comfortable"
            :text="detailError"
          />

          <template v-else-if="detailLoading">
            <VSkeletonLoader type="article, article, article" />
          </template>

          <template v-else-if="!selectedSubscription">
            <VAlert
              type="info"
              variant="tonal"
              density="comfortable"
              text="选择订阅后，这里会显示 run 历史、SearchJob 摘要和 organize 状态。"
            />
          </template>

          <template v-else>
            <div class="meta-pairs">
              <div class="meta-pair">
                <span class="meta-pair__label">Mode</span>
                <span class="meta-pair__value">{{ selectedSubscription.mode }}</span>
              </div>
              <div class="meta-pair">
                <span class="meta-pair__label">Latest Run</span>
                <span class="meta-pair__value">{{ selectedSubscription.latest_run_status || '-' }}</span>
              </div>
              <div class="meta-pair">
                <span class="meta-pair__label">Last Run At</span>
                <span class="meta-pair__value">{{ formatDate(selectedSubscription.last_run_at) }}</span>
              </div>
              <div class="meta-pair">
                <span class="meta-pair__label">Entity Type</span>
                <span class="meta-pair__value">{{ selectedSubscription.target_entity_type || '-' }}</span>
              </div>
            </div>

            <div class="soft-block">
              <p class="eyebrow">Recognition Snapshot</p>
              <p class="section-note">
                {{ recognitionSnapshotText }}
              </p>
            </div>

            <div class="stack">
              <div class="subscriptions-view__header">
                <div>
                  <p class="eyebrow">Runs</p>
                  <h4 class="subscriptions-view__title">执行历史</h4>
                </div>
              </div>

              <VCard
                v-for="run in runs"
                :key="run.id"
                class="subscriptions-view__item"
                :class="{ 'subscriptions-view__item--active': selectedRunId === run.id }"
                rounded="xl"
                elevation="0"
                @click="selectRun(run.id)"
              >
                <VCardText class="stack">
                  <div class="subscriptions-view__header">
                    <div>
                      <p class="eyebrow">{{ run.execution_status }}</p>
                      <h5 class="subscriptions-view__title">{{ run.id }}</h5>
                    </div>
                    <VChip variant="outlined">{{ run.matched_candidates_count }} candidates</VChip>
                  </div>
                  <p class="section-note">{{ formatDate(run.finished_at || run.started_at) }}</p>
                </VCardText>
              </VCard>
            </div>

            <div v-if="selectedRunDetail" class="stack">
              <div class="soft-block">
                <p class="eyebrow">Run Summary</p>
                <p class="section-note">
                  {{ selectedRunDetail.execution_status }} ·
                  {{ selectedRunDetail.search_job?.status || 'no search job' }} ·
                  {{ selectedRunDetail.organize_preview?.organize_status || 'no organize preview' }}
                </p>
              </div>

              <div v-if="selectedRunDetail.search_job" class="soft-block">
                <p class="eyebrow">Search Job</p>
                <p class="section-note">
                  {{ selectedRunDetail.search_job.id }} · {{ selectedRunDetail.search_job.music_media_info.title || '-' }}
                </p>
              </div>

              <div v-if="selectedRunDetail.candidates.length > 0" class="stack">
                <p class="eyebrow">Candidates</p>
                <VCard
                  v-for="candidate in selectedRunDetail.candidates"
                  :key="candidate.id"
                  class="subscriptions-view__item"
                  rounded="xl"
                  elevation="0"
                >
                  <VCardText class="stack">
                    <div class="subscriptions-view__header">
                      <div>
                        <h5 class="subscriptions-view__title">{{ candidate.title }}</h5>
                        <p class="section-note">{{ candidate.site_name }} · {{ candidate.score_total }}</p>
                      </div>
                      <VChip variant="outlined">{{ candidate.dispatch_status }}</VChip>
                    </div>
                  </VCardText>
                </VCard>
              </div>

              <div v-if="selectedRunDetail.organize_preview" class="soft-block">
                <p class="eyebrow">Organize</p>
                <p class="section-note">
                  {{ selectedRunDetail.organize_preview.organize_status }} ·
                  {{ selectedRunDetail.organize_preview.target_relative_path }}
                </p>
              </div>
            </div>
          </template>
        </VCardText>
      </VCard>
    </div>
  </div>
</template>

<script setup lang="ts">
import { computed, onMounted, ref } from 'vue';

import {
  archiveSubscription,
  fetchSubscription,
  fetchSubscriptionRun,
  fetchSubscriptions,
  fetchSubscriptionRuns,
  runSubscription,
  updateSubscription,
} from '@/services/subscriptions';
import type {
  SubscriptionDetail,
  SubscriptionRunDetail,
  SubscriptionRunSummary,
  SubscriptionState,
  SubscriptionSummary,
  SubscriptionType,
} from '@/types/orchestration';

const typeFilter = ref<'all' | SubscriptionType>('all');
const statusFilter = ref<'all' | SubscriptionState>('all');
const listLoading = ref(false);
const listError = ref('');
const subscriptions = ref<SubscriptionSummary[]>([]);
const selectedSubscriptionId = ref('');
const selectedSubscription = ref<SubscriptionDetail | null>(null);
const detailLoading = ref(false);
const detailError = ref('');
const runningSubscriptionId = ref('');
const runs = ref<SubscriptionRunSummary[]>([]);
const selectedRunId = ref('');
const selectedRunDetail = ref<SubscriptionRunDetail | null>(null);

const typeOptions = [
  { value: 'all', label: '全部类型' },
  { value: 'artist', label: '艺人' },
  { value: 'album', label: '专辑' },
  { value: 'track', label: '歌曲' },
  { value: 'chart_entry', label: '榜单项' },
] as const;

const statusOptions = [
  { value: 'all', label: '全部状态' },
  { value: 'active', label: 'active' },
  { value: 'paused', label: 'paused' },
  { value: 'archived', label: 'archived' },
] as const;

const recognitionSnapshotText = computed(() => {
  const payload = selectedSubscription.value?.target_payload || {};
  const assessment = payload.music_recognition_assessment as { state?: string; note?: string } | undefined;
  const media = payload.music_media_info as { provider?: string; provider_id?: string } | undefined;
  if (!assessment && !media) return '当前订阅没有固化的识别快照。';
  return `${assessment?.state || 'unknown'} · ${assessment?.note || '无附加说明'} · ${media?.provider || 'unknown'} / ${
    media?.provider_id || '-'
  }`;
});

onMounted(() => {
  void loadSubscriptions();
});

async function loadSubscriptions() {
  listLoading.value = true;
  listError.value = '';
  try {
    const response = await fetchSubscriptions({
      subscription_type: typeFilter.value === 'all' ? undefined : typeFilter.value,
      status: statusFilter.value === 'all' ? undefined : statusFilter.value,
    });
    subscriptions.value = response.data.items;
    if (subscriptions.value.length > 0 && !selectedSubscriptionId.value) {
      await selectSubscription(subscriptions.value[0].id);
    }
  } catch (error) {
    listError.value = error instanceof Error ? error.message : '订阅列表加载失败。';
  } finally {
    listLoading.value = false;
  }
}

async function selectSubscription(subscriptionId: string) {
  selectedSubscriptionId.value = subscriptionId;
  detailLoading.value = true;
  detailError.value = '';
  try {
    const [detailResponse, runsResponse] = await Promise.all([
      fetchSubscription(subscriptionId),
      fetchSubscriptionRuns(subscriptionId),
    ]);
    selectedSubscription.value = detailResponse.data;
    runs.value = runsResponse.data.items;
    if (runs.value.length > 0) {
      await selectRun(runs.value[0].id);
    } else {
      selectedRunId.value = '';
      selectedRunDetail.value = null;
    }
  } catch (error) {
    detailError.value = error instanceof Error ? error.message : '订阅详情加载失败。';
  } finally {
    detailLoading.value = false;
  }
}

async function refreshSelectedSubscription() {
  if (!selectedSubscriptionId.value) return;
  await selectSubscription(selectedSubscriptionId.value);
}

async function selectRun(runId: string) {
  selectedRunId.value = runId;
  try {
    const response = await fetchSubscriptionRun(runId);
    selectedRunDetail.value = response.data;
  } catch (error) {
    detailError.value = error instanceof Error ? error.message : '运行详情加载失败。';
  }
}

async function handleRun(subscriptionId: string) {
  runningSubscriptionId.value = subscriptionId;
  try {
    await runSubscription(subscriptionId);
    await selectSubscription(subscriptionId);
  } catch (error) {
    detailError.value = error instanceof Error ? error.message : '执行订阅失败。';
  } finally {
    runningSubscriptionId.value = '';
  }
}

async function toggleSubscriptionStatus(item: SubscriptionSummary) {
  const nextStatus: SubscriptionState = item.status === 'active' ? 'paused' : 'active';
  await updateSubscription(item.id, { status: nextStatus });
  await loadSubscriptions();
  if (selectedSubscriptionId.value === item.id) {
    await selectSubscription(item.id);
  }
}

async function handleArchive(subscriptionId: string) {
  await archiveSubscription(subscriptionId);
  selectedSubscriptionId.value = '';
  selectedSubscription.value = null;
  selectedRunId.value = '';
  selectedRunDetail.value = null;
  await loadSubscriptions();
}

function formatDate(value?: string | null) {
  if (!value) return '-';
  return new Date(value).toLocaleString();
}
</script>

<style scoped lang="scss">
.subscriptions-view__header,
.subscriptions-view__filters,
.subscriptions-view__actions {
  display: flex;
  align-items: flex-start;
  justify-content: space-between;
  gap: 0.75rem;
}

.subscriptions-view__filters,
.subscriptions-view__actions {
  flex-wrap: wrap;
}

.subscriptions-view__item {
  border: 1px solid var(--mp-line);
  background: var(--mp-panel-soft);
}

.subscriptions-view__item--active {
  border-color: var(--mp-line-strong);
}

.subscriptions-view__title {
  margin: 0.25rem 0 0;
}
</style>
