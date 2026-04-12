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

import AppPage from '@/plugin/AppPage.vue';

describe('plugin/AppPage.vue', () => {
  it('mounts standalone app page shell and shows workbench content', async () => {
    const wrapper = mount(AppPage, {
      props: {
        api: { get: vi.fn(), post: vi.fn(), put: vi.fn(), patch: vi.fn(), delete: vi.fn() },
        pluginId: 'musicpilot',
        navKey: 'main',
      },
      global: {
        stubs: {
          VCard: { template: '<div><slot /></div>' },
          VCardText: { template: '<div><slot /></div>' },
        },
      },
    });

    expect(mountMusicPilotApp).toHaveBeenCalled();
    expect(wrapper.find('.plugin-app-shell').exists()).toBe(true);
  });
});
