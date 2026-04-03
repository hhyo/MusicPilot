<template>
  <section class="job-panel">
    <header class="job-panel__header">
      <div>
        <p class="job-panel__eyebrow">Phase 5 Host-Aware Acquisition Loop</p>
        <h3>搜索任务、候选评分与宿主派发边界</h3>
      </div>
      <el-tag v-if="job" :type="jobAdapterMode === 'host' ? 'success' : 'warning'" effect="plain">
        {{ adapterBadgeLabel }}
      </el-tag>
    </header>

    <el-alert
      title="当前页面展示的是 Phase 5 host-aware acquisition loop。若宿主能力可用会优先走 host-backed skeleton；若能力缺失或配置不完整，会自动回退到 mock，并显式展示 fallback 信息。"
      :type="jobAdapterMode === 'host' ? 'success' : 'warning'"
      :closable="false"
      show-icon
    />

    <el-alert
      v-if="errorMessage"
      :title="errorMessage"
      type="error"
      :closable="false"
      show-icon
    />

    <el-skeleton v-else-if="loading" animated :rows="8" />

    <el-empty
      v-else-if="!job"
      description="从 metadata 详情点击“创建并执行搜索任务”后，这里会展示 query、job 和候选结果。"
    />

    <template v-else>
      <section class="job-card-grid">
        <article class="job-card">
          <span>Job ID</span>
          <strong>{{ job.id }}</strong>
          <p>{{ job.status }} / {{ job.mode }} / {{ job.strategy }}</p>
        </article>
        <article class="job-card">
          <span>Source</span>
          <strong>{{ job.query_source_type }}</strong>
          <p>{{ job.metadata_snapshot?.title || job.query_source_id }}</p>
        </article>
        <article class="job-card">
          <span>Dispatch Recommendation</span>
          <strong>{{ dispatchRecommendation }}</strong>
          <p>best_score: {{ bestScore }}</p>
        </article>
        <article class="job-card">
          <span>Active Search Adapter</span>
          <strong>{{ activeSearchAdapter }}</strong>
          <p>{{ activeFallbackReason }}</p>
        </article>
      </section>

      <section v-if="job.query_build" class="query-section">
        <h4>QueryBuilder 输出</h4>
        <p class="query-section__note">{{ job.query_build.query_context.summary }}</p>

        <div class="query-columns">
          <article class="query-group">
            <h5>Canonical</h5>
            <ul>
              <li v-for="item in job.query_build.canonical_queries" :key="item.query">
                <strong>{{ item.query }}</strong>
                <span>{{ item.explanation }}</span>
              </li>
            </ul>
          </article>
          <article class="query-group">
            <h5>Alias</h5>
            <ul>
              <li v-for="item in job.query_build.alias_queries" :key="item.query">
                <strong>{{ item.query }}</strong>
                <span>{{ item.explanation }}</span>
              </li>
            </ul>
          </article>
          <article class="query-group">
            <h5>Relaxed</h5>
            <ul>
              <li v-for="item in job.query_build.relaxed_queries" :key="item.query">
                <strong>{{ item.query }}</strong>
                <span>{{ item.explanation }}</span>
              </li>
            </ul>
          </article>
          <article class="query-group">
            <h5>Negative</h5>
            <ul>
              <li v-for="item in job.query_build.negative_queries" :key="item.query">
                <strong>{{ item.query }}</strong>
                <span>{{ item.explanation }}</span>
              </li>
            </ul>
          </article>
        </div>
      </section>

      <section class="candidate-section">
        <header class="candidate-section__header">
          <h4>候选列表</h4>
          <p>{{ candidatesNote || '当前候选列表会显示 search adapter mode、dispatch backend 与 fallback 信息。' }}</p>
        </header>

        <el-empty v-if="candidates.length === 0" description="当前 job 暂无候选结果。" />

        <div v-else class="candidate-grid">
          <article v-for="candidate in candidates" :key="candidate.id" class="candidate-card">
            <header class="candidate-card__header">
              <div>
                <p class="candidate-card__site">{{ candidate.site_name }}</p>
                <h5>{{ candidate.title }}</h5>
              </div>
              <el-tag :type="decisionTagType(candidate.decision)" effect="plain">
                {{ candidate.decision }}
              </el-tag>
            </header>

            <div class="candidate-card__meta">
              <span>score_total: {{ candidate.score_total }}</span>
              <span>raw_score: {{ candidate.raw_score }}</span>
              <span>seeders: {{ candidate.seeders }}</span>
              <span>peers: {{ candidate.peers }}</span>
              <span>format: {{ candidate.format_tag || '-' }}</span>
              <span>bitrate: {{ candidate.bitrate_kbps || '-' }}</span>
            </div>

            <div class="candidate-card__tags">
              <el-tag v-for="tag in candidate.source_tags" :key="tag" size="small" effect="plain">
                {{ tag }}
              </el-tag>
              <el-tag size="small" effect="plain" :type="candidate.adapter_resolution?.adapter_mode === 'host' ? 'success' : 'warning'">
                search_backend: {{ candidate.adapter_resolution?.adapter_mode ?? 'mock' }}
              </el-tag>
              <el-tag size="small" effect="plain" type="info">
                verification: {{ candidate.adapter_resolution?.verification_state ?? 'placeholder' }}
              </el-tag>
            </div>

            <p class="candidate-card__note">{{ candidate.note }}</p>
            <p v-if="candidate.adapter_resolution?.fallback_reason" class="candidate-card__runtime">
              fallback: {{ candidate.adapter_resolution.fallback_reason }}
            </p>

            <div class="candidate-card__breakdown">
              <div
                v-for="[key, item] in Object.entries(candidate.score_breakdown)"
                :key="key"
                class="breakdown-row"
              >
                <span>{{ key }}</span>
                <strong>{{ item.score }}</strong>
                <p>{{ item.reason }}</p>
              </div>
            </div>

            <footer class="candidate-card__footer">
              <div>
                <p>dispatch_status: {{ candidate.dispatch_status }}</p>
                <p>search_adapter: {{ candidate.adapter_resolution?.adapter_key ?? 'pending' }}</p>
                <p v-if="dispatchResults[candidate.id]">
                  dispatch_backend: {{ dispatchResults[candidate.id].dispatch_backend }} / {{ dispatchResults[candidate.id].target_downloader }}
                </p>
                <p v-if="dispatchResults[candidate.id]?.fallback_reason">
                  dispatch fallback: {{ dispatchResults[candidate.id]?.fallback_reason }}
                </p>
                <p v-if="dispatchResults[candidate.id]">{{ dispatchResults[candidate.id].note }}</p>
              </div>
              <el-button
                type="primary"
                plain
                :disabled="!candidate.dispatchable"
                :loading="dispatchingCandidateId === candidate.id"
                @click="$emit('dispatch', candidate)"
              >
                {{ candidate.decision === 'manual_confirm' ? '手动确认并派发' : '执行 mock 派发' }}
              </el-button>
            </footer>
          </article>
        </div>
      </section>
    </template>
  </section>
</template>

<script setup lang="ts">
import { computed } from 'vue';

import type { DispatchResult, SearchCandidateDetail, SearchJobSummary } from '@/types/acquisition';

const props = defineProps<{
  job: SearchJobSummary | null;
  candidates: SearchCandidateDetail[];
  loading: boolean;
  errorMessage: string;
  dispatchingCandidateId: string;
  dispatchResults: Record<string, DispatchResult>;
  candidatesNote: string;
}>();

defineEmits<{
  (event: 'dispatch', candidate: SearchCandidateDetail): void;
}>();

const dispatchRecommendation = computed(() => props.job?.summary.dispatch_recommendation ?? 'pending');
const bestScore = computed(() => props.job?.summary.best_score ?? '-');
const jobAdapterMode = computed(() => props.job?.adapter_resolution?.adapter_mode ?? 'mock');
const activeSearchAdapter = computed(() => props.job?.adapter_resolution?.adapter_key ?? 'pending');
const activeFallbackReason = computed(() => props.job?.adapter_resolution?.fallback_reason ?? 'fallback: none');
const adapterBadgeLabel = computed(() => {
  const adapterMode = props.job?.adapter_resolution?.adapter_mode ?? 'mock';
  const adapterKey = props.job?.adapter_resolution?.adapter_key ?? 'mock_host_search';
  return `${adapterMode} / ${adapterKey}`;
});

function decisionTagType(decision: SearchCandidateDetail['decision']) {
  if (decision === 'auto_download') {
    return 'success';
  }
  if (decision === 'manual_confirm') {
    return 'warning';
  }
  return 'danger';
}
</script>

<style scoped lang="scss">
.job-panel {
  display: grid;
  gap: 1rem;
  padding: 1.35rem;
  border: 1px solid var(--mp-line);
  border-radius: 28px;
  background: rgba(255, 255, 255, 0.82);
  box-shadow: 0 18px 40px rgba(52, 37, 122, 0.06);
}

.job-panel__header,
.candidate-section__header,
.candidate-card__header,
.candidate-card__footer {
  display: flex;
  align-items: flex-start;
  justify-content: space-between;
  gap: 1rem;
}

.job-panel__header h3,
.job-panel__eyebrow,
.candidate-section__header h4,
.candidate-section__header p,
.candidate-card__header h5,
.candidate-card__site,
.candidate-card__note,
.candidate-card__runtime {
  margin: 0;
}

.job-panel__eyebrow {
  color: var(--mp-accent);
  font-size: 0.82rem;
  font-weight: 700;
  letter-spacing: 0.08em;
  text-transform: uppercase;
}

.job-card-grid,
.query-columns,
.candidate-grid {
  display: grid;
  gap: 1rem;
}

.job-card-grid {
  grid-template-columns: repeat(4, minmax(0, 1fr));
}

.job-card {
  padding: 1rem;
  border: 1px solid var(--mp-line);
  border-radius: 20px;
  background: rgba(255, 255, 255, 0.92);
}

.job-card span,
.candidate-section__header p,
.query-section__note,
.candidate-card__note,
.breakdown-row p,
.candidate-card__footer p {
  color: var(--mp-muted);
}

.job-card span {
  display: block;
  font-size: 0.88rem;
}

.job-card strong {
  display: block;
  margin-top: 0.45rem;
  font-size: 1.1rem;
}

.job-card p {
  margin: 0.6rem 0 0;
  line-height: 1.6;
}

.query-section,
.candidate-card {
  padding: 1rem;
  border: 1px solid var(--mp-line);
  border-radius: 22px;
  background: rgba(255, 255, 255, 0.92);
}

.query-group h5 {
  margin: 0 0 0.7rem;
}

.query-group ul {
  margin: 0;
  padding-left: 1rem;
  display: grid;
  gap: 0.55rem;
}

.query-group li {
  display: grid;
  gap: 0.2rem;
}

.query-group strong {
  font-size: 0.95rem;
}

.query-group span {
  color: var(--mp-muted);
  line-height: 1.6;
}

.candidate-grid {
  grid-template-columns: repeat(2, minmax(0, 1fr));
}

.candidate-card {
  display: grid;
  gap: 0.9rem;
}

.candidate-card__site {
  color: var(--mp-accent);
  font-size: 0.82rem;
  font-weight: 700;
  letter-spacing: 0.08em;
  text-transform: uppercase;
}

.candidate-card__meta,
.candidate-card__tags {
  display: flex;
  gap: 0.55rem;
  flex-wrap: wrap;
}

.candidate-card__meta span {
  font-size: 0.9rem;
  color: var(--mp-text);
}

.candidate-card__runtime {
  color: var(--mp-accent);
  font-size: 0.82rem;
}

.candidate-card__breakdown {
  display: grid;
  gap: 0.65rem;
}

.breakdown-row {
  display: grid;
  gap: 0.2rem;
  padding: 0.7rem 0.8rem;
  border-radius: 14px;
  background: rgba(246, 247, 251, 0.88);
}

.breakdown-row span,
.breakdown-row strong,
.breakdown-row p {
  margin: 0;
}

@media (max-width: 1100px) {
  .job-card-grid,
  .candidate-grid {
    grid-template-columns: 1fr 1fr;
  }
}

@media (max-width: 760px) {
  .job-card-grid,
  .query-columns,
  .candidate-grid {
    grid-template-columns: 1fr;
  }

  .job-panel__header,
  .candidate-section__header,
  .candidate-card__header,
  .candidate-card__footer {
    flex-direction: column;
  }
}
</style>
