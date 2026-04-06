import { flushPromises, mount } from '@vue/test-utils';
import { beforeEach, describe, expect, it, vi } from 'vitest';

const {
  fetchChartProviders,
  fetchCharts,
  fetchChartDetail,
  subscribeFromChartEntry,
  fetchDiscoveryTargetDetail,
  createSubscription,
  createSearchJob,
  executeSearchJob,
  elMessageSuccess,
  elMessageWarning,
} = vi.hoisted(() => ({
  fetchChartProviders: vi.fn(),
  fetchCharts: vi.fn(),
  fetchChartDetail: vi.fn(),
  subscribeFromChartEntry: vi.fn(),
  fetchDiscoveryTargetDetail: vi.fn(),
  createSubscription: vi.fn(),
  createSearchJob: vi.fn(),
  executeSearchJob: vi.fn(),
  elMessageSuccess: vi.fn(),
  elMessageWarning: vi.fn(),
}));

vi.mock('@/services/orchestration', () => ({
  fetchChartProviders,
  fetchCharts,
  fetchChartDetail,
  subscribeFromChartEntry,
  createSubscription,
}));

vi.mock('@/services/discovery-metadata', () => ({
  fetchDiscoveryTargetDetail,
}));

vi.mock('@/services/acquisition', () => ({
  createSearchJob,
  executeSearchJob,
}));

vi.mock('element-plus', async () => {
  const actual = await vi.importActual<typeof import('element-plus')>('element-plus');
  return {
    ...actual,
    ElMessage: {
      success: elMessageSuccess,
      warning: elMessageWarning,
      error: vi.fn(),
    },
  };
});

import ChartsView from '@/views/ChartsView.vue';

const chartListResponse = {
  success: true,
  data: {
    items: [
      {
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
      {
        id: 'chart-2',
        chart_source: 'listenbrainz',
        chart_name: 'Top Artists',
        chart_type: 'artist',
        item_count: 1,
        updated_at: '2026-04-05T11:00:00Z',
        mock: false,
        note: 'live',
        summary: 'artist summary',
        chart_group: 'Artists',
        chart_scope: 'sitewide',
        freshness_label: 'weekly',
        supports_subscription: true,
      },
    ],
    total: 2,
    mock: false,
    note: '',
    integration_point: 'runtime',
  },
};

const artistDetailResponse = {
  success: true,
  data: {
    chart: chartListResponse.data.items[1],
    items: [],
    item_count: 1,
    mock: false,
    note: '',
    integration_point: 'runtime',
    hero_entry: {
      entry: {
        item_id: 'artist-entry-1',
        chart_id: 'chart-2',
        chart_source: 'listenbrainz',
        chart_name: 'Top Artists',
        rank: 1,
        item_type: 'artist',
        target_id: 'artist-123',
        target_name: 'Adele',
        provider: 'musicbrainz',
        source_type: 'runtime',
        mock: false,
        note: '',
      },
      target: {
        target_kind: 'artist',
        provider: 'musicbrainz',
        provider_id: 'artist-123',
        display_title: 'Adele',
        display_subtitle: 'UK',
        source_context: {
          chart_source: 'listenbrainz',
          chart_id: 'chart-2',
          chart_name: 'Top Artists',
          rank: 1,
          chart_type: 'artist',
        },
        conversion_ready: true,
        conversion_note: null,
        resolution_mode: 'direct_id',
        resolution_hints: {},
        discovery_badges: ['top_artist'],
      },
      entry_summary: 'artist summary',
      badges: ['top_artist'],
    },
    summary_stats: { items: 1 },
    entry_groups: [],
    conversion_summary: { ready: 1, not_ready: 0 },
  },
};

const readyDetailResponse = {
  success: true,
  data: {
    chart: chartListResponse.data.items[0],
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
        resolution_mode: 'direct_id',
        resolution_hints: {},
        discovery_badges: ['top_track'],
      },
      entry_summary: 'summary',
      badges: ['top_track'],
    },
    summary_stats: { items: 1 },
    entry_groups: [
      {
        group_key: 'tracks',
        group_label: 'Tracks',
        items: [
          {
            entry: {
              item_id: 'entry-2',
              chart_id: 'chart-1',
              chart_source: 'listenbrainz',
              chart_name: 'Top Tracks',
              rank: 2,
              item_type: 'track',
              target_id: 'recording-456',
              target_name: 'Skyfall',
              provider: 'musicbrainz',
              source_type: 'runtime',
              mock: false,
              note: '',
            },
            target: {
              target_kind: 'track',
              provider: 'musicbrainz',
              provider_id: 'recording-456',
              display_title: 'Skyfall',
              display_subtitle: 'Adele',
              source_context: {
                chart_source: 'listenbrainz',
                chart_id: 'chart-1',
                chart_name: 'Top Tracks',
                rank: 2,
                chart_type: 'track',
              },
              conversion_ready: false,
              conversion_note: '需要补充 provider id',
              resolution_mode: 'direct_id',
              resolution_hints: {},
              discovery_badges: [],
            },
            entry_summary: 'summary',
            badges: ['top_track'],
          },
        ],
      },
    ],
    conversion_summary: { ready: 1, not_ready: 1 },
  },
};

const rssChartListResponse = {
  success: true,
  data: {
    items: [
      {
        id: 'rss-feed-feed-1',
        chart_source: 'rss_feed',
        chart_name: '网易云喜欢',
        chart_type: 'track',
        item_count: 1,
        updated_at: '2026-04-05T10:00:00Z',
        mock: false,
        note: 'rss',
        summary: 'summary',
        chart_group: 'tracks',
        chart_scope: 'liked',
        freshness_label: 'rss-feed',
        supports_subscription: true,
      },
    ],
    total: 1,
    mock: false,
    note: '',
    integration_point: 'runtime',
  },
};

const rssDetailResponse = {
  success: true,
  data: {
    chart: rssChartListResponse.data.items[0],
    items: [],
    item_count: 1,
    mock: false,
    note: '',
    integration_point: 'runtime',
    hero_entry: {
      entry: {
        item_id: 'rss-entry-1',
        chart_id: 'rss-feed-feed-1',
        chart_source: 'rss_feed',
        chart_name: '网易云喜欢',
        rank: 1,
        item_type: 'track',
        target_id: '',
        target_name: 'Hello',
        provider: 'rss_feed',
        source_type: 'rss_feed/netease_playlist_tracks',
        target_payload: {
          title: 'Hello',
          artist_name: 'Adele',
          album_title: '25',
        },
        mock: false,
        note: '',
      },
      target: {
        target_kind: 'track',
        provider: 'musicbrainz',
        provider_id: '',
        display_title: 'Hello',
        display_subtitle: 'Adele',
        source_context: {
          chart_source: 'rss_feed',
          chart_id: 'rss-feed-feed-1',
          chart_name: '网易云喜欢',
          rank: 1,
          chart_type: 'track',
        },
        conversion_ready: true,
        conversion_note: null,
        resolution_mode: 'search_lookup',
        resolution_hints: {
          title: 'Hello',
          artist_name: 'Adele',
          album_title: '25',
        },
        discovery_badges: ['rss'],
      },
      entry_summary: 'summary',
      badges: ['rss'],
    },
    summary_stats: { items: 1 },
    entry_groups: [
      {
        group_key: 'tracks',
        group_label: 'Tracks',
        items: [
          {
            entry: {
              item_id: 'rss-entry-1',
              chart_id: 'rss-feed-feed-1',
              chart_source: 'rss_feed',
              chart_name: '网易云喜欢',
              rank: 1,
              item_type: 'track',
              target_id: '',
              target_name: 'Hello',
              provider: 'rss_feed',
              source_type: 'rss_feed/netease_playlist_tracks',
              target_payload: {
                title: 'Hello',
                artist_name: 'Adele',
                album_title: '25',
              },
              mock: false,
              note: '',
            },
            target: {
              target_kind: 'track',
              provider: 'musicbrainz',
              provider_id: '',
              display_title: 'Hello',
              display_subtitle: 'Adele',
              source_context: {
                chart_source: 'rss_feed',
                chart_id: 'rss-feed-feed-1',
                chart_name: '网易云喜欢',
                rank: 1,
                chart_type: 'track',
              },
              conversion_ready: true,
              conversion_note: null,
              resolution_mode: 'search_lookup',
              resolution_hints: {
                title: 'Hello',
                artist_name: 'Adele',
                album_title: '25',
              },
              discovery_badges: ['rss'],
            },
            entry_summary: 'summary',
            badges: ['rss'],
          },
        ],
      },
    ],
    conversion_summary: { ready: 1, not_ready: 0 },
  },
};

function mountView() {
  return mount(ChartsView, {
    global: {
      stubs: {
        'el-tag': { template: '<span><slot /></span>' },
        'el-alert': { template: '<div><slot /></div>', props: ['title'] },
        'el-skeleton': { template: '<div class="skeleton" />' },
        'el-empty': { template: '<div class="empty"><slot /></div>' },
        'el-button': {
          template: '<button @click="$emit(\'click\', $event)"><slot /></button>',
          props: ['loading', 'type', 'plain', 'text'],
          emits: ['click'],
        },
        'el-pagination': { template: '<div class="pagination" />' },
        MetadataDetailDrawer: {
          name: 'MetadataDetailDrawer',
          props: ['modelValue', 'loading', 'detail', 'errorMessage'],
          emits: ['update:modelValue', 'create-subscription', 'search-resources'],
          template: '<div data-test="metadata-drawer-stub" />',
        },
      },
    },
  });
}

describe('ChartsView discovery metadata drawer', () => {
  beforeEach(() => {
    vi.clearAllMocks();

    fetchChartProviders.mockReset().mockResolvedValue({
      success: true,
      data: [
        {
          id: 'listenbrainz',
          chart_source: 'listenbrainz',
          display_name: 'ListenBrainz',
          enabled: true,
          mock: false,
          note: '',
          integration_point: 'runtime',
        },
      ],
    });
    fetchCharts.mockReset().mockResolvedValue(chartListResponse);
    fetchChartDetail
      .mockReset()
      .mockResolvedValueOnce(readyDetailResponse)
      .mockResolvedValueOnce(artistDetailResponse);
    fetchDiscoveryTargetDetail.mockReset().mockResolvedValue({
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
    });
    subscribeFromChartEntry.mockReset().mockResolvedValue({
      success: true,
      data: {
        dispatch_status: 'accepted',
      },
    });
    createSubscription.mockReset().mockResolvedValue({
      success: true,
      data: {
        id: 'sub-1',
        subscription_type: 'track',
        target_id: 'recording-123',
        target_name: 'Hello',
        target_entity_type: 'track',
        status: 'active',
        mode: 'manual',
        preference_json: {},
        target_payload: {},
        mock: false,
        created_at: '2026-04-05T10:00:00Z',
        updated_at: '2026-04-05T10:00:00Z',
      },
    });
    createSearchJob.mockReset().mockResolvedValue({
      success: true,
      data: { id: 'job-1' },
    });
    executeSearchJob.mockReset().mockResolvedValue({
      success: true,
      data: { id: 'job-1' },
    });
  });

  it('opens metadata drawer from hero entry click', async () => {
    const wrapper = mountView();
    await flushPromises();

    await wrapper.get('[data-test="discovery-hero-entry"]').trigger('click');
    await flushPromises();

    expect(fetchDiscoveryTargetDetail).toHaveBeenCalledWith(
      readyDetailResponse.data.hero_entry.target,
    );
    const drawer = wrapper.findComponent({ name: 'MetadataDetailDrawer' });
    expect(drawer.props('modelValue')).toBe(true);
    expect(drawer.props('detail')).toMatchObject({
      id: 'recording-123',
      title: 'Hello',
    });
  });

  it('does not fetch metadata when conversion is not ready', async () => {
    const wrapper = mountView();
    await flushPromises();

    await wrapper.get('[data-test="discovery-entry-entry-2"]').trigger('click');
    await flushPromises();

    expect(fetchDiscoveryTargetDetail).not.toHaveBeenCalledWith(
      readyDetailResponse.data.entry_groups[0].items[0].target,
    );
    expect(elMessageWarning).toHaveBeenCalledWith('需要补充 provider id');
  });

  it('keeps subscribe button behavior isolated from metadata click', async () => {
    const wrapper = mountView();
    await flushPromises();

    await wrapper.get('[data-test="subscribe-entry-entry-2"]').trigger('click');
    await flushPromises();

    expect(subscribeFromChartEntry).toHaveBeenCalledTimes(1);
    expect(fetchDiscoveryTargetDetail).not.toHaveBeenCalled();
  });

  it('clears stale active entry and drawer state when switching charts', async () => {
    const wrapper = mountView();
    await flushPromises();

    await wrapper.get('[data-test="discovery-hero-entry"]').trigger('click');
    await flushPromises();

    expect(wrapper.findComponent({ name: 'MetadataDetailDrawer' }).props('modelValue')).toBe(true);

    await wrapper.get('[data-test="open-chart-chart-2"]').trigger('click');
    await flushPromises();

    const drawer = wrapper.findComponent({ name: 'MetadataDetailDrawer' });
    expect(drawer.props('modelValue')).toBe(false);
    expect(drawer.props('detail')).toBe(null);
    expect(wrapper.find('[data-test="discovery-hero-entry"]').classes()).not.toContain('hero-entry-card--active');
  });

  it('renders rss search_lookup entry status and opens drawer through lookup target', async () => {
    fetchCharts.mockReset().mockResolvedValue(rssChartListResponse);
    fetchChartDetail.mockReset().mockResolvedValue(rssDetailResponse);

    const wrapper = mountView();
    await flushPromises();

    const statusText = wrapper.find('.entry-card__conversion').text();
    expect(statusText).toContain('metadata lookup ready');

    await wrapper.get('[data-test="discovery-entry-rss-entry-1"]').trigger('click');
    await flushPromises();

    expect(fetchDiscoveryTargetDetail).toHaveBeenCalledWith(
      rssDetailResponse.data.entry_groups[0].items[0].target,
    );
    const drawer = wrapper.findComponent({ name: 'MetadataDetailDrawer' });
    expect(drawer.props('modelValue')).toBe(true);
  });
});
