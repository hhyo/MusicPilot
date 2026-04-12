import { mount } from '@vue/test-utils';
import { describe, expect, it, vi } from 'vitest';

const { mountMusicPilotApp } = vi.hoisted(() => ({
  mountMusicPilotApp: vi.fn(() => ({
    app: { unmount: vi.fn() },
    router: {
      isReady: vi.fn().mockResolvedValue(undefined),
    },
  })),
}));

vi.mock('@/app/createApp', () => ({
  mountMusicPilotApp,
}));

import Page from '@/plugin/Page.vue';

describe('plugin/Page.vue', () => {
  it('mounts plugin page shell and shows discovery entry', async () => {
    const wrapper = mount(Page, {
      props: {
        api: { get: vi.fn(), post: vi.fn(), put: vi.fn(), patch: vi.fn(), delete: vi.fn() },
        show_switch: true,
      },
      global: {
        stubs: {
          VCard: { template: '<div><slot /></div>' },
          VCardText: { template: '<div><slot /></div>' },
          VBtn: { emits: ['click'], template: '<button @click="$emit(\'click\')"><slot /></button>' },
        },
      },
    });

    expect(wrapper.text()).toContain('MusicPilot');
    expect(mountMusicPilotApp).toHaveBeenCalled();
  });

  it('emits switch when plugin settings button is clicked', async () => {
    const wrapper = mount(Page, {
      props: {
        api: { get: vi.fn(), post: vi.fn(), put: vi.fn(), patch: vi.fn(), delete: vi.fn() },
        show_switch: true,
      },
      global: {
        stubs: {
          VCard: { template: '<div><slot /></div>' },
          VCardText: { template: '<div><slot /></div>' },
          VBtn: { emits: ['click'], template: '<button @click="$emit(\'click\')"><slot /></button>' },
        },
      },
    });

    await wrapper.findAll('button')[0].trigger('click');

    expect(wrapper.emitted('switch')).toHaveLength(1);
  });
});
