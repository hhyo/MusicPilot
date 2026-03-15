import { createRouter, createWebHashHistory } from 'vue-router'
import type { RouteRecordRaw } from 'vue-router'

const routes: RouteRecordRaw[] = [
  {
    path: '/',
    name: 'Home',
    component: () => import('../views/HomeView.vue'),
  },
  {
    path: '/search',
    name: 'Search',
    component: () => import('../views/SearchView.vue'),
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
    path: '/system',
    name: 'System',
    component: () => import('../views/system/SystemView.vue'),
  },
  {
    path: '/mediaserver',
    name: 'MediaServer',
    component: () => import('../views/mediaserver/MediaServerView.vue'),
  },
]

const router = createRouter({
  history: createWebHashHistory(),
  routes,
})

export default router
