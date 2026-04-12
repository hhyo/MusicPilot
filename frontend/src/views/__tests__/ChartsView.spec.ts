import { flushPromises, mount } from '@vue/test-utils';
import { beforeEach, describe, expect, it, vi } from 'vitest';

const {
  fetchChartProviders,
  fetchCharts,
  fetchChartDetail,
  subscribeFromChartEntry,
  resolveMusicMediaDetail,
  createSubscription,
  createSearchJob,
} = vi.hoisted(() => ({
  fetchChartProviders: vi.fn(),
  fetchCharts: vi.fn(),
  fetchChartDetail: vi.fn(),
  subscribeFromChartEntry: vi.fn(),
  resolveMusicMediaDetail: vi.fn(),
  createSubscription: vi.fn(),
  createSearchJob: vi.fn(),
}));

vi.mock('@/services/discovery', () => ({
  fetchChartProviders,
  fetchCharts,
  fetchChartDetail,
  subscribeFromChartEntry,
}));

vi.mock('@/services/music-media', () => ({
  resolveMusicMediaDetail,
}));

vi.mock('@/services/subscriptions', () => ({
  createSubscription,
}));

vi.mock('@/services/acquisition', () => ({
  createSearchJob,
}));

vi.mock('@/components/MetadataDetailDrawer.vue', () => ({
  default: {
    props: ['modelValue', 'detail', 'loading', 'errorMessage'],
    template: '<div class="metadata-drawer-stub">{{ detail?.title }}</div>',
  },
}));

import ChartsView from '@/views/ChartsView.vue';

const chart = {
  id: 'rss-feed-1',
  chart_source: 'rss_feed',
  chart_name: '网易云热歌榜',
  chart_type: 'track',
  item_count: 2,
  updated_at: '2026-04-12T10:00:00Z',
  mock: false,
  note: 'live',
  summary: '热门歌曲发现入口',
  chart_group: 'tracks',
  chart_scope: 'sitewide',
  freshness_label: 'daily',
  supports_subscription: true,
};

const entry = {
  entry: {
    item_id: 'entry-1',
    chart_id: 'rss-feed-1',
    chart_source: 'rss_feed',
    chart_name: '网易云热歌榜',
    rank: 1,
    item_type: 'track',
    target_id: 'track-1',
    target_name: 'Hello',
    subtitle: 'Adele',
    provider: 'rss_feed',
    source_type: 'rss_feed',
    target_payload: { provider: 'musicbrainz', provider_id: 'track-1' },
    mock: false,
    note: 'ok',
  },
  media_input: {
    entity_hint: 'track',
    source_kind: 'discovery',
    title: 'Hello',
    subtitle: 'Adele',
    artist_names: ['Adele'],
    album_title: '25',
    album_artist_names: ['Adele'],
    release_date: null,
    year: 2015,
    track_number: null,
    disc_number: null,
    external_refs: {},
    source_context: {},
    raw_context: {},
  },
  meta_base: {
    entity_type: 'track',
    canonical_title: 'Hello',
    canonical_artist_names: ['Adele'],
    canonical_album_title: '25',
    canonical_album_artist_names: ['Adele'],
    canonical_release_date: null,
    canonical_year: 2015,
    track_number: null,
    disc_number: null,
    alias_titles: [],
    alias_artist_names: [],
    alias_album_titles: [],
    featuring_artist_names: [],
    external_refs: {},
    source_refs: {},
    evidence: [],
    normalization_notes: [],
    confidence_hint: 0.98,
  },
  entry_summary: '统一音乐媒体解析链已准备好该条目的识别输入。',
  badges: ['track'],
  highlight_reason: 'hero',
  recognition_assessment: {
    state: 'ready',
    note: '可直接进入 detail 解析。',
  },
};

beforeEach(() => {
  fetchChartProviders.mockResolvedValue({
    data: [{ id: 'rss_feed', display_name: 'RSS Feed', chart_source: 'rss_feed', enabled: true, mock: false, note: '', integration_point: 'runtime' }],
  });
  fetchCharts.mockResolvedValue({ data: { items: [chart], total: 1, mock: false, note: '', integration_point: 'runtime' } });
  fetchChartDetail.mockResolvedValue({
    data: {
      chart,
      items: [],
      item_count: 1,
      mock: false,
      note: '',
      integration_point: 'runtime',
      hero_entry: entry,
      summary_stats: { items: 1 },
      entry_groups: [{ group_key: 'tracks', group_label: 'Tracks', items: [entry] }],
      recognition_summary: { ready: 1, partial: 0, insufficient: 0 },
    },
  });
  resolveMusicMediaDetail.mockResolvedValue({
    data: {
      base: entry.meta_base,
      assessment: entry.recognition_assessment,
      media: {
        entity_type: 'track',
        provider: 'musicbrainz',
        provider_id: 'track-1',
        title: 'Hello',
        artist_names: ['Adele'],
        album_title: '25',
        album_artist_names: ['Adele'],
        release_date: null,
        year: 2015,
        track_number: null,
        disc_number: null,
        related_artist_ids: [],
        related_album_id: null,
        related_track_ids: [],
        external_refs: {},
        match_confidence: 0.99,
        match_strategy: 'provider_ref',
        match_evidence: [],
        diagnostics: [],
        cover_url: null,
        disambiguation: null,
        release_context: {},
      },
      detail: {
        entity_type: 'track',
        id: 'track-1',
        title: 'Hello',
        artist_name: 'Adele',
        album_title: '25',
        aliases: [],
        year: 2015,
        release_type: 'single',
        genres: [],
        external_ids: {},
        provider: 'musicbrainz',
        source_type: 'runtime',
        mock: false,
        note: 'detail loaded',
        label_names: [],
        secondary_types: [],
        primary_release_types: [],
        featured_albums: [],
        featured_singles: [],
        featured_other_releases: [],
        featured_release_group_counts: {},
        metadata_stage: 'resolved',
        integration_point: 'runtime',
        related_artists: [],
        related_albums: [],
        tracks: [],
        todo: [],
      },
    },
  });
});

function mountView() {
  return mount(ChartsView, {
    global: {
      stubs: {
        VCard: { template: '<div><slot /></div>' },
        VCardText: { template: '<div><slot /></div>' },
        VAlert: { props: ['text'], template: '<div>{{ text }}</div>' },
        VBtn: { emits: ['click'], template: '<button @click="$emit(\'click\', $event)"><slot /></button>' },
        VChip: { template: '<span><slot /></span>' },
        VChipGroup: { template: '<div><slot /></div>' },
        VSkeletonLoader: { template: '<div>loading</div>' },
      },
    },
  });
}

describe('ChartsView', () => {
  it('loads charts and chart detail using the new discovery contract', async () => {
    const wrapper = mountView();
    await flushPromises();

    expect(fetchCharts).toHaveBeenCalledTimes(1);
    expect(fetchChartDetail).toHaveBeenCalledWith('rss-feed-1');
    expect(wrapper.text()).toContain('榜单发现与媒体识别');
    expect(wrapper.text()).toContain('网易云热歌榜');
    expect(wrapper.text()).toContain('统一音乐媒体解析链已准备好该条目的识别输入。');
  });

  it('opens chart entry detail through media resolve detail', async () => {
    const wrapper = mountView();
    await flushPromises();

    const buttons = wrapper.findAll('button');
    await buttons.find((button) => button.text().includes('打开详情'))!.trigger('click');
    await flushPromises();

    expect(resolveMusicMediaDetail).toHaveBeenCalled();
    expect(wrapper.text()).toContain('Hello');
  });
});
