import { flushPromises, mount } from '@vue/test-utils';
import { beforeEach, describe, expect, it, vi } from 'vitest';

const {
  fetchProviderSettings,
  updateProviderSettings,
  elMessageSuccess,
  elMessageError,
} = vi.hoisted(() => ({
  fetchProviderSettings: vi.fn(),
  updateProviderSettings: vi.fn(),
  elMessageSuccess: vi.fn(),
  elMessageError: vi.fn(),
}));

vi.mock('@/services/settings', () => ({
  fetchProviderSettings,
  updateProviderSettings,
}));

vi.mock('element-plus', async () => {
  const actual = await vi.importActual<typeof import('element-plus')>('element-plus');
  return {
    ...actual,
    ElMessage: {
      success: elMessageSuccess,
      error: elMessageError,
    },
  };
});

import SettingsView from '@/views/SettingsView.vue';

const providerSettingsResponse = {
  success: true,
  code: 'SETTINGS_PROVIDERS_OK',
  message: 'Provider settings loaded.',
  data: {
    chart_provider_mode: 'rss_feed',
    chart_rss_feeds: [
      {
        id: 'netease-hot-tracks',
        label: '网易云热歌榜',
        url: 'https://rsshub.rssforever.com/163/music/playlist/3778678',
        category: 'hot',
        region: 'CN',
        enabled: true,
      },
    ],
    metadata_provider_mode: 'seed',
  },
  request_id: 'req-1',
  timestamp: '2026-04-06T08:00:00Z',
  mock: false,
  note: null,
  todo: null,
};

const validationErrorResponse = {
  success: false,
  code: 'VALIDATION_ERROR',
  message: 'Validation failed.',
  data: null,
  request_id: 'req-422',
  timestamp: '2026-04-06T08:02:00Z',
  mock: false,
  note: null,
  todo: null,
  detail: [
    {
      loc: ['body', 'chart_provider_mode'],
      msg: 'value is not a valid enumeration member',
      type: 'type_error.enum',
    },
  ],
};

function mountView() {
  return mount(SettingsView, {
    global: {
      stubs: {
        'el-alert': {
          props: ['title', 'type', 'closable', 'showIcon'],
          template: '<div class="el-alert-stub" :data-type="type">{{ title }}<slot /></div>',
        },
        'el-button': {
          props: ['loading', 'type', 'plain', 'text', 'disabled'],
          emits: ['click'],
          template: '<button :disabled="disabled" @click="$emit(\'click\', $event)"><slot /></button>',
        },
        'el-tag': {
          template: '<span class="el-tag-stub"><slot /></span>',
        },
      },
    },
  });
}

describe('SettingsView', () => {
  beforeEach(() => {
    vi.clearAllMocks();
    fetchProviderSettings.mockReset().mockResolvedValue(providerSettingsResponse);
    updateProviderSettings.mockReset().mockResolvedValue(providerSettingsResponse);
  });

  it('loads provider mode and RSS feeds from the settings API', async () => {
    const wrapper = mountView();

    await flushPromises();

    expect(fetchProviderSettings).toHaveBeenCalledTimes(1);
    expect(wrapper.get('[data-test="chart-provider-mode"]').element.value).toBe('rss_feed');
    expect(wrapper.get('[data-test="metadata-provider-mode"]').text()).toContain('seed');
    expect(wrapper.get('[data-test="rss-feed-json"]').element.value).toContain('网易云热歌榜');
  });

  it('keeps save disabled until settings load succeeds', async () => {
    fetchProviderSettings.mockReset().mockRejectedValueOnce(new Error('network down'));

    const wrapper = mountView();

    await flushPromises();

    expect(wrapper.get('[data-test="save-provider-settings"]').attributes('disabled')).toBeDefined();
    expect(wrapper.get('[data-test="settings-feedback"]').text()).toContain('network down');
  });

  it('enables save after a successful reload', async () => {
    fetchProviderSettings
      .mockReset()
      .mockRejectedValueOnce(new Error('network down'))
      .mockResolvedValueOnce(providerSettingsResponse);

    const wrapper = mountView();

    await flushPromises();

    expect(wrapper.get('[data-test="save-provider-settings"]').attributes('disabled')).toBeDefined();

    await wrapper.get('[data-test="retry-load-provider-settings"]').trigger('click');
    await flushPromises();

    expect(fetchProviderSettings).toHaveBeenCalledTimes(2);
    expect(wrapper.get('[data-test="save-provider-settings"]').attributes('disabled')).toBeUndefined();
  });

  it('saves edited provider settings with the parsed RSS feed payload', async () => {
    const wrapper = mountView();

    await flushPromises();

    await wrapper.get('[data-test="chart-provider-mode"]').setValue('listenbrainz');
    await wrapper.get('[data-test="rss-feed-json"]').setValue(
      JSON.stringify(
        [
          {
            id: 'youtube-pop',
            label: 'YouTube Popular',
            url: 'https://example.com/rss',
            category: 'popular',
            region: 'GLOBAL',
            enabled: false,
          },
        ],
        null,
        2,
      ),
    );

    await wrapper.get('[data-test="save-provider-settings"]').trigger('click');
    await flushPromises();

    expect(updateProviderSettings).toHaveBeenCalledWith({
      chart_provider_mode: 'listenbrainz',
      chart_rss_feeds: [
        {
          id: 'youtube-pop',
          label: 'YouTube Popular',
          url: 'https://example.com/rss',
          category: 'popular',
          region: 'GLOBAL',
          enabled: false,
        },
      ],
    });
    expect(wrapper.get('[data-test="settings-feedback"]').text()).toContain('保存成功');
  });

  it('blocks save when the RSS feed JSON is invalid', async () => {
    const wrapper = mountView();

    await flushPromises();

    await wrapper.get('[data-test="rss-feed-json"]').setValue('{"id": "broken"');
    await wrapper.get('[data-test="save-provider-settings"]').trigger('click');

    expect(updateProviderSettings).not.toHaveBeenCalled();
    expect(wrapper.get('[data-test="settings-feedback"]').text()).toContain('RSS Feed JSON 解析失败');
  });

  it('shows backend errors when provider settings update fails', async () => {
    updateProviderSettings.mockResolvedValue({
      success: false,
      code: 'SETTINGS_PROVIDERS_FAILED',
      message: '保存失败，请稍后重试。',
      data: providerSettingsResponse.data,
      request_id: 'req-2',
      timestamp: '2026-04-06T08:01:00Z',
      mock: false,
      note: null,
      todo: null,
    });

    const wrapper = mountView();

    await flushPromises();

    await wrapper.get('[data-test="save-provider-settings"]').trigger('click');
    await flushPromises();

    expect(wrapper.get('[data-test="settings-feedback"]').text()).toContain('保存失败，请稍后重试。');
  });

  it('shows a readable summary for 422 validation responses', async () => {
    updateProviderSettings.mockResolvedValue(validationErrorResponse);

    const wrapper = mountView();

    await flushPromises();

    await wrapper.get('[data-test="chart-provider-mode"]').setValue('listenbrainz');
    await wrapper.get('[data-test="save-provider-settings"]').trigger('click');
    await flushPromises();

    expect(wrapper.get('[data-test="settings-feedback"]').text()).toContain('Validation failed');
    expect(wrapper.get('[data-test="settings-feedback"]').text()).toContain('chart_provider_mode');
  });
});
