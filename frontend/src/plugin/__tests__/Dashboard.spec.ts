import { mount } from '@vue/test-utils';
import { afterEach, describe, expect, it } from 'vitest';

import Dashboard from '@/plugin/Dashboard.vue';

const vuetifyStubs = {
  VCard: { template: '<div><slot /></div>' },
  VCardItem: { template: '<div><slot /><slot name="prepend" /><slot name="append" /></div>' },
  VCardTitle: { template: '<div><slot /></div>' },
  VCardSubtitle: { template: '<div><slot /></div>' },
  VCardText: { template: '<div><slot /></div>' },
  VChip: { template: '<span><slot /></span>' },
  VBtn: { template: '<button><slot /></button>' },
  VIcon: { template: '<i><slot /></i>' },
};

describe('plugin/Dashboard.vue', () => {
  afterEach(() => {
    window.location.hash = '';
  });

  it('renders lightweight dashboard card content', () => {
    const wrapper = mount(Dashboard, {
      props: {
        config: {
          id: 'musicpilot',
          name: 'MusicPilot',
          key: 'home',
          attrs: {
            title: 'MusicPilot',
            subtitle: '音乐发现、元数据与整理工作台',
          },
          cols: {},
          elements: [],
          render_mode: 'vue',
        },
        allowRefresh: true,
        api: { get: () => undefined },
      },
      global: {
        stubs: vuetifyStubs,
      },
    });

    expect(wrapper.text()).toContain('MusicPilot');
    expect(wrapper.text()).toContain('音乐发现、元数据与整理工作台');
    expect(wrapper.text()).toContain('Metadata');
    expect(wrapper.text()).toContain('Discovery');
    expect(wrapper.text()).toContain('Workspace');
  });

  it('navigates to plugin dialog route when open button is clicked', async () => {
    const wrapper = mount(Dashboard, {
      props: {
        config: {
          id: 'musicpilot',
          name: 'MusicPilot',
          key: 'home',
          attrs: {
            title: 'MusicPilot',
            subtitle: '音乐发现、元数据与整理工作台',
          },
          cols: {},
          elements: [],
          render_mode: 'vue',
        },
        allowRefresh: true,
        api: { get: () => undefined },
      },
      global: {
        stubs: vuetifyStubs,
      },
    });

    await wrapper.get('button.musicpilot-dashboard__open').trigger('click');

    expect(window.location.hash).toBe('#/plugins?id=musicpilot');
  });
});
