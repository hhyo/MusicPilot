import { flushPromises, mount } from '@vue/test-utils';
import { nextTick } from 'vue';
import { beforeAll, describe, expect, it, vi } from 'vitest';

import Page from '@/plugin/Page.vue';

describe('plugin/Page.vue', () => {
  beforeAll(() => {
    window.scrollTo = vi.fn();
  });

  it('mounts plugin page shell and shows discovery entry', async () => {
    const wrapper = mount(Page, {
      props: {
        api: { get: vi.fn(), post: vi.fn(), put: vi.fn(), patch: vi.fn(), delete: vi.fn() },
        show_switch: true,
      },
    });

    await nextTick();
    await flushPromises();
    await nextTick();

    expect(wrapper.text()).toContain('MusicPilot');
    expect(wrapper.text()).toContain('榜单');
  });

  it('emits switch when plugin settings button is clicked', async () => {
    const wrapper = mount(Page, {
      props: {
        api: { get: vi.fn(), post: vi.fn(), put: vi.fn(), patch: vi.fn(), delete: vi.fn() },
        show_switch: true,
      },
    });

    await nextTick();
    await flushPromises();

    await wrapper.get('button.plugin-page-shell__switch').trigger('click');

    expect(wrapper.emitted('switch')).toHaveLength(1);
  });
});
