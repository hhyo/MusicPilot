/**
 * 订阅 API
 */
import request from './request'

export interface Subscribe {
  id: number
  type: 'artist' | 'album' | 'playlist' | 'chart'
  source_type: 'musicbrainz' | 'netease' | 'qq'
  musicbrainz_id?: string
  playlist_id?: string
  name: string
  description?: string
  auto_download: boolean
  download_format?: string
  rules?: Record<string, any>
  state?: 'active' | 'paused'
  created_at: string
  updated_at: string
}

export interface SubscribeRelease {
  id: number
  subscribe_id: number
  release_type: 'album' | 'track'
  musicbrainz_id?: string
  title: string
  artist?: string
  download_status: 'pending' | 'downloading' | 'completed' | 'failed'
  torrent_id?: string
  downloader_task_id?: string
  created_at: string
  updated_at: string
}

export interface SubscribeListResponse {
  items: Subscribe[]
  total: number
  page: number
  page_size: number
}

export interface SubscribeReleaseListResponse {
  items: SubscribeRelease[]
  total: number
  page: number
  page_size: number
}

export interface CreateSubscribeRequest {
  type: 'artist' | 'album' | 'playlist' | 'chart'
  source_type?: 'musicbrainz' | 'netease' | 'qq'
  musicbrainz_id?: string
  playlist_id?: string
  name: string
  description?: string
  auto_download?: boolean
  download_format?: string
  rules?: Record<string, any>
}

export interface UpdateSubscribeRequest extends Partial<CreateSubscribeRequest> {
  state?: 'active' | 'paused'
}

/**
 * 获取订阅列表
 */
export async function listSubscribes(params?: {
  type?: string
  state?: string
  page?: number
  page_size?: number
}): Promise<SubscribeListResponse> {
  return request.get('/api/v1/subscribes', { params })
}

/**
 * 获取订阅详情
 */
export async function getSubscribe(id: number): Promise<Subscribe> {
  return request.get(`/api/v1/subscribes/${id}`)
}

/**
 * 创建订阅
 */
export async function createSubscribe(data: CreateSubscribeRequest): Promise<Subscribe> {
  return request.post('/api/v1/subscribes', data)
}

/**
 * 更新订阅
 */
export async function updateSubscribe(id: number, data: UpdateSubscribeRequest): Promise<Subscribe> {
  return request.put(`/api/v1/subscribes/${id}`, data)
}

/**
 * 删除订阅
 */
export async function deleteSubscribe(id: number): Promise<void> {
  return request.delete(`/api/v1/subscribes/${id}`)
}

/**
 * 检查订阅（手动触发）
 */
export async function checkSubscribe(id: number): Promise<any> {
  return request.post(`/api/v1/subscribes/${id}/check`)
}

/**
 * 检查所有订阅
 */
export async function checkAllSubscribes(): Promise<any> {
  return request.post('/api/v1/subscribes/check-all')
}

/**
 * 获取订阅的发布记录
 */
export async function getSubscribeReleases(
  subscribeId: number,
  params?: {
    download_status?: string
    page?: number
    page_size?: number
  }
): Promise<SubscribeReleaseListResponse> {
  return request.get(`/api/v1/subscribes/${subscribeId}/releases`, { params })
}

/**
 * 获取所有发布记录
 */
export async function getAllReleases(params?: {
  download_status?: string
  page?: number
  page_size?: number
}): Promise<SubscribeReleaseListResponse> {
  return request.get('/api/v1/subscribe-releases', { params })
}

/**
 * 获取发布记录详情
 */
export async function getRelease(id: number): Promise<SubscribeRelease> {
  return request.get(`/api/v1/subscribe-releases/${id}`)
}

/**
 * 重新下载发布记录
 */
export async function reDownloadRelease(id: number): Promise<any> {
  return request.post(`/api/v1/subscribe-releases/${id}/redownload`)
}