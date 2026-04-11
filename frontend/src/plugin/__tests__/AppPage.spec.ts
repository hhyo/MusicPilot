import { flushPromises, mount } from '@vue/test-utils';
import { nextTick } from 'vue';
import { beforeAll, describe, expect, it, vi } from 'vitest';

import AppPage from '@/plugin/AppPage.vue';

describe('plugin/AppPage.vue', () => {
  beforeAll(() => {
    window.scrollTo = vi.fn();
  });

  it('mounts standalone app page shell and shows workbench content', async () => {
    const wrapper = mount(AppPage, {
      props: {
        api: { get: vi.fn(), post: vi.fn(), put: vi.fn(), patch: vi.fn(), delete: vi.fn() },
        pluginId: 'musicpilot',
        navKey: 'main',
      },
    });

    await nextTick();
    await flushPromises();
    await nextTick();

    expect(wrapper.text()).toContain('MusicPilot');
    expect(wrapper.text()).toContain('音乐工作台');
  });
});
