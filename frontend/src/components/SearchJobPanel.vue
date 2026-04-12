<template>
  <VCard class="panel-card">
    <VCardText class="stack">
      <div class="search-job-panel__header">
        <div>
          <p class="eyebrow">Acquisition</p>
          <h3 class="section-title">搜索任务与候选结果</h3>
        </div>
        <VChip v-if="job" color="primary" variant="tonal">{{ job.status }}</VChip>
      </div>

      <VAlert
        v-if="errorMessage"
        type="error"
        variant="tonal"
        density="comfortable"
        :text="errorMessage"
      />

      <template v-else-if="loading">
        <VSkeletonLoader type="article, article, article" />
      </template>

      <template v-else-if="job">
        <div class="meta-pairs">
          <div class="meta-pair">
            <span class="meta-pair__label">Job</span>
            <span class="meta-pair__value">{{ job.id }}</span>
          </div>
          <div class="meta-pair">
            <span class="meta-pair__label">Trigger</span>
            <span class="meta-pair__value">{{ job.trigger_source }}</span>
          </div>
          <div class="meta-pair">
            <span class="meta-pair__label">Profile</span>
            <span class="meta-pair__value">{{ job.profile_id }}</span>
          </div>
          <div class="meta-pair">
            <span class="meta-pair__label">Entity</span>
            <span class="meta-pair__value">{{ job.music_media_info.title || '-' }}</span>
          </div>
        </div>

        <div v-if="job.query_build" class="soft-block stack">
          <p class="eyebrow">Query Build</p>
          <p class="section-note">{{ job.query_build.query_context.summary }}</p>
          <div class="search-job-panel__chips">
            <VChip
              v-for="query in job.query_build.ordered_queries.slice(0, 6)"
              :key="`${query.query_type}-${query.query}`"
              variant="outlined"
            >
              {{ query.query }}
            </VChip>
          </div>
        </div>

        <div v-if="candidates.length > 0" class="stack">
          <div class="search-job-panel__header">
            <div>
              <p class="eyebrow">Candidates</p>
              <p class="section-note">{{ candidatesNote || '当前候选列表展示评分、派发状态与 handoff 摘要。' }}</p>
            </div>
          </div>

          <VCard
            v-for="candidate in candidates"
            :key="candidate.id"
            class="search-job-panel__candidate"
            rounded="xl"
            elevation="0"
          >
            <VCardText class="stack">
              <div class="search-job-panel__candidate-head">
                <div>
                  <h4 class="search-job-panel__candidate-title">{{ candidate.title }}</h4>
                  <p class="section-note">
                    {{ candidate.site_name }} · {{ candidate.format_tag || 'unknown format' }} ·
                    {{ candidate.seeders }} seeders
                  </p>
                </div>
                <VChip color="secondary" variant="tonal">{{ candidate.decision }}</VChip>
              </div>

              <div class="search-job-panel__chips">
                <VChip variant="outlined">Score {{ candidate.score_total }}</VChip>
                <VChip variant="outlined">{{ candidate.dispatch_status }}</VChip>
                <VChip v-if="candidate.path_handoff?.handoff_status" variant="outlined">
                  {{ candidate.path_handoff.handoff_status }}
                </VChip>
              </div>

              <div class="search-job-panel__candidate-actions">
                <VBtn
                  color="primary"
                  variant="flat"
                  :loading="dispatchingCandidateId === candidate.id"
                  :disabled="!candidate.dispatchable"
                  @click="$emit('dispatch', candidate)"
                >
                  派发下载
                </VBtn>
                <VChip
                  v-if="dispatchResults[candidate.id]"
                  color="success"
                  variant="tonal"
                >
                  {{ dispatchResults[candidate.id].dispatch_status }}
                </VChip>
              </div>
            </VCardText>
          </VCard>
        </div>
      </template>

      <VAlert
        v-else
        type="info"
        variant="tonal"
        density="comfortable"
        text="创建并执行搜索任务后，这里会显示 QueryBuilder 输出、候选评分与派发结果。"
      />
    </VCardText>
  </VCard>
</template>

<script setup lang="ts">
import type { DispatchResult, SearchCandidateDetail, SearchJobSummary } from '@/types/acquisition';

defineProps<{
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
</script>

<style scoped lang="scss">
.search-job-panel__header,
.search-job-panel__candidate-head,
.search-job-panel__candidate-actions {
  display: flex;
  align-items: flex-start;
  justify-content: space-between;
  gap: 0.75rem;
}

.search-job-panel__chips {
  display: flex;
  flex-wrap: wrap;
  gap: 0.5rem;
}

.search-job-panel__candidate {
  border: 1px solid var(--mp-line);
  background: var(--mp-panel-soft);
}

.search-job-panel__candidate-title {
  margin: 0;
  font-size: 1rem;
}
</style>
