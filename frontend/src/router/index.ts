import { createRouter, createWebHistory } from 'vue-router';

import AppShell from '@/layouts/AppShell.vue';
import ChartsView from '@/views/ChartsView.vue';
import HomeView from '@/views/HomeView.vue';
import ModulePlaceholderView from '@/views/ModulePlaceholderView.vue';
import SearchView from '@/views/SearchView.vue';
import SubscriptionsView from '@/views/SubscriptionsView.vue';

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
        component: ChartsView,
        meta: {
          title: '榜单',
          description: 'Phase 4 提供榜单发现与从榜单项创建订阅的最小闭环。',
        },
      },
      {
        path: 'search',
        name: 'search',
        component: SearchView,
        meta: {
          title: '搜索',
          description: 'Phase 4 打通 metadata 搜索、SearchJob 与从详情创建订阅的最小闭环。',
        },
      },
      {
        path: 'subscriptions',
        name: 'subscriptions',
        component: SubscriptionsView,
        meta: {
          title: '订阅',
          description: 'Phase 4 提供订阅管理、立即执行与 run 结果回看。',
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
