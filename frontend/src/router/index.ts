import { createRouter, createWebHashHistory } from 'vue-router'
import type { RouteRecordRaw } from 'vue-router'

const routes: RouteRecordRaw[] = [
  {
    path: '/',
    name: 'Home',
    component: () => import('../views/HomeView.vue'),
  },
  {
    path: '/library',
    name: 'Library',
    component: () => import('../views/library/LibraryView.vue'),
  },
  {
    path: '/artists',
    name: 'Artists',
    component: () => import('../views/artist/ArtistListView.vue'),
  },
  {
    path: '/artist/:id',
    name: 'ArtistDetail',
    component: () => import('../views/artist/ArtistDetailView.vue'),
  },
  {
    path: '/albums',
    name: 'Albums',
    component: () => import('../views/album/AlbumListView.vue'),
  },
  {
    path: '/album/:id',
    name: 'AlbumDetail',
    component: () => import('../views/album/AlbumDetailView.vue'),
  },
  {
    path: '/playlists',
    name: 'Playlists',
    component: () => import('../views/playlist/PlaylistListView.vue'),
  },
  {
    path: '/playlist/:id',
    name: 'PlaylistDetail',
    component: () => import('../views/playlist/PlaylistDetailView.vue'),
  },
  {
    path: '/download',
    name: 'Download',
    component: () => import('../views/download/DownloadView.vue'),
  },
  {
    path: '/subscribe',
    name: 'Subscribe',
    component: () => import('../views/subscribe/SubscribeView.vue'),
  },
  {
    path: '/site',
    name: 'Site',
    component: () => import('../views/site/SiteView.vue'),
  },
  {
    path: '/media',
    name: 'Media',
    component: () => import('../views/media/MediaView.vue'),
  },
  {
    path: '/system',
    name: 'System',
    component: () => import('../views/system/SystemView.vue'),
  },
  {
    path: '/chart',
    name: 'Chart',
    component: () => import('../views/chart/ChartView.vue'),
  },
  {
    path: '/organize',
    name: 'Organize',
    component: () => import('../views/organize/OrganizeView.vue'),
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
