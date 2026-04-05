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
          description: '音乐工作台首页与当前项目状态总览',
        },
      },
      {
        path: 'charts',
        name: 'charts',
        component: ChartsView,
        meta: {
          title: '榜单',
          description: '当前提供 mock 或真实榜单入口，并支持从榜单项创建订阅。',
        },
      },
      {
        path: 'search',
        name: 'search',
        component: SearchView,
        meta: {
          title: '搜索',
          description: '当前提供 metadata 搜索、SearchJob 与从详情创建订阅，真实 provider 待接入。',
        },
      },
      {
        path: 'subscriptions',
        name: 'subscriptions',
        component: SubscriptionsView,
        meta: {
          title: '订阅',
          description: '当前提供订阅管理、手动执行、run 回看与音乐 organize 状态查看。',
        },
      },
      {
        path: 'downloads',
        name: 'downloads',
        component: ModulePlaceholderView,
        meta: {
          title: '下载',
          description: '当前仍是待接入模块，尚未提供真实 PT 搜索或自动下载派发闭环。',
        },
      },
      {
        path: 'organize',
        name: 'organize',
        component: ModulePlaceholderView,
        meta: {
          title: '整理',
          description: '当前主整理能力已嵌入订阅执行流，独立整理工作台仍待补齐。',
        },
      },
      {
        path: 'settings',
        name: 'settings',
        component: ModulePlaceholderView,
        meta: {
          title: '设置',
          description: '当前为配置入口占位，宿主接入与运行参数仍以环境变量为主。',
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
