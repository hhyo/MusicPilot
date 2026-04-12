<template>
  <div class="page-shell">
    <VCard class="hero-card">
      <VCardText class="pa-6 stack">
        <div class="search-view__hero">
          <div>
            <p class="eyebrow">Metadata</p>
            <h2 class="section-title">搜索、识别与获取入口</h2>
            <p class="section-note">
              搜索页现在只围绕 metadata 搜索结果和统一音乐媒体解析链来组织，详情操作直接进入 SearchJob 与 Subscription。
            </p>
          </div>
          <VChip color="primary" variant="tonal">{{ form.type }}</VChip>
        </div>

        <VTabs v-model="form.type" color="primary" align-tabs="start">
          <VTab value="artist">Artist</VTab>
          <VTab value="album">Album</VTab>
          <VTab value="track">Track</VTab>
        </VTabs>

        <div class="search-view__controls">
          <VTextField
            v-model.trim="form.keyword"
            :label="placeholderText"
            prepend-inner-icon="mdi-magnify"
            @keyup.enter="runSearch(true)"
          />
          <VBtn color="primary" :loading="searching" @click="runSearch(true)">搜索</VBtn>
        </div>

        <div class="search-view__samples">
          <VChip
            v-for="sample in sampleKeywords[form.type]"
            :key="sample"
            variant="outlined"
            @click="applySample(sample)"
          >
            {{ sample }}
          </VChip>
        </div>
      </VCardText>
    </VCard>

    <VAlert
      v-if="searchError"
      type="error"
      variant="tonal"
      density="comfortable"
      :text="searchError"
    />

    <div class="split-layout">
      <VCard class="panel-card">
        <VCardText class="pa-6 stack">
          <div class="search-view__section-head">
            <div>
              <p class="eyebrow">Results</p>
              <h3 class="section-title">结构化 metadata 结果</h3>
            </div>
            <VChip v-if="result" variant="tonal" color="primary">
              {{ result.provider }}
            </VChip>
          </div>

          <template v-if="searching">
            <VSkeletonLoader type="article, article, article" />
          </template>

          <template v-else-if="result && result.items.length > 0">
            <div class="surface-grid search-view__results-grid">
              <SearchResultCard
                v-for="item in result.items"
                :key="item.id"
                :item="item"
                @view-detail="openDetail"
              />
            </div>
          </template>

          <VAlert
            v-else
            type="info"
            variant="tonal"
            density="comfortable"
            text="输入关键词后开始搜索。当前页面直接展示 metadata 搜索结果，并从详情进入搜索任务与订阅。"
          />
        </VCardText>
      </VCard>

      <SearchJobPanel
        :job="activeJob"
        :candidates="candidates"
        :loading="jobLoading"
        :error-message="jobError"
        :dispatching-candidate-id="dispatchingCandidateId"
        :dispatch-results="dispatchResults"
        :candidates-note="candidatesNote"
        @dispatch="handleDispatch"
      />
    </div>

    <MetadataDetailDrawer
      :model-value="detailVisible"
      :loading="detailLoading"
      :detail="detail"
      :error-message="detailError"
      @update:model-value="detailVisible = $event"
      @create-subscription="createSubscriptionFromDetail"
      @search-resources="createAndRunSearchJob"
    />
  </div>
</template>

<script setup lang="ts">
import { computed, reactive, ref } from 'vue';

import MetadataDetailDrawer from '@/components/MetadataDetailDrawer.vue';
import SearchJobPanel from '@/components/SearchJobPanel.vue';
import SearchResultCard from '@/components/SearchResultCard.vue';
import {
  createSearchJob,
  dispatchCandidate,
  executeSearchJob,
  fetchSearchCandidates,
} from '@/services/acquisition';
import { buildMusicMediaInputFromMetadataDetail, buildSearchJobPayload, buildSubscriptionPayloadFromMetadataDetail } from '@/services/music-media-mappers';
import { fetchMetadataDetail, searchMetadata } from '@/services/metadata';
import { createSubscription } from '@/services/subscriptions';
import type { DispatchResult, SearchCandidateDetail, SearchJobSummary } from '@/types/acquisition';
import type { EntityType, MetadataDetail, MetadataSearchData, MetadataSummary } from '@/types/metadata';

const form = reactive<{
  keyword: string;
  type: EntityType;
}>({
  keyword: '',
  type: 'artist',
});

const sampleKeywords: Record<EntityType, string[]> = {
  artist: ['Adele', 'Taylor Swift', '周杰伦'],
  album: ['25', '1989', 'Random Access Memories'],
  track: ['Hello', 'Get Lucky', '晴天'],
};

const searching = ref(false);
const searchError = ref('');
const result = ref<MetadataSearchData | null>(null);

const detailVisible = ref(false);
const detailLoading = ref(false);
const detailError = ref('');
const detail = ref<MetadataDetail | null>(null);

const activeJob = ref<SearchJobSummary | null>(null);
const candidates = ref<SearchCandidateDetail[]>([]);
const candidatesNote = ref('');
const jobLoading = ref(false);
const jobError = ref('');
const dispatchingCandidateId = ref('');
const dispatchResults = ref<Record<string, DispatchResult>>({});

const placeholderText = computed(() => {
  const placeholderMap: Record<EntityType, string> = {
    artist: '搜索艺人，例如 Adele、Taylor Swift、周杰伦',
    album: '搜索专辑，例如 25、1989、Random Access Memories',
    track: '搜索歌曲，例如 Hello、Get Lucky、晴天',
  };

  return placeholderMap[form.type];
});

function applySample(keyword: string) {
  form.keyword = keyword;
  void runSearch(true);
}

async function runSearch(resetPage: boolean) {
  void resetPage;
  if (!form.keyword.trim()) {
    searchError.value = '请输入搜索关键词。';
    result.value = null;
    return;
  }

  searching.value = true;
  searchError.value = '';
  try {
    const response = await searchMetadata({
      keyword: form.keyword.trim(),
      type: form.type,
      page: 1,
      page_size: 12,
    });
    result.value = response.data;
  } catch (error) {
    searchError.value = error instanceof Error ? error.message : '搜索失败。';
  } finally {
    searching.value = false;
  }
}

async function openDetail(item: MetadataSummary) {
  detailVisible.value = true;
  detailLoading.value = true;
  detailError.value = '';
  try {
    const response = await fetchMetadataDetail(item.entity_type, item.id);
    detail.value = response.data;
  } catch (error) {
    detail.value = null;
    detailError.value = error instanceof Error ? error.message : '详情加载失败。';
  } finally {
    detailLoading.value = false;
  }
}

async function createSubscriptionFromDetail(target: MetadataDetail) {
  await createSubscription(buildSubscriptionPayloadFromMetadataDetail(target));
}

async function createAndRunSearchJob(target: MetadataDetail) {
  jobLoading.value = true;
  jobError.value = '';
  candidates.value = [];
  dispatchResults.value = {};
  try {
    const createResponse = await createSearchJob(
      buildSearchJobPayload(buildMusicMediaInputFromMetadataDetail(target)),
    );
    const runResponse = await executeSearchJob(createResponse.data.id);
    activeJob.value = runResponse.data;

    const candidatesResponse = await fetchSearchCandidates(runResponse.data.id);
    candidates.value = candidatesResponse.data.items;
    candidatesNote.value = candidatesResponse.data.note;
  } catch (error) {
    jobError.value = error instanceof Error ? error.message : '搜索任务执行失败。';
  } finally {
    jobLoading.value = false;
  }
}

async function handleDispatch(candidate: SearchCandidateDetail) {
  dispatchingCandidateId.value = candidate.id;
  try {
    const response = await dispatchCandidate({
      result_id: candidate.id,
    });
    dispatchResults.value = {
      ...dispatchResults.value,
      [candidate.id]: response.data,
    };
  } catch (error) {
    jobError.value = error instanceof Error ? error.message : '派发失败。';
  } finally {
    dispatchingCandidateId.value = '';
  }
}
</script>

<style scoped lang="scss">
.search-view__hero,
.search-view__controls,
.search-view__section-head {
  display: flex;
  align-items: flex-start;
  justify-content: space-between;
  gap: 0.75rem;
}

.search-view__controls {
  align-items: center;
}

.search-view__samples {
  display: flex;
  flex-wrap: wrap;
  gap: 0.5rem;
}

.search-view__results-grid {
  grid-template-columns: repeat(auto-fit, minmax(260px, 1fr));
}

@media (max-width: 760px) {
  .search-view__controls,
  .search-view__hero {
    flex-direction: column;
  }
}
</style>
