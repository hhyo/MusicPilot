<template>
  <div class="subscriptions-view">
    <section class="hero-panel">
      <div>
        <p class="hero-panel__eyebrow">Subscriptions</p>
        <h2>订阅与执行记录最小闭环</h2>
        <p class="hero-panel__description">
          当前页面展示的是 Phase 6 最小订阅闭环：可创建和管理四类订阅、同步执行一次 run、
          回看 SearchJob 摘要与 organize preview/apply。真实 scheduler、真实榜单增量与真实文件整理链路仍未完成验证。
        </p>
      </div>
      <el-tag type="warning" effect="plain">host-aware organize / sync subscription executor</el-tag>
    </section>

    <el-alert
      title="Phase 6 订阅执行器仍为同步最小骨架：不会自动定时执行；organize 已升级为 host-aware preview/apply，但真实文件移动、硬链接、刮削与媒体库刷新仍待宿主验证。"
      type="warning"
      :closable="false"
      show-icon
    />

    <section class="filters-panel">
      <div class="filters-panel__group">
        <span>订阅类型</span>
        <div class="pill-row">
          <button
            v-for="item in typeOptions"
            :key="item.value"
            type="button"
            class="pill-button"
            :class="{ 'pill-button--active': typeFilter === item.value }"
            @click="changeTypeFilter(item.value)"
          >
            {{ item.label }}
          </button>
        </div>
      </div>

      <div class="filters-panel__group">
        <span>状态</span>
        <div class="pill-row">
          <button
            v-for="item in statusOptions"
            :key="item.value"
            type="button"
            class="pill-button"
            :class="{ 'pill-button--active': statusFilter === item.value }"
            @click="changeStatusFilter(item.value)"
          >
            {{ item.label }}
          </button>
        </div>
      </div>
    </section>

    <div class="layout-grid">
      <section class="list-panel">
        <header class="section-header">
          <div>
            <p class="section-header__eyebrow">Subscription List</p>
            <h3>订阅对象</h3>
          </div>
          <el-button text @click="loadSubscriptions">刷新</el-button>
        </header>

        <el-alert
          v-if="listError"
          :title="listError"
          type="error"
          :closable="false"
          show-icon
        />

        <div v-else-if="listLoading" class="loading-grid">
          <el-skeleton v-for="index in 4" :key="index" animated :rows="4" />
        </div>

        <el-empty
          v-else-if="subscriptions.length === 0"
          description="当前还没有订阅。可以先到搜索页或榜单页创建一个。"
        />

        <div v-else class="subscription-list">
          <article
            v-for="item in subscriptions"
            :key="item.id"
            class="subscription-card"
            :class="{ 'subscription-card--active': selectedSubscriptionId === item.id }"
            @click="selectSubscription(item.id)"
          >
            <div class="subscription-card__header">
              <div>
                <p class="subscription-card__eyebrow">{{ item.subscription_type }}</p>
                <h4>{{ item.target_name }}</h4>
              </div>
              <el-tag :type="subscriptionStatusTag(item.status)" effect="plain">
                {{ item.status }}
              </el-tag>
            </div>

            <p class="subscription-card__meta">
              {{ item.chart_source || item.target_entity_type || 'metadata' }}
              <span v-if="item.chart_name"> · {{ item.chart_name }}</span>
            </p>
            <p class="subscription-card__note">{{ item.note }}</p>

            <div class="subscription-card__footer">
              <div>
                <p>最近执行：{{ formatDate(item.last_run_at) }}</p>
                <p>最近状态：{{ item.latest_run_status || '尚未执行' }}</p>
              </div>
              <div class="subscription-card__actions">
                <el-button
                  size="small"
                  type="primary"
                  plain
                  :loading="runningSubscriptionId === item.id"
                  @click.stop="handleRun(item.id)"
                >
                  立即执行
                </el-button>
                <el-button
                  size="small"
                  @click.stop="toggleSubscriptionStatus(item)"
                >
                  {{ item.status === 'active' ? '暂停' : '启用' }}
                </el-button>
                <el-button
                  size="small"
                  type="danger"
                  plain
                  @click.stop="handleArchive(item.id)"
                >
                  归档
                </el-button>
              </div>
            </div>
          </article>
        </div>
      </section>

      <section class="detail-panel">
        <header class="section-header">
          <div>
            <p class="section-header__eyebrow">Execution Detail</p>
            <h3>{{ selectedSubscription?.target_name || '订阅详情与 run 结果' }}</h3>
          </div>
          <el-button
            v-if="selectedSubscriptionId"
            text
            @click="refreshSelectedSubscription"
          >
            刷新
          </el-button>
        </header>

        <el-alert
          v-if="detailError"
          :title="detailError"
          type="error"
          :closable="false"
          show-icon
        />

        <div v-else-if="detailLoading" class="loading-grid">
          <el-skeleton v-for="index in 3" :key="index" animated :rows="6" />
        </div>

        <el-empty
          v-else-if="!selectedSubscription"
          description="选择订阅后，这里会显示 run 历史、候选摘要和 organize 状态。"
        />

        <template v-else>
          <section class="summary-grid">
            <article class="summary-card">
              <span>类型</span>
              <strong>{{ selectedSubscription.subscription_type }}</strong>
              <p>{{ selectedSubscription.mode }}</p>
            </article>
            <article class="summary-card">
              <span>状态</span>
              <strong>{{ selectedSubscription.status }}</strong>
              <p>{{ selectedSubscription.latest_run_status || '尚未执行' }}</p>
            </article>
            <article class="summary-card">
              <span>目标</span>
              <strong>{{ selectedSubscription.target_name }}</strong>
              <p>{{ selectedSubscription.chart_name || selectedSubscription.target_entity_type || 'metadata' }}</p>
            </article>
          </section>

          <section class="runs-panel">
            <header class="runs-panel__header">
              <h4>Run 历史</h4>
              <p>同步执行结果可回看，当前不启用生产级 scheduler。</p>
            </header>

            <el-empty
              v-if="runs.length === 0"
              description="当前订阅还没有 run 记录。"
            />

            <div v-else class="run-list">
              <article
                v-for="run in runs"
                :key="run.id"
                class="run-card"
                :class="{ 'run-card--active': selectedRunId === run.id }"
                @click="selectRun(run.id)"
              >
                <div>
                  <strong>{{ run.execution_status }}</strong>
                  <p>{{ run.dispatch_recommendation }} · {{ run.matched_candidates_count }} candidates</p>
                </div>
                <span>{{ formatDate(run.finished_at || run.started_at) }}</span>
              </article>
            </div>
          </section>

          <section class="run-detail-panel">
            <header class="runs-panel__header">
              <h4>Run 摘要</h4>
              <p>候选、评分与 organize 会明确展示当前 backend、verification state 与 fallback。</p>
            </header>

            <el-empty
              v-if="!selectedRunDetail"
              description="选择一条 run 记录后查看详情。"
            />

            <template v-else>
              <section class="summary-grid">
                <article class="summary-card">
                  <span>Run</span>
                  <strong>{{ selectedRunDetail.execution_status }}</strong>
                  <p>{{ selectedRunDetail.id }}</p>
                </article>
                <article class="summary-card">
                  <span>SearchJob</span>
                  <strong>{{ selectedRunDetail.search_job?.status || '-' }}</strong>
                  <p>{{ selectedRunDetail.search_job?.id || '未生成' }}</p>
                </article>
                <article class="summary-card">
                  <span>Dispatch Recommendation</span>
                  <strong>{{ selectedRunDetail.dispatch_recommendation }}</strong>
                  <p>{{ selectedRunDetail.matched_candidates_count }} candidates</p>
                </article>
                <article v-if="selectedRunDetail.organize_preview" class="summary-card">
                  <span>Organize Backend</span>
                  <strong>{{ selectedRunDetail.organize_preview.organize_backend }}</strong>
                  <p>{{ selectedRunDetail.organize_preview.organize_status }}</p>
                </article>
              </section>

              <section class="candidate-panel">
                <h4>候选摘要</h4>
                <el-empty
                  v-if="selectedRunDetail.candidates.length === 0"
                  description="当前 run 没有候选。"
                />

                <div v-else class="candidate-list">
                  <article
                    v-for="candidate in selectedRunDetail.candidates.slice(0, 3)"
                    :key="candidate.id"
                    class="candidate-card"
                  >
                    <div>
                      <h5>{{ candidate.title }}</h5>
                      <p>{{ candidate.site_name }} · {{ candidate.decision }}</p>
                    </div>
                    <div class="candidate-card__stats">
                      <span>{{ candidate.score_total }}</span>
                      <span>{{ candidate.format_tag || '-' }}</span>
                      <span>{{ candidate.seeders }} seeders</span>
                    </div>
                  </article>
                </div>
              </section>

              <section class="organize-panel">
                <header class="runs-panel__header">
                  <h4>Organize Record</h4>
                  <div class="organize-actions">
                    <el-button
                      v-if="selectedRunDetail.candidates[0]"
                      size="small"
                      :loading="organizeLoading"
                      @click="handleOrganizePreview(selectedRunDetail.candidates[0].id)"
                    >
                      刷新 organize preview
                    </el-button>
                    <el-button
                      v-if="selectedRunDetail.organize_preview"
                      size="small"
                      type="primary"
                      plain
                      :loading="organizeApplying"
                      :disabled="!selectedRunDetail.organize_preview.organizeable"
                      @click="handleOrganizeApply(selectedRunDetail.organize_preview.id)"
                    >
                      执行 organize apply
                    </el-button>
                  </div>
                </header>

                <el-empty
                  v-if="!selectedRunDetail.organize_preview"
                  description="当前 run 还没有 organize preview。"
                />

                <article v-else class="organize-card">
                  <div>
                    <strong>{{ selectedRunDetail.organize_preview.organize_status }}</strong>
                    <p>{{ selectedRunDetail.organize_preview.target_library_path }}</p>
                  </div>
                  <div class="organize-card__body">
                    <p>backend: {{ selectedRunDetail.organize_preview.organize_backend }}</p>
                    <p>verification: {{ selectedRunDetail.organize_preview.verification_state }}</p>
                    <p>relative_path: {{ selectedRunDetail.organize_preview.target_relative_path }}</p>
                    <p>strategy: {{ selectedRunDetail.organize_preview.strategy }}</p>
                    <p>conflict_policy: {{ selectedRunDetail.organize_preview.strategy_snapshot.conflict_policy }}</p>
                    <p v-if="selectedRunDetail.organize_preview.fallback_reason">
                      fallback: {{ selectedRunDetail.organize_preview.fallback_reason }}
                    </p>
                    <p v-if="selectedRunDetail.organize_preview.failure_reason">
                      failure: {{ selectedRunDetail.organize_preview.failure_reason }}
                    </p>
                    <p>{{ selectedRunDetail.organize_preview.strategy_note }}</p>
                  </div>
                </article>
              </section>
            </template>
          </section>
        </template>
      </section>
    </div>
  </div>
</template>

<script setup lang="ts">
import axios from 'axios';
import { computed, onMounted, ref } from 'vue';
import { ElMessage } from 'element-plus';

import {
  applyOrganize,
  archiveSubscription,
  fetchSubscription,
  fetchSubscriptionRun,
  fetchSubscriptionRuns,
  fetchSubscriptions,
  previewOrganize,
  runSubscription,
  updateSubscription,
} from '@/services/orchestration';
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
const subscriptions = ref<SubscriptionSummary[]>([]);
const selectedSubscriptionId = ref('');
const selectedRunId = ref('');
const selectedSubscription = ref<SubscriptionDetail | null>(null);
const selectedRunDetail = ref<SubscriptionRunDetail | null>(null);
const runs = ref<SubscriptionRunSummary[]>([]);
const listLoading = ref(false);
const detailLoading = ref(false);
const organizeLoading = ref(false);
const organizeApplying = ref(false);
const listError = ref('');
const detailError = ref('');
const runningSubscriptionId = ref('');

const typeOptions = [
  { value: 'all', label: '全部' },
  { value: 'artist', label: '艺人' },
  { value: 'album', label: '专辑' },
  { value: 'track', label: '歌曲' },
  { value: 'chart_entry', label: '榜单项' },
] as const;

const statusOptions = [
  { value: 'all', label: '全部' },
  { value: 'active', label: '启用' },
  { value: 'paused', label: '暂停' },
  { value: 'archived', label: '归档' },
] as const;

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

    if (!response.success) {
      throw new Error(response.message);
    }

    subscriptions.value = response.data.items;

    if (response.data.items.length > 0) {
      const nextId = response.data.items.some((item) => item.id === selectedSubscriptionId.value)
        ? selectedSubscriptionId.value
        : response.data.items[0].id;
      await selectSubscription(nextId);
    } else {
      selectedSubscriptionId.value = '';
      selectedRunId.value = '';
      selectedSubscription.value = null;
      selectedRunDetail.value = null;
      runs.value = [];
    }
  } catch (error) {
    subscriptions.value = [];
    listError.value = resolveErrorMessage(error, '订阅列表加载失败，请确认后端已启动。');
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

    if (!detailResponse.success) {
      throw new Error(detailResponse.message);
    }
    if (!runsResponse.success) {
      throw new Error(runsResponse.message);
    }

    selectedSubscription.value = detailResponse.data;
    runs.value = runsResponse.data.items;

    if (runsResponse.data.items.length > 0) {
      const nextRunId = runsResponse.data.items.some((item) => item.id === selectedRunId.value)
        ? selectedRunId.value
        : runsResponse.data.items[0].id;
      await selectRun(nextRunId);
    } else {
      selectedRunId.value = '';
      selectedRunDetail.value = null;
    }
  } catch (error) {
    detailError.value = resolveErrorMessage(error, '订阅详情加载失败。');
  } finally {
    detailLoading.value = false;
  }
}

async function selectRun(runId: string) {
  selectedRunId.value = runId;

  try {
    const response = await fetchSubscriptionRun(runId);
    if (!response.success) {
      throw new Error(response.message);
    }
    selectedRunDetail.value = response.data;
  } catch (error) {
    detailError.value = resolveErrorMessage(error, 'run 详情加载失败。');
  }
}

async function handleRun(subscriptionId: string) {
  runningSubscriptionId.value = subscriptionId;
  detailError.value = '';

  try {
    const response = await runSubscription(subscriptionId);
    if (!response.success) {
      throw new Error(response.message);
    }

    selectedRunDetail.value = response.data;
    selectedRunId.value = response.data.id;
    ElMessage.success('订阅已执行一次最小闭环。');
    await loadSubscriptions();
    await selectSubscription(subscriptionId);
  } catch (error) {
    ElMessage.error(resolveErrorMessage(error, '执行订阅失败。'));
  } finally {
    runningSubscriptionId.value = '';
  }
}

async function toggleSubscriptionStatus(item: SubscriptionSummary) {
  if (item.status === 'archived') {
    return;
  }

  const nextStatus: SubscriptionState = item.status === 'active' ? 'paused' : 'active';

  try {
    const response = await updateSubscription(item.id, { status: nextStatus });
    if (!response.success) {
      throw new Error(response.message);
    }
    ElMessage.success(`订阅已切换为 ${nextStatus}。`);
    await loadSubscriptions();
  } catch (error) {
    ElMessage.error(resolveErrorMessage(error, '更新订阅状态失败。'));
  }
}

async function handleArchive(subscriptionId: string) {
  try {
    const response = await archiveSubscription(subscriptionId);
    if (!response.success) {
      throw new Error(response.message);
    }
    ElMessage.success('订阅已归档。');
    await loadSubscriptions();
  } catch (error) {
    ElMessage.error(resolveErrorMessage(error, '归档订阅失败。'));
  }
}

async function handleOrganizePreview(candidateId: string) {
  organizeLoading.value = true;

  try {
    const response = await previewOrganize({ candidate_id: candidateId });
    if (!response.success) {
      throw new Error(response.message);
    }

    if (selectedRunDetail.value) {
      selectedRunDetail.value = {
        ...selectedRunDetail.value,
        organize_preview: response.data,
      };
    }

    ElMessage.success('已刷新 organize preview。');
  } catch (error) {
    ElMessage.error(resolveErrorMessage(error, '刷新 organize preview 失败。'));
  } finally {
    organizeLoading.value = false;
  }
}

async function handleOrganizeApply(recordId: string) {
  organizeApplying.value = true;

  try {
    const response = await applyOrganize({ organize_job_id: recordId });
    if (!response.success) {
      throw new Error(response.message);
    }

    if (selectedRunDetail.value) {
      selectedRunDetail.value = {
        ...selectedRunDetail.value,
        organize_preview: response.data,
      };
    }

    ElMessage.success('已执行 organize apply。');
  } catch (error) {
    ElMessage.error(resolveErrorMessage(error, '执行 organize apply 失败。'));
  } finally {
    organizeApplying.value = false;
  }
}

async function refreshSelectedSubscription() {
  if (!selectedSubscriptionId.value) {
    return;
  }
  await selectSubscription(selectedSubscriptionId.value);
}

function changeTypeFilter(value: 'all' | SubscriptionType) {
  typeFilter.value = value;
  void loadSubscriptions();
}

function changeStatusFilter(value: 'all' | SubscriptionState) {
  statusFilter.value = value;
  void loadSubscriptions();
}

function subscriptionStatusTag(status: SubscriptionState) {
  if (status === 'active') {
    return 'success';
  }
  if (status === 'paused') {
    return 'warning';
  }
  return 'info';
}

function formatDate(value?: string | null) {
  if (!value) {
    return '尚未执行';
  }

  return new Date(value).toLocaleString('zh-CN', {
    hour12: false,
  });
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
.subscriptions-view {
  display: grid;
  gap: 1.2rem;
}

.hero-panel,
.filters-panel,
.list-panel,
.detail-panel {
  padding: 1.4rem;
  border: 1px solid var(--mp-line);
  border-radius: 28px;
  background: rgba(255, 255, 255, 0.82);
  box-shadow: 0 18px 40px rgba(52, 37, 122, 0.06);
}

.hero-panel,
.section-header,
.subscription-card__header,
.subscription-card__footer,
.runs-panel__header,
.run-card,
.organize-card {
  display: flex;
  align-items: flex-start;
  justify-content: space-between;
  gap: 1rem;
}

.organize-actions {
  display: flex;
  gap: 0.6rem;
  flex-wrap: wrap;
}

.hero-panel__eyebrow,
.section-header__eyebrow,
.subscription-card__eyebrow {
  margin: 0;
  color: var(--mp-accent);
  font-size: 0.82rem;
  font-weight: 700;
  letter-spacing: 0.08em;
  text-transform: uppercase;
}

.hero-panel h2,
.section-header h3,
.subscription-card h4,
.subscription-card__meta,
.subscription-card__note,
.hero-panel__description,
.run-card p,
.organize-card p,
.summary-card p {
  margin: 0;
}

.hero-panel__description,
.subscription-card__meta,
.subscription-card__note,
.run-card p,
.organize-card p,
.summary-card p,
.runs-panel__header p {
  color: var(--mp-muted);
  line-height: 1.7;
}

.filters-panel,
.filters-panel__group,
.pill-row,
.summary-grid,
.loading-grid,
.subscription-list,
.run-list,
.candidate-list,
.candidate-card,
.detail-panel,
.runs-panel,
.run-detail-panel {
  display: grid;
  gap: 1rem;
}

.filters-panel__group span {
  font-weight: 700;
}

.pill-row {
  grid-auto-flow: column;
  grid-auto-columns: max-content;
  overflow-x: auto;
  padding-bottom: 0.2rem;
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

.layout-grid {
  display: grid;
  grid-template-columns: minmax(0, 0.95fr) minmax(0, 1.05fr);
  gap: 1.2rem;
}

.subscription-card,
.summary-card,
.run-card,
.candidate-card,
.organize-card {
  padding: 1rem;
  border: 1px solid var(--mp-line);
  border-radius: 22px;
  background: rgba(255, 255, 255, 0.92);
}

.subscription-card {
  cursor: pointer;
}

.subscription-card--active,
.run-card--active {
  border-color: rgba(126, 94, 248, 0.4);
  box-shadow: 0 12px 30px rgba(126, 94, 248, 0.12);
}

.subscription-card__actions {
  display: flex;
  gap: 0.45rem;
  flex-wrap: wrap;
  justify-content: flex-end;
}

.summary-grid {
  grid-template-columns: repeat(auto-fit, minmax(180px, 1fr));
}

.summary-card span {
  color: var(--mp-muted);
  font-size: 0.88rem;
}

.summary-card strong {
  display: block;
  margin-top: 0.45rem;
  font-size: 1.05rem;
}

.run-card {
  cursor: pointer;
  align-items: center;
}

.candidate-card h5 {
  margin: 0;
}

.candidate-card__stats {
  display: flex;
  gap: 0.8rem;
  flex-wrap: wrap;
  color: var(--mp-muted);
}

.organize-card__body {
  display: grid;
  gap: 0.35rem;
}

@media (max-width: 1040px) {
  .hero-panel,
  .section-header,
  .subscription-card__header,
  .subscription-card__footer,
  .runs-panel__header,
  .run-card,
  .organize-card {
    flex-direction: column;
  }

  .layout-grid,
  .summary-grid {
    grid-template-columns: 1fr;
  }
}
</style>
