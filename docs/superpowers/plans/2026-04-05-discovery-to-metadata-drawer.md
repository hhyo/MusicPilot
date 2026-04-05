# Discovery To Metadata Drawer Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** 让 discovery 榜单条目能够通过稳定的 `DiscoveryTarget` 转化层打开现有 metadata 详情抽屉，形成“浏览 discovery -> 下钻 metadata -> 从详情行动”的真实产品交互。

**Architecture:** 复用现有 `MetadataDetailDrawer` 和 metadata API，不新增详情路由页。Charts 页面只维护一个很薄的 discovery->metadata 桥接层、抽屉状态和激活 entry 状态；provider 原始字段继续被隔离在 `DiscoveryTarget` 之后。

**Tech Stack:** Vue 3、Element Plus、TypeScript、Vitest、@vue/test-utils、Vite

---

## File Structure

- Create: `frontend/src/services/discovery-metadata.ts`
  - 只负责把 `DiscoveryTarget` 转成 metadata detail 请求，不允许泄漏 provider 原始 payload
- Create: `frontend/src/views/__tests__/ChartsView.spec.ts`
  - 覆盖 discovery entry 打开 drawer、not-ready guard、订阅按钮不串行为、切换榜单清空激活态
- Modify: `frontend/vite.config.ts`
  - 增加 Vitest 基础配置，保证前端交互测试能以 jsdom 跑起来
- Modify: `frontend/src/views/ChartsView.vue`
  - 接入 metadata drawer 状态、active entry 状态、entry click 交互、inline warning
- Modify: `frontend/src/types/orchestration.ts`
  - 如果测试/组件需要更清晰的前端类型，可补 discovery 视图字段注释或类型导出，不扩接口语义
- Modify: `docs/28_项目整体任务盘点与执行路线.md`
  - 记录 discovery 第一轮产品化后的下一步：discovery entry 已可进入 metadata detail
- Modify: `README.md`
  - 收口 charts/discovery 当前真实交互

### Task 1: 建 discovery->metadata 桥接层并补前端测试基线

**Files:**
- Create: `frontend/src/services/discovery-metadata.ts`
- Create: `frontend/src/views/__tests__/ChartsView.spec.ts`
- Modify: `frontend/vite.config.ts`
- Test: `frontend/src/views/__tests__/ChartsView.spec.ts`

- [ ] **Step 1: 写桥接层的 failing test**

```ts
import { describe, expect, it, vi } from 'vitest';

import type { DiscoveryTarget } from '@/types/orchestration';
import { fetchDiscoveryTargetDetail } from '@/services/discovery-metadata';
import * as metadataService from '@/services/metadata';

describe('fetchDiscoveryTargetDetail', () => {
  it('uses target_kind and provider_id to request metadata detail', async () => {
    const target: DiscoveryTarget = {
      target_kind: 'track',
      provider: 'musicbrainz',
      provider_id: 'recording-123',
      display_title: 'Hello',
      display_subtitle: 'Adele',
      source_context: {
        chart_source: 'listenbrainz',
        chart_id: 'chart-1',
        chart_name: 'Top Tracks',
        rank: 1,
        chart_type: 'track',
      },
      conversion_ready: true,
      conversion_note: null,
      discovery_badges: ['top_track'],
    };

    const spy = vi
      .spyOn(metadataService, 'fetchMetadataDetail')
      .mockResolvedValue({ success: true, code: 'OK', message: 'ok', data: {} as never });

    await fetchDiscoveryTargetDetail(target);

    expect(spy).toHaveBeenCalledWith('track', 'recording-123');
  });

  it('throws when conversion_ready is false', async () => {
    const target: DiscoveryTarget = {
      target_kind: 'artist',
      provider: 'musicbrainz',
      provider_id: 'artist-1',
      display_title: 'Unknown Artist',
      display_subtitle: null,
      source_context: {
        chart_source: 'listenbrainz',
        chart_id: 'chart-1',
        chart_name: 'Top Artists',
        rank: 2,
        chart_type: 'artist',
      },
      conversion_ready: false,
      conversion_note: 'provider id missing',
      discovery_badges: [],
    };

    await expect(fetchDiscoveryTargetDetail(target)).rejects.toThrow('provider id missing');
  });
});
```

- [ ] **Step 2: 跑 test，确认当前失败**

Run: `cd frontend && PATH=/Users/lihuanhuan/.npm-global/bin:$PATH pnpm test -- --run frontend/src/views/__tests__/ChartsView.spec.ts`

Expected:
- 失败，原因是 `@/services/discovery-metadata` 不存在
- 或 Vitest 还没有 jsdom/test config

- [ ] **Step 3: 写最小测试基础设施和桥接实现**

```ts
// frontend/src/services/discovery-metadata.ts
import { fetchMetadataDetail } from '@/services/metadata';
import type { DiscoveryTarget } from '@/types/orchestration';

export async function fetchDiscoveryTargetDetail(target: DiscoveryTarget) {
  if (!target.conversion_ready) {
    throw new Error(target.conversion_note || '当前榜单项暂不支持 metadata detail。');
  }

  return fetchMetadataDetail(target.target_kind, target.provider_id);
}
```

```ts
// frontend/vite.config.ts
export default defineConfig({
  plugins: [vue()],
  resolve: {
    alias: {
      '@': fileURLToPath(new URL('./src', import.meta.url)),
    },
  },
  test: {
    environment: 'jsdom',
    globals: true,
    css: true,
  },
});
```

- [ ] **Step 4: 跑 test，确认转绿**

Run: `cd frontend && PATH=/Users/lihuanhuan/.npm-global/bin:$PATH pnpm test -- --run frontend/src/views/__tests__/ChartsView.spec.ts`

Expected:
- 通过桥接层测试
- 仍然可能缺 ChartsView 组件测试，留给下一任务继续补

- [ ] **Step 5: Commit**

```bash
git add frontend/src/services/discovery-metadata.ts frontend/src/views/__tests__/ChartsView.spec.ts frontend/vite.config.ts
git commit -m "test: add discovery metadata bridge tests"
```

### Task 2: 在 ChartsView 中接入 MetadataDetailDrawer

**Files:**
- Modify: `frontend/src/views/ChartsView.vue`
- Modify: `frontend/src/components/MetadataDetailDrawer.vue`
- Test: `frontend/src/views/__tests__/ChartsView.spec.ts`

- [ ] **Step 1: 先写 ChartsView 的 failing tests**

```ts
import { mount, flushPromises } from '@vue/test-utils';
import { describe, expect, it, vi } from 'vitest';

import ChartsView from '@/views/ChartsView.vue';

vi.mock('@/services/orchestration', () => ({
  fetchChartProviders: vi.fn().mockResolvedValue({
    success: true,
    data: [{ id: 'listenbrainz', chart_source: 'listenbrainz', display_name: 'ListenBrainz', enabled: true, mock: false, note: '', integration_point: 'runtime' }],
  }),
  fetchCharts: vi.fn().mockResolvedValue({
    success: true,
    data: {
      items: [{
        id: 'chart-1',
        chart_source: 'listenbrainz',
        chart_name: 'Top Tracks',
        chart_type: 'track',
        item_count: 1,
        updated_at: '2026-04-05T10:00:00Z',
        mock: false,
        note: 'live',
        summary: 'summary',
        chart_group: 'Tracks',
        chart_scope: 'sitewide',
        freshness_label: 'weekly',
        supports_subscription: true,
      }],
      total: 1,
      mock: false,
      note: '',
      integration_point: 'runtime',
    },
  }),
  fetchChartDetail: vi.fn().mockResolvedValue({
    success: true,
    data: {
      chart: {
        id: 'chart-1',
        chart_source: 'listenbrainz',
        chart_name: 'Top Tracks',
        chart_type: 'track',
        item_count: 1,
        updated_at: '2026-04-05T10:00:00Z',
        mock: false,
        note: 'live',
        summary: 'summary',
        chart_group: 'Tracks',
        chart_scope: 'sitewide',
        freshness_label: 'weekly',
        supports_subscription: true,
      },
      items: [],
      item_count: 1,
      mock: false,
      note: '',
      integration_point: 'runtime',
      hero_entry: {
        entry: {
          item_id: 'entry-1',
          chart_id: 'chart-1',
          chart_source: 'listenbrainz',
          chart_name: 'Top Tracks',
          rank: 1,
          item_type: 'track',
          target_id: 'recording-123',
          target_name: 'Hello',
          provider: 'musicbrainz',
          source_type: 'runtime',
          mock: false,
          note: '',
        },
        target: {
          target_kind: 'track',
          provider: 'musicbrainz',
          provider_id: 'recording-123',
          display_title: 'Hello',
          display_subtitle: 'Adele',
          source_context: {
            chart_source: 'listenbrainz',
            chart_id: 'chart-1',
            chart_name: 'Top Tracks',
            rank: 1,
            chart_type: 'track',
          },
          conversion_ready: true,
          conversion_note: null,
          discovery_badges: ['top_track'],
        },
        entry_summary: 'summary',
        badges: ['top_track'],
      },
      summary_stats: { items: 1 },
      entry_groups: [],
      conversion_summary: { ready: 1, not_ready: 0 },
    },
  }),
  subscribeFromChartEntry: vi.fn(),
}));

vi.mock('@/services/discovery-metadata', () => ({
  fetchDiscoveryTargetDetail: vi.fn().mockResolvedValue({
    success: true,
    data: {
      id: 'recording-123',
      entity_type: 'track',
      title: 'Hello',
      artist_name: 'Adele',
      provider: 'musicbrainz',
      source_type: 'runtime',
      note: 'detail',
      integration_point: 'runtime',
      todo: [],
      aliases: [],
      genres: [],
      related_artists: [],
      related_albums: [],
      featured_albums: [],
      featured_singles: [],
      featured_other_releases: [],
      featured_release_group_counts: {},
      tracks: [],
      external_ids: {},
      primary_release_types: [],
      secondary_types: [],
      label_names: [],
    },
  }),
}));

describe('ChartsView discovery detail drawer', () => {
  it('opens metadata drawer from hero entry click', async () => {
    const wrapper = mount(ChartsView);
    await flushPromises();

    await wrapper.get('[data-test=\"discovery-hero-entry\"]').trigger('click');
    await flushPromises();

    expect(wrapper.findComponent({ name: 'MetadataDetailDrawer' }).props('modelValue')).toBe(true);
    expect(wrapper.html()).toContain('Hello');
  });
});
```

- [ ] **Step 2: 跑 test，确认当前失败**

Run: `cd frontend && PATH=/Users/lihuanhuan/.npm-global/bin:$PATH pnpm test -- --run frontend/src/views/__tests__/ChartsView.spec.ts`

Expected:
- 失败，因为 `ChartsView` 还没有 drawer 状态、click handler、data-test 钩子

- [ ] **Step 3: 写最小实现**

```ts
// ChartsView.vue script setup additions
import MetadataDetailDrawer from '@/components/MetadataDetailDrawer.vue';
import { fetchDiscoveryTargetDetail } from '@/services/discovery-metadata';
import type { MetadataDetail } from '@/types/metadata';
import type { DiscoveryEntryView } from '@/types/orchestration';

const metadataDrawerOpen = ref(false);
const metadataDetailLoading = ref(false);
const metadataDetailError = ref('');
const metadataDetail = ref<MetadataDetail | null>(null);
const activeDiscoveryEntryId = ref('');
const discoveryWarningMessage = ref('');

async function openDiscoveryMetadata(item: DiscoveryEntryView) {
  activeDiscoveryEntryId.value = item.entry.item_id;
  discoveryWarningMessage.value = '';

  if (!item.target.conversion_ready) {
    metadataDrawerOpen.value = false;
    metadataDetail.value = null;
    metadataDetailError.value = '';
    discoveryWarningMessage.value = item.target.conversion_note || '当前榜单项暂不支持 metadata detail。';
    ElMessage.warning(discoveryWarningMessage.value);
    return;
  }

  metadataDrawerOpen.value = true;
  metadataDetailLoading.value = true;
  metadataDetailError.value = '';
  metadataDetail.value = null;

  try {
    const response = await fetchDiscoveryTargetDetail(item.target);
    if (!response.success) {
      throw new Error(response.message);
    }
    metadataDetail.value = response.data;
  } catch (error) {
    metadataDetailError.value = resolveErrorMessage(error, 'metadata detail 加载失败。');
  } finally {
    metadataDetailLoading.value = false;
  }
}
```

```vue
<!-- ChartsView.vue template additions -->
<section v-if="discoveryWarningMessage" class="chart-detail-panel__notice">
  <el-alert
    :title="discoveryWarningMessage"
    type="warning"
    :closable="false"
    show-icon
  />
</section>

<section
  v-if="selectedChart.hero_entry"
  class="hero-entry-card"
  :class="{ 'hero-entry-card--active': activeDiscoveryEntryId === selectedChart.hero_entry.entry.item_id }"
  data-test="discovery-hero-entry"
  @click="void openDiscoveryMetadata(selectedChart.hero_entry)"
>
```

```vue
<MetadataDetailDrawer
  v-model="metadataDrawerOpen"
  :loading="metadataDetailLoading"
  :detail="metadataDetail"
  :error-message="metadataDetailError"
  @create-subscription="handleCreateSubscriptionFromMetadata"
  @search-resources="handleSearchResourcesFromMetadata"
/>
```

- [ ] **Step 4: 继续补测试并转绿**

Add tests for:
- not-ready entry only shows warning and does not call fetch
- subscribe button `.stop` keeps current subscribe behavior
- changing chart clears `activeDiscoveryEntryId`, `metadataDrawerOpen`, `metadataDetail`

Run:
- `cd frontend && PATH=/Users/lihuanhuan/.npm-global/bin:$PATH pnpm test -- --run frontend/src/views/__tests__/ChartsView.spec.ts`
- `cd frontend && PATH=/Users/lihuanhuan/.npm-global/bin:$PATH pnpm test -- --run`

Expected:
- discovery drawer tests pass
- no regression in other frontend tests (if none, Vitest exits clean)

- [ ] **Step 5: Commit**

```bash
git add frontend/src/views/ChartsView.vue frontend/src/components/MetadataDetailDrawer.vue frontend/src/views/__tests__/ChartsView.spec.ts
git commit -m "feat: open metadata drawer from discovery entries"
```

### Task 3: 做 UI/UX 收口、真实截图与文档同步

**Files:**
- Modify: `README.md`
- Modify: `docs/28_项目整体任务盘点与执行路线.md`
- Optional Modify: `frontend/src/views/ChartsView.vue`
- Artifact: screenshot images under `.tmp/` or another ignored directory

- [ ] **Step 1: 写文档更新**

```md
## Discovery -> Metadata

- 榜单 hero entry 与分组 entry 现在都可通过 `DiscoveryTarget` 打开现有 metadata detail drawer
- artist / album / track 三类 discovery target 共用同一条 metadata detail 入口
- 当前尚未实现 discovery -> search 自动转化；本轮只做 detail 下钻
```

- [ ] **Step 2: 跑完整验证**

Run:
- `cd backend && .venv/bin/python -m unittest discover -s tests`
- `cd frontend && PATH=/Users/lihuanhuan/.npm-global/bin:$PATH pnpm build`
- `cd /Users/lihuanhuan/PycharmProjects/MusicPilot && python3 scripts/package_plugin.py`

Expected:
- backend tests all pass
- frontend build passes
- plugin runtime packaging succeeds

- [ ] **Step 3: 采集真实截图**

Use a browser automation step to capture:
- charts list page with discovery cards
- chart detail with active hero entry
- metadata detail drawer opened from discovery artist or track entry

Save screenshots under an ignored temp path, for example:

```bash
mkdir -p /Users/lihuanhuan/PycharmProjects/MusicPilot/.tmp/discovery-metadata-drawer
```

- [ ] **Step 4: Commit**

```bash
git add README.md docs/28_项目整体任务盘点与执行路线.md
git commit -m "docs: record discovery metadata detail flow"
```
