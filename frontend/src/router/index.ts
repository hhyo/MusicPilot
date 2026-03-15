import { createRouter, createWebHashHistory } from 'vue-router'
import type { RouteRecordRaw } from 'vue-router'

const routes: RouteRecordRaw[] = [
  {
    path: '/',
    name: 'Home',
    component: () => import('../views/HomeView.vue'),
  },
  {
    path: '/discover',
    name: 'Discover',
    component: () => import('../views/DiscoverView.vue'),
  },
  {
    path: '/subscribe',
    name: 'Subscribe',
    component: () => import('../views/SubscribeView.vue'),
  },
  {
    path: '/download',
    name: 'Download',
    component: () => import('../views/DownloadView.vue'),
  },
  {
    path: '/organize',
    name: 'Organize',
    component: () => import('../views/OrganizeView.vue'),
  },
  {
    path: '/site',
    name: 'Site',
    component: () => import('../views/site/SiteView.vue'),
  },
  {
    path: '/system',
    name: 'System',
    component: () => import('../views/system/SystemView.vue'),
  },
]

const router = createRouter({
  history: createWebHashHistory(),
  routes,
})

export default router
