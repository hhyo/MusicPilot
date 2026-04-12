<template>
  <div class="search-view">
    <section class="search-hero">
      <div>
        <p class="search-hero__eyebrow">Metadata Search</p>
        <h2>Metadata -> Query -> Job -> Candidate -> Host Adapter 收口闭环</h2>
        <p class="search-hero__description">
          当前搜索页已接通 metadata 搜索、SearchJob 与从详情创建订阅的最小闭环。search / dispatch
          会在当前接入模式下直接暴露真实 backend、adapter mode 与错误原因；organize 则在订阅页继续沿用
          MusicPilot 本地 preview 与宿主底层文件执行的双阶段闭环。真实 metadata provider 仍是下一阶段重点。
        </p>
      </div>
      <el-tag type="warning" effect="plain">
        metadata seed + host search/dispatch + music preview/apply
      </el-tag>
    </section>

    <el-alert
      v-if="latestSubscription"
      :title="`已创建订阅：${latestSubscription.target_name}（${latestSubscription.subscription_type}）`"
      type="success"
      :closable="false"
      show-icon
    />

    <section class="search-panel">
      <el-tabs v-model="form.type" class="search-panel__tabs">
        <el-tab-pane label="Artist" name="artist" />
        <el-tab-pane label="Album" name="album" />
        <el-tab-pane label="Track" name="track" />
      </el-tabs>

      <div class="search-panel__controls">
        <el-input
          v-model.trim="form.keyword"
          :placeholder="placeholderText"
          clearable
          @keyup.enter="runSearch(true)"
        />
        <el-button type="primary" :loading="searching" @click="runSearch(true)">
          搜索
        </el-button>
      </div>

      <p class="search-panel__hint">
        推荐试试：
        <button
          v-for="sample in sampleKeywords[form.type]"
          :key="sample"
          class="search-panel__sample"
          type="button"
          @click="applySample(sample)"
        >
          {{ sample }}
        </button>
      </p>
    </section>

    <section class="search-status">
      <article class="status-card">
        <span>搜索类型</span>
        <strong>{{ form.type }}</strong>
      </article>
      <article class="status-card">
        <span>当前 Provider</span>
        <strong>{{ result?.provider ?? 'mock_seed_catalog' }}</strong>
      </article>
      <article class="status-card">
        <span>结果总数</span>
        <strong>{{ result?.total ?? 0 }}</strong>
      </article>
      <article class="status-card">
        <span>分页</span>
        <strong>{{ page }} / {{ totalPages }}</strong>
      </article>
    </section>

    <section class="results-panel">
      <header class="results-panel__header">
        <div>
          <p class="results-panel__eyebrow">Search Results</p>
          <h3>结构化元数据结果</h3>
        </div>
        <el-tag v-if="result" type="info" effect="plain">
          {{ result.source_type }} / {{ result.integration_point }}
        </el-tag>
      </header>

      <el-alert
        v-if="searchError"
        :title="searchError"
        type="error"
        :closable="false"
        show-icon
      />

      <div v-else-if="searching" class="results-panel__loading">
        <el-skeleton v-for="index in 3" :key="index" animated :rows="5" />
      </div>

      <el-empty
        v-else-if="searched && result && result.items.length === 0"
        description="当前关键词在本地 seed metadata 中没有匹配结果。"
      />

      <div v-else-if="result && result.items.length > 0" class="results-grid">
        <SearchResultCard
          v-for="item in result.items"
          :key="item.id"
          :item="item"
          @view-detail="openDetail"
        />
      </div>

      <el-empty
        v-else
        description="输入关键词后开始搜索。当前阶段先返回 metadata 结果与后续订阅入口。"
      />

      <el-pagination
        v-if="result && result.total > pageSize"
        class="results-panel__pagination"
        background
        layout="prev, pager, next"
        :current-page="page"
        :page-size="pageSize"
        :total="result.total"
        @current-change="handlePageChange"
      />
    </section>

    <MetadataDetailDrawer
      v-model="detailVisible"
      :loading="detailLoading"
      :detail="detail"
      :error-message="detailError"
      @create-subscription="createSubscriptionFromDetail"
      @search-resources="createAndRunSearchJob"
    />

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
</template>

<script setup lang="ts">
import axios from 'axios';
import { computed, reactive, ref } from 'vue';
import { ElMessage } from 'element-plus';

import MetadataDetailDrawer from '@/components/MetadataDetailDrawer.vue';
import SearchResultCard from '@/components/SearchResultCard.vue';
import SearchJobPanel from '@/components/SearchJobPanel.vue';
import {
  createSearchJob,
  dispatchCandidate,
  executeSearchJob,
  fetchSearchCandidates,
} from '@/services/acquisition';
import { fetchMetadataDetail, searchMetadata } from '@/services/metadata';
import { createSubscription } from '@/services/orchestration';
import type {
  DispatchResult,
  SearchCandidateDetail,
  SearchJobSummary,
} from '@/types/acquisition';
import type {
  EntityType,
  MetadataDetail,
  MetadataSearchData,
  MetadataSummary,
} from '@/types/metadata';
import type { SubscriptionSummary } from '@/types/orchestration';

const pageSize = 6;

const form = reactive<{
  keyword: string;
  type: EntityType;
}>({
  keyword: '',
  type: 'artist',
});

const sampleKeywords: Record<EntityType, string[]> = {
  artist: ['Adele', 'Taylor', 'Daft'],
  album: ['25', '1989', 'Random'],
  track: ['Hello', 'Anti', 'Lucky'],
};

const searched = ref(false);
const searching = ref(false);
const searchError = ref('');
const result = ref<MetadataSearchData | null>(null);
const page = ref(1);

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
const latestSubscription = ref<SubscriptionSummary | null>(null);

const placeholderText = computed(() => {
  const placeholderMap: Record<EntityType, string> = {
    artist: '输入艺人名，例如 Adele、Taylor Swift',
    album: '输入专辑名，例如 25、Random Access Memories',
    track: '输入歌曲名，例如 Hello、Get Lucky',
  };

  return placeholderMap[form.type];
});

const totalPages = computed(() => {
  if (!result.value || result.value.total === 0) {
    return 1;
  }

  return Math.ceil(result.value.total / pageSize);
});

function applySample(keyword: string) {
  form.keyword = keyword;
  void runSearch(true);
}

async function runSearch(resetPage: boolean) {
  const keyword = form.keyword.trim();

  if (!keyword) {
    searched.value = false;
    result.value = null;
    searchError.value = '请输入搜索关键词。';
    return;
  }

  if (resetPage) {
    page.value = 1;
  }

  searching.value = true;
  searched.value = true;
  searchError.value = '';

  try {
    const response = await searchMetadata({
      keyword,
      type: form.type,
      page: page.value,
      page_size: pageSize,
    });

    if (!response.success) {
      throw new Error(response.message);
    }

    result.value = response.data;
  } catch (error) {
    result.value = null;
    searchError.value = resolveErrorMessage(error, '元数据搜索失败，请确认后端服务已启动。');
  } finally {
    searching.value = false;
  }
}

async function openDetail(item: MetadataSummary) {
  detailVisible.value = true;
  detailLoading.value = true;
  detailError.value = '';
  detail.value = null;

  try {
    const response = await fetchMetadataDetail(item.entity_type, item.id);

    if (!response.success) {
      throw new Error(response.message);
    }

    detail.value = response.data;
  } catch (error) {
    detailError.value = resolveErrorMessage(error, '详情加载失败，请稍后重试。');
  } finally {
    detailLoading.value = false;
  }
}

async function createAndRunSearchJob(metadataDetail: MetadataDetail) {
  jobLoading.value = true;
  jobError.value = '';
  candidates.value = [];
  candidatesNote.value = '';
  dispatchResults.value = {};

  try {
    const created = await createSearchJob({
      query_source_type: metadataDetail.entity_type,
      query_source_id: metadataDetail.id,
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

    activeJob.value = executed.data;

    const results = await fetchSearchCandidates(executed.data.id);

    if (!results.success) {
      throw new Error(results.message);
    }

    candidates.value = results.data.items;
    candidatesNote.value = results.data.note;
  } catch (error) {
    activeJob.value = null;
    candidates.value = [];
    jobError.value = resolveErrorMessage(error, '搜索任务执行失败，请确认后端服务已启动。');
  } finally {
    jobLoading.value = false;
  }
}

async function createSubscriptionFromDetail(metadataDetail: MetadataDetail) {
  try {
    const response = await createSubscription({
      subscription_type: metadataDetail.entity_type,
      target_id: metadataDetail.id,
      target_name: metadataDetail.title,
      target_entity_type: metadataDetail.entity_type,
      mode: 'manual',
    });

    if (!response.success) {
      throw new Error(response.message);
    }

    latestSubscription.value = response.data;
    ElMessage.success(`已创建 ${response.data.target_name} 的订阅。`);
  } catch (error) {
    ElMessage.error(resolveErrorMessage(error, '创建订阅失败，请稍后重试。'));
  }
}

async function handleDispatch(candidate: SearchCandidateDetail) {
  dispatchingCandidateId.value = candidate.id;

  try {
    const response = await dispatchCandidate({
      result_id: candidate.id,
      downloader_id: 'mock-downloader',
      save_path_policy: 'auto',
      manual_confirm: true,
    });

    if (!response.success) {
      throw new Error(response.message);
    }

    dispatchResults.value = {
      ...dispatchResults.value,
      [candidate.id]: response.data,
    };
    candidate.dispatch_status = response.data.dispatch_status;
    if (activeJob.value) {
      activeJob.value.status = 'dispatched';
    }
  } catch (error) {
    jobError.value = resolveErrorMessage(error, '派发失败，请稍后重试。');
  } finally {
    dispatchingCandidateId.value = '';
  }
}

function handlePageChange(nextPage: number) {
  page.value = nextPage;
  void runSearch(false);
}

function resolveErrorMessage(error: unknown, fallback: string) {
  if (axios.isAxiosError(error)) {
    return error.response?.data?.message ?? error.message ?? fallback;
  }

  if (error instanceof Error) {
    return error.message;
  }

  return fallback;
}
</script>

<style scoped lang="scss">
.search-view {
  display: grid;
  gap: 1.25rem;
}

.search-hero,
.search-panel,
.results-panel {
  padding: 1.35rem;
  border: 1px solid var(--mp-line);
  border-radius: 28px;
  background: rgba(255, 255, 255, 0.82);
  box-shadow: 0 18px 40px rgba(52, 37, 122, 0.06);
}

.search-hero {
  display: flex;
  align-items: flex-start;
  justify-content: space-between;
  gap: 1rem;
}

.search-hero h2,
.search-hero__description,
.results-panel__header h3,
.results-panel__eyebrow {
  margin: 0;
}

.search-hero__eyebrow,
.results-panel__eyebrow {
  color: var(--mp-accent);
  font-size: 0.82rem;
  font-weight: 700;
  letter-spacing: 0.08em;
  text-transform: uppercase;
}

.search-hero__description {
  max-width: 72ch;
  margin-top: 0.55rem;
  color: var(--mp-muted);
  line-height: 1.8;
}

.search-panel {
  display: grid;
  gap: 1rem;
}

.search-panel__controls {
  display: grid;
  grid-template-columns: minmax(0, 1fr) auto;
  gap: 0.8rem;
}

.search-panel__hint {
  margin: 0;
  color: var(--mp-muted);
}

.search-panel__sample {
  padding: 0;
  border: none;
  background: none;
  color: var(--mp-accent);
  cursor: pointer;
  font-weight: 700;
}

.search-status {
  display: grid;
  grid-template-columns: repeat(4, minmax(0, 1fr));
  gap: 1rem;
}

.status-card {
  display: grid;
  gap: 0.45rem;
  padding: 1rem 1.1rem;
  border: 1px solid var(--mp-line);
  border-radius: 20px;
  background: rgba(255, 255, 255, 0.78);
}

.status-card span {
  color: var(--mp-muted);
  font-size: 0.88rem;
}

.status-card strong {
  font-size: 1.15rem;
}

.results-panel {
  display: grid;
  gap: 1rem;
}

.results-panel__header {
  display: flex;
  align-items: flex-start;
  justify-content: space-between;
  gap: 1rem;
}

.results-grid,
.results-panel__loading {
  display: grid;
  gap: 1rem;
  grid-template-columns: repeat(2, minmax(0, 1fr));
}

.results-panel__pagination {
  justify-self: flex-end;
}

@media (max-width: 960px) {
  .search-status,
  .results-grid {
    grid-template-columns: 1fr;
  }
}

@media (max-width: 720px) {
  .search-hero,
  .results-panel__header {
    flex-direction: column;
  }

  .search-panel__controls {
    grid-template-columns: 1fr;
  }
}
</style>
