/**
 * 统一的 API 客户端
 * 所有 API 调用都通过这个模块进行
 */
import axios from 'axios'

// 创建 axios 实例
const api = axios.create({
  baseURL: import.meta.env.VITE_API_BASE_URL || 'http://localhost:8000',
  timeout: 30000,
  headers: {
    'Content-Type': 'application/json',
  },
})

// 请求拦截器
api.interceptors.request.use(
  (config) => {
    return config
  },
  (error) => {
    return Promise.reject(error)
  }
)

// 响应拦截器
api.interceptors.response.use(
  (response) => {
    return response.data
  },
  (error) => {
    console.error('API Error:', error)
    return Promise.reject(error)
  }
)

// ========== 专辑 API ==========
export const albumApi = {
  // 获取专辑列表
  list: (params?: { skip?: number; limit?: number }) => 
    api.get('/api/v1/albums/', params),
  
  // 获取最近添加的专辑
  recent: (params?: { limit?: number }) => 
    api.get('/api/v1/albums/recent', params),
  
  // 获取热门专辑
  top: (params?: { limit?: number }) => 
    api.get('/api/v1/albums/top', params),
  
  // 获取专辑详情
  get: (albumId: number) => 
    api.get(`/api/v1/albums/${albumId}`),
  
  // 获取专辑封面
  cover: (albumId: number) => 
    api.get(`/api/v1/albums/${albumId}/cover`),
  
  // 获取专辑曲目
  tracks: (albumId: number) => 
    api.get(`/api/v1/albums/${albumId}/tracks`),
}

// ========== 艺术家 API ==========
export const artistApi = {
  // 获取艺术家列表
  list: (params?: { skip?: number; limit?: number }) => 
    api.get('/api/v1/artists/', params),
  
  // 获取热门艺术家
  top: (params?: { limit?: number }) => 
    api.get('/api/v1/artists/top', params),
  
  // 获取艺术家详情
  get: (artistId: number) => 
    api.get(`/api/v1/artists/${artistId}`),
}

// ========== 歌曲 API ==========
export const trackApi = {
  // 获取歌曲列表
  list: (params?: { skip?: number; limit?: number }) => 
    api.get('/api/v1/tracks/', params),
  
  // 获取最近播放的歌曲
  recent: (params?: { limit?: number }) => 
    api.get('/api/v1/tracks/recent', params),
  
  // 获取歌曲详情
  get: (trackId: number) => 
    api.get(`/api/v1/tracks/${trackId}`),
  
  // 播放歌曲
  play: (trackId: number) => 
    api.post(`/api/v1/tracks/${trackId}/play`),
  
  // 获取歌词
  lyrics: (trackId: number) => 
    api.get(`/api/v1/tracks/${trackId}/lyrics`),
  
  // 获取歌曲流地址
  stream: (trackId: number) => 
    api.get(`/api/v1/tracks/${trackId}/stream`),
}

// ========== 订阅 API ==========
export const subscribeApi = {
  // 获取订阅列表
  list: (params?: { type?: string; state?: string; skip?: number; limit?: number }) => 
    api.get('/api/v1/subscribes', params),
  
  // 创建订阅
  create: (data: {
    type: string
    name: string
    source_type?: string
    musicbrainz_id?: string
    description?: string
    auto_download?: boolean
    download_format?: string
  }) => api.post('/api/v1/subscribes', data),
  
  // 删除订阅
  delete: (subscribeId: number) => 
    api.delete(`/api/v1/subscribes/${subscribeId}`),
  
  // 检查所有订阅
  checkAll: () => 
    api.post('/api/v1/subscribes/check-all'),
  
  // 检查单个订阅
  check: (subscribeId: number) => 
    api.post(`/api/v1/subscribes/${subscribeId}/check`),
}

// ========== 下载任务 API ==========
export const downloadApi = {
  // 获取下载任务列表
  list: () => api.get('/api/v1/download/tasks'),
  
  // 创建下载任务
  create: (data: { torrent_url: string; save_path?: string }) => 
    api.post('/api/v1/download/tasks', data),
  
  // 删除下载任务
  delete: (taskId: number) => 
    api.delete(`/api/v1/download/tasks/${taskId}`),
  
  // 获取可用的下载客户端
  clients: () => api.get('/api/v1/download/clients'),
}

// ========== 整理任务 API ==========
export const organizeApi = {
  // 获取整理任务列表
  list: () => api.get('/api/v1/organize/tasks'),
  
  // 创建整理任务
  create: (data: { source_path: string; target_path: string }) => 
    api.post('/api/v1/organize/tasks', data),
  
  // 删除整理任务
  delete: (taskId: number) => 
    api.delete(`/api/v1/organize/tasks/${taskId}`),
  
  // 重试失败的整理任务
  retry: (taskId: number) => 
    api.post(`/api/v1/organize/tasks/${taskId}/retry`),
}

// ========== 榜单 API ==========
export const chartApi = {
  // 获取榜单来源
  sources: () => api.get('/api/v1/chart/sources'),
  
  // 获取榜单类型
  types: (source: string) => 
    api.get(`/api/v1/chart/${source}/types`),
  
  // 获取榜单数据
  get: (source: string, chartType: string, params?: { limit?: number }) => 
    api.get(`/api/v1/chart/${source}/${chartType}`, params),
}

// ========== 媒体服务器 API ==========
export const mediaServerApi = {
  // 获取媒体服务器列表
  list: () => api.get('/api/v1/mediaserver/servers'),
  
  // 刷新媒体服务器
  refresh: (serverId: number) => 
    api.post(`/api/v1/mediaserver/servers/${serverId}/refresh`),
}

// ========== 站点 API ==========
export const siteApi = {
  // 获取站点列表
  list: () => api.get('/api/v1/sites'),
  
  // 获取启用的站点
  enabled: () => api.get('/api/v1/sites/enabled'),
  
  // 测试站点
  test: (siteId: number) => api.post(`/api/v1/sites/${site_id}/test`),
  
  // 切换站点
  toggle: (siteId: number) => 
    api.post(`/api/v1/sites/${siteId}/toggle`),
}

// ========== 音乐库 API ==========
export const libraryApi = {
  // 获取音乐库列表
  list: () => api.get('/api/v1/library/'),
  
  // 获取音乐库详情
  get: (libraryId: number) => api.get(`/api/v1/library/${libraryId}`),
  
  // 创建音乐库
  create: (data: { name: string; path: string }) => 
    api.post('/api/v1/library/', data),
  
  // 删除音乐库
  delete: (libraryId: number) => api.delete(`/api/v1/library/${libraryId}`),
  
  // 扫描音乐库
  scan: (libraryId: number) => api.post(`/api/v1/library/${libraryId}/scan'),
}

// ========== 播放列表 API ==========
export const playlistApi = {
  // 获取播放列表
  list: () => api.get('/api/v1/playlists/'),
  
  // 获取智能播放列表
  smart: () => api.get('/api/v1/playlists/smart'),
  
  // 获取播放列表详情
  get: (playlistId: number) => 
    api.get(`/api/v1/playlists/${playlistId}`),
  
  // 获取播放列表曲目
  tracks: (playlistId: number) => 
    api.get(`/api/v1/playlists/${playlistId}/tracks`),
}

// 导出默认 API 实例
export default api