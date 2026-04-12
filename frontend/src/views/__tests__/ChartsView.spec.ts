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
  executeSearchJob,
  elMessageSuccess,
  elMessageWarning,
  elMessageError,
} = vi.hoisted(() => ({
  fetchChartProviders: vi.fn(),
  fetchCharts: vi.fn(),
  fetchChartDetail: vi.fn(),
  subscribeFromChartEntry: vi.fn(),
  resolveMusicMediaDetail: vi.fn(),
  createSubscription: vi.fn(),
  createSearchJob: vi.fn(),
  executeSearchJob: vi.fn(),
  elMessageSuccess: vi.fn(),
  elMessageWarning: vi.fn(),
  elMessageError: vi.fn(),
}));

vi.mock('@/services/orchestration', () => ({
  fetchChartProviders,
  fetchCharts,
  fetchChartDetail,
  subscribeFromChartEntry,
  createSubscription,
}));

vi.mock('@/services/music-media', () => ({
  resolveMusicMediaDetail,
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
      error: elMessageError,
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
        item_count: 2,
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

function buildMediaInput(overrides: Record<string, unknown> = {}) {
  return {
    entity_hint: 'track',
    source_kind: 'discovery',
    title: 'Hello',
    subtitle: 'Adele',
    artist_names: ['Adele'],
    album_title: '25',
    album_artist_names: [],
    release_date: '2015-11-20',
    year: 2015,
    track_number: null,
    disc_number: null,
    external_refs: {},
    source_context: {
      chart_id: 'chart-1',
      chart_source: 'listenbrainz',
      chart_name: 'Top Tracks',
      rank: 1,
      provider: 'musicbrainz',
      source_type: 'runtime',
    },
    raw_context: {},
    ...overrides,
  };
}

function buildEntryView(overrides: Record<string, unknown> = {}) {
  return {
    entry: {
      item_id: 'entry-1',
      chart_id: 'chart-1',
      chart_source: 'listenbrainz',
      chart_name: 'Top Tracks',
      rank: 1,
      item_type: 'track',
      target_id: 'recording-123',
      target_name: 'Hello',
      subtitle: 'Adele',
      provider: 'musicbrainz',
      source_type: 'runtime',
      target_payload: {},
      mock: false,
      note: '',
    },
    media_input: buildMediaInput(),
    entry_summary: 'Hello · Adele',
    badges: ['top-1', 'tracks'],
    highlight_reason: 'Top track',
    conversion_state: 'direct',
    conversion_note: null,
    ...overrides,
  };
}

const artistDetailResponse = {
  success: true,
  data: {
    chart: chartListResponse.data.items[1],
    items: [],
    item_count: 1,
    mock: false,
    note: '',
    integration_point: 'runtime',
    hero_entry: buildEntryView({
      entry: {
        item_id: 'artist-entry-1',
        chart_id: 'chart-2',
        chart_source: 'listenbrainz',
        chart_name: 'Top Artists',
        rank: 1,
        item_type: 'artist',
        target_id: 'artist-123',
        target_name: 'Adele',
        subtitle: 'UK',
        provider: 'musicbrainz',
        source_type: 'runtime',
        target_payload: {},
        mock: false,
        note: '',
      },
      media_input: buildMediaInput({
        entity_hint: 'artist',
        title: null,
        subtitle: 'UK',
        artist_names: ['Adele'],
        album_title: null,
        year: null,
        release_date: null,
        external_refs: {
          musicbrainz_artist_id: 'artist-123',
        },
        source_context: {
          chart_id: 'chart-2',
          chart_source: 'listenbrainz',
          chart_name: 'Top Artists',
          rank: 1,
          provider: 'musicbrainz',
          source_type: 'runtime',
        },
      }),
      entry_summary: 'Adele · UK',
      badges: ['top-1', 'artists'],
      conversion_state: 'direct',
    }),
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
    item_count: 2,
    mock: false,
    note: '',
    integration_point: 'runtime',
    hero_entry: buildEntryView(),
    summary_stats: { items: 2 },
    entry_groups: [
      {
        group_key: 'tracks',
        group_label: 'Tracks',
        items: [
          buildEntryView({
            entry: {
              item_id: 'entry-2',
              chart_id: 'chart-1',
              chart_source: 'listenbrainz',
              chart_name: 'Top Tracks',
              rank: 2,
              item_type: 'track',
              target_id: 'recording-456',
              target_name: 'Skyfall',
              subtitle: 'Adele',
              provider: 'musicbrainz',
              source_type: 'runtime',
              target_payload: {},
              mock: false,
              note: '',
            },
            media_input: buildMediaInput({
              title: 'Skyfall',
              subtitle: 'Adele',
              external_refs: {},
              source_context: {
                chart_id: 'chart-1',
                chart_source: 'listenbrainz',
                chart_name: 'Top Tracks',
                rank: 2,
                provider: 'musicbrainz',
                source_type: 'runtime',
              },
            }),
            entry_summary: 'Skyfall · Adele',
            conversion_state: 'insufficient',
            conversion_note: 'Missing media input fields: requires title + artist_names.',
          }),
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

const rssReadyEntry = buildEntryView({
  entry: {
    item_id: 'rss-entry-1',
    chart_id: 'rss-feed-feed-1',
    chart_source: 'rss_feed',
    chart_name: '网易云喜欢',
    rank: 1,
    item_type: 'track',
    target_id: '',
    target_name: 'Hello',
    subtitle: 'Adele',
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
  media_input: buildMediaInput({
    entity_hint: 'track',
    source_kind: 'discovery',
    title: 'Hello',
    subtitle: 'Adele',
    artist_names: ['Adele'],
    album_title: '25',
    external_refs: {
      source_id: 'song-123',
      source_url: 'https://music.163.com/#/song?id=123',
    },
    source_context: {
      chart_id: 'rss-feed-feed-1',
      chart_source: 'rss_feed',
      chart_name: '网易云喜欢',
      rank: 1,
      provider: 'rss_feed',
      source_type: 'rss_feed/netease_playlist_tracks',
      family: 'netease_playlist_tracks',
    },
    raw_context: {
      family: 'netease_playlist_tracks',
      title_candidates: ['Hello'],
      artist_name_candidates: ['Adele'],
      album_title_candidates: ['25'],
    },
  }),
  badges: ['liked', 'tracks'],
  conversion_state: 'ready',
  conversion_note: null,
});

const rssDetailResponse = {
  success: true,
  data: {
    chart: rssChartListResponse.data.items[0],
    items: [],
    item_count: 1,
    mock: false,
    note: '',
    integration_point: 'runtime',
    hero_entry: rssReadyEntry,
    summary_stats: { items: 1 },
    entry_groups: [
      {
        group_key: 'tracks',
        group_label: 'Tracks',
        items: [rssReadyEntry],
      },
    ],
    conversion_summary: { ready: 1, not_ready: 0 },
  },
};

const directReadyDetailResponse = {
  success: true,
  data: {
    chart: chartListResponse.data.items[0],
    items: [],
    item_count: 1,
    mock: false,
    note: '',
    integration_point: 'runtime',
    hero_entry: null,
    summary_stats: { items: 1 },
    entry_groups: [
      {
        group_key: 'tracks',
        group_label: 'Tracks',
        items: [
          buildEntryView({
            entry: {
              item_id: 'direct-ready-entry',
              chart_id: 'chart-1',
              chart_source: 'listenbrainz',
              chart_name: 'Top Tracks',
              rank: 1,
              item_type: 'track',
              target_id: 'recording-999',
              target_name: 'Set Fire to the Rain',
              subtitle: 'Adele',
              provider: 'musicbrainz',
              source_type: 'listenbrainz_sitewide_stats',
              target_payload: {},
              mock: false,
              note: '',
            },
            media_input: buildMediaInput({
              title: 'Set Fire to the Rain',
              subtitle: 'Adele',
              external_refs: {
                musicbrainz_recording_id: 'recording-999',
              },
              source_context: {
                chart_id: 'chart-1',
                chart_source: 'listenbrainz',
                chart_name: 'Top Tracks',
                rank: 1,
                provider: 'musicbrainz',
                source_type: 'listenbrainz_sitewide_stats',
              },
            }),
            entry_summary: 'Set Fire to the Rain · Adele',
            conversion_state: 'direct',
          }),
        ],
      },
    ],
    conversion_summary: { ready: 1, not_ready: 0 },
  },
};

const rssNotReadyDetailResponse = {
  success: true,
  data: {
    chart: rssChartListResponse.data.items[0],
    items: [],
    item_count: 1,
    mock: false,
    note: '',
    integration_point: 'runtime',
    hero_entry: null,
    summary_stats: { items: 1 },
    entry_groups: [
      {
        group_key: 'tracks',
        group_label: 'Tracks',
        items: [
          buildEntryView({
            entry: {
              item_id: 'rss-not-ready-entry',
              chart_id: 'rss-feed-feed-1',
              chart_source: 'rss_feed',
              chart_name: '网易云喜欢',
              rank: 1,
              item_type: 'track',
              target_id: '',
              target_name: 'Unknown',
              subtitle: null,
              provider: 'rss_feed',
              source_type: 'rss_feed/netease_playlist_tracks',
              target_payload: {},
              mock: false,
              note: '',
            },
            media_input: buildMediaInput({
              title: 'Unknown',
              subtitle: null,
              artist_names: [],
              album_title: null,
              external_refs: {},
              source_context: {
                chart_id: 'rss-feed-feed-1',
                chart_source: 'rss_feed',
                chart_name: '网易云喜欢',
                rank: 1,
                provider: 'rss_feed',
                source_type: 'rss_feed/netease_playlist_tracks',
                family: 'netease_playlist_tracks',
              },
              raw_context: {},
            }),
            entry_summary: 'Unknown',
            badges: ['liked', 'tracks'],
            conversion_state: 'insufficient',
            conversion_note: 'Missing media input fields: requires title + artist_names.',
          }),
        ],
      },
    ],
    conversion_summary: { ready: 0, not_ready: 1 },
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
    resolveMusicMediaDetail.mockReset().mockResolvedValue({
      success: true,
      data: {
        media: {
          entity_type: 'track',
          provider: 'musicbrainz',
          provider_id: 'recording-123',
          title: 'Hello',
          artist_names: ['Adele'],
          album_artist_names: [],
          related_artist_ids: [],
          related_track_ids: [],
          external_refs: {},
          match_evidence: [],
          diagnostics: [],
          release_context: {},
        },
        detail: {
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

  it('opens metadata drawer from hero entry click through the unified media chain', async () => {
    const wrapper = mountView();
    await flushPromises();

    await wrapper.get('[data-test="discovery-hero-entry"]').trigger('click');
    await flushPromises();

    expect(resolveMusicMediaDetail).toHaveBeenCalledWith(readyDetailResponse.data.hero_entry.media_input);
    const drawer = wrapper.findComponent({ name: 'MetadataDetailDrawer' });
    expect(drawer.props('modelValue')).toBe(true);
    expect(drawer.props('detail')).toMatchObject({
      id: 'recording-123',
      title: 'Hello',
    });
  });

  it('does not resolve metadata when conversion state is insufficient', async () => {
    const wrapper = mountView();
    await flushPromises();

    await wrapper.get('[data-test="discovery-entry-entry-2"]').trigger('click');
    await flushPromises();

    expect(resolveMusicMediaDetail).not.toHaveBeenCalledWith(
      readyDetailResponse.data.entry_groups[0].items[0].media_input,
    );
    expect(elMessageWarning).toHaveBeenCalledWith('解析信息不足');
  });

  it('keeps subscribe button behavior isolated from metadata click', async () => {
    fetchCharts.mockReset().mockResolvedValue(rssChartListResponse);
    fetchChartDetail.mockReset().mockResolvedValue(rssDetailResponse);

    const wrapper = mountView();
    await flushPromises();

    await wrapper.get('[data-test="subscribe-entry-rss-entry-1"]').trigger('click');
    await flushPromises();

    expect(subscribeFromChartEntry).toHaveBeenCalledTimes(1);
    expect(resolveMusicMediaDetail).not.toHaveBeenCalled();
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

  it('renders rss ready entry status and opens drawer through the unified media chain', async () => {
    fetchCharts.mockReset().mockResolvedValue(rssChartListResponse);
    fetchChartDetail.mockReset().mockResolvedValue(rssDetailResponse);

    const wrapper = mountView();
    await flushPromises();

    const statusText = wrapper.find('.entry-card__conversion').text();
    expect(statusText).toContain('可进入统一媒体解析');

    await wrapper.get('[data-test="discovery-entry-rss-entry-1"]').trigger('click');
    await flushPromises();

    expect(resolveMusicMediaDetail).toHaveBeenCalledWith(
      rssDetailResponse.data.entry_groups[0].items[0].media_input,
    );
    expect(wrapper.findComponent({ name: 'MetadataDetailDrawer' }).props('modelValue')).toBe(true);
  });

  it('shows direct ready status text as 已可直接查看详情', async () => {
    fetchCharts.mockReset().mockResolvedValue(chartListResponse);
    fetchChartDetail.mockReset().mockResolvedValue(directReadyDetailResponse);

    const wrapper = mountView();
    await flushPromises();

    expect(wrapper.find('.entry-card__conversion').text()).toContain('已可直接查看详情');
  });

  it('shows insufficient status text as 解析信息不足', async () => {
    fetchCharts.mockReset().mockResolvedValue(rssChartListResponse);
    fetchChartDetail.mockReset().mockResolvedValue(rssNotReadyDetailResponse);

    const wrapper = mountView();
    await flushPromises();

    expect(wrapper.find('.entry-card__conversion').text()).toContain('解析信息不足');
  });

  it('disables subscribe button for unresolved entries', async () => {
    fetchCharts.mockReset().mockResolvedValue(rssChartListResponse);
    fetchChartDetail.mockReset().mockResolvedValue(rssNotReadyDetailResponse);

    const wrapper = mountView();
    await flushPromises();

    const subscribeButton = wrapper.get('[data-test="subscribe-entry-rss-not-ready-entry"]');
    expect((subscribeButton.element as HTMLButtonElement).disabled).toBe(true);
  });
});
