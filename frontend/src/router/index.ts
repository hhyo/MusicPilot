import { createRouter, createWebHistory } from 'vue-router';

import AppShell from '@/layouts/AppShell.vue';
import HomeView from '@/views/HomeView.vue';
import ModulePlaceholderView from '@/views/ModulePlaceholderView.vue';
import SearchView from '@/views/SearchView.vue';

const routes = [
  {
    path: '/',
    component: AppShell,
    children: [
      {
        path: '',
        name: 'home',
        component: HomeView,
        meta: {
          title: 'MusicPilot Home',
          description: '音乐工作台首页占位',
        },
      },
      {
        path: 'charts',
        name: 'charts',
        component: ModulePlaceholderView,
        meta: {
          title: '榜单',
          description: 'Phase 0 仅保留榜单入口与页面边界说明，后续接入真实榜单源。',
        },
      },
      {
        path: 'search',
        name: 'search',
        component: SearchView,
        meta: {
          title: '搜索',
          description: 'Phase 2 打通最小 metadata 搜索闭环，联调本地 seed provider。',
        },
      },
      {
        path: 'subscriptions',
        name: 'subscriptions',
        component: ModulePlaceholderView,
        meta: {
          title: '订阅',
          description: 'Phase 0 仅保留四类订阅管理页面边界，不实现真实 CRUD 与调度。',
        },
      },
      {
        path: 'downloads',
        name: 'downloads',
        component: ModulePlaceholderView,
        meta: {
          title: '下载',
          description: 'Phase 0 仅保留任务列表与候选确认壳，不实现真实 PT 搜索或下载派发。',
        },
      },
      {
        path: 'organize',
        name: 'organize',
        component: ModulePlaceholderView,
        meta: {
          title: '整理',
          description: 'Phase 0 仅保留整理页占位，不实现真实整理、标签写入或媒体库刷新。',
        },
      },
      {
        path: 'settings',
        name: 'settings',
        component: ModulePlaceholderView,
        meta: {
          title: '设置',
          description: 'Phase 0 仅保留配置入口壳，后续再补分组表单与宿主适配项。',
        },
      },
    ],
  },
];

const router = createRouter({
  history: createWebHistory(),
  routes,
  scrollBehavior() {
    return { top: 0 };
  },
});

router.afterEach((to) => {
  const pageTitle = typeof to.meta.title === 'string' ? to.meta.title : 'MusicPilot';
  document.title = `${pageTitle} · MusicPilot`;
});

export default router;
