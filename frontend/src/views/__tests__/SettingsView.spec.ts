import { flushPromises, mount } from '@vue/test-utils';
import { beforeEach, describe, expect, it, vi } from 'vitest';

const { fetchProviderSettings, updateProviderSettings } = vi.hoisted(() => ({
  fetchProviderSettings: vi.fn(),
  updateProviderSettings: vi.fn(),
}));

vi.mock('@/services/settings', () => ({
  fetchProviderSettings,
  updateProviderSettings,
}));

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
    metadata_provider_mode: 'musicbrainz',
  },
  request_id: 'req-1',
  timestamp: '2026-04-12T08:00:00Z',
  mock: false,
  note: null,
  todo: null,
};

function mountView() {
  return mount(SettingsView, {
    global: {
      stubs: {
        VCard: { template: '<div><slot /></div>' },
        VCardText: { template: '<div><slot /></div>' },
        VAlert: { props: ['text'], template: '<div class="alert">{{ text }}</div>' },
        VSelect: {
          props: ['modelValue', 'items', 'label'],
          emits: ['update:modelValue'],
          template:
            '<select data-test="provider-mode" :value="modelValue" @change="$emit(\'update:modelValue\', $event.target.value)"><option v-for="item in items" :key="item.value" :value="item.value">{{ item.label }}</option></select>',
        },
        VTextarea: {
          props: ['modelValue'],
          emits: ['update:modelValue'],
          template:
            '<textarea data-test="rss-json" :value="modelValue" @input="$emit(\'update:modelValue\', $event.target.value)" />',
        },
        VBtn: {
          emits: ['click'],
          template: '<button @click="$emit(\'click\')"><slot /></button>',
        },
        VChip: { template: '<span><slot /></span>' },
      },
    },
  });
}

describe('SettingsView', () => {
  beforeEach(() => {
    vi.clearAllMocks();
    fetchProviderSettings.mockResolvedValue(providerSettingsResponse);
    updateProviderSettings.mockResolvedValue(providerSettingsResponse);
  });

  it('loads provider settings into the new view', async () => {
    const wrapper = mountView();
    await flushPromises();

    expect(fetchProviderSettings).toHaveBeenCalledTimes(1);
    expect(wrapper.text()).toContain('运行时 provider 与 RSS feed 配置');
    expect(wrapper.get('[data-test="provider-mode"]').element.value).toBe('rss_feed');
    expect(wrapper.get('[data-test="rss-json"]').element.value).toContain('网易云热歌榜');
  });

  it('saves edited RSS feed settings', async () => {
    const wrapper = mountView();
    await flushPromises();

    await wrapper.get('[data-test="provider-mode"]').setValue('listenbrainz');
    await wrapper.get('[data-test="rss-json"]').setValue(
      JSON.stringify(
        [
          {
            id: 'youtube-top-songs',
            label: 'YouTube 热门歌曲榜',
            url: 'https://rsshub.rssforever.com/youtube/charts/TopSongs',
            category: 'hot',
            region: 'Global',
            enabled: true,
          },
        ],
        null,
        2,
      ),
    );

    const buttons = wrapper.findAll('button');
    await buttons[1].trigger('click');
    await flushPromises();

    expect(updateProviderSettings).toHaveBeenCalledWith({
      chart_provider_mode: 'listenbrainz',
      chart_rss_feeds: [
        {
          id: 'youtube-top-songs',
          label: 'YouTube 热门歌曲榜',
          url: 'https://rsshub.rssforever.com/youtube/charts/TopSongs',
          category: 'hot',
          region: 'Global',
          enabled: true,
        },
      ],
    });
  });
});
