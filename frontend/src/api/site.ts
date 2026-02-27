import request from './request'

export interface Site {
  id: number
  name: string
  domain?: string
  url: string
  cookie?: string
  passkey?: string
  username?: string
  password?: string
  proxy?: string
  ua?: string
  timeout: number
  rss?: string
  rss_interval: number
  downloader: string
  priority: number
  enabled: boolean
  site_type: string
  created_at: string
  updated_at: string
}

export interface SiteCreate {
  name: string
  domain?: string
  url: string
  cookie?: string
  passkey?: string
  username?: string
  password?: string
  proxy?: string
  ua?: string
  timeout?: number
  rss?: string
  rss_interval?: number
  downloader?: string
  priority?: number
  enabled?: boolean
  site_type?: string
}

export interface SiteUpdate {
  name?: string
  domain?: string
  url?: string
  cookie?: string
  passkey?: string
  username?: string
  password?: string
  proxy?: string
  ua?: string
  timeout?: number
  rss?: string
  rss_interval?: number
  downloader?: string
  priority?: number
  enabled?: boolean
  site_type?: string
}

export interface SiteListResponse {
  total: number
  items: Site[]
}

export interface TestSiteRequest {
  id: number
}

export interface TestSiteResponse {
  success: boolean
  message: string
}

export const siteApi = {
  /**
   * 获取站点列表
   */
  getSites: (params?: {
    skip?: number
    limit?: number
    enabled?: boolean
    downloader?: string
  }) => {
    return request.get<SiteListResponse>('/api/v1/sites', { params })
  },

  /**
   * 获取启用的站点
   */
  getEnabledSites: () => {
    return request.get<Site[]>('/api/v1/sites/enabled')
  },

  /**
   * 获取站点详情
   */
  getSite: (id: number) => {
    return request.get<Site>(`/api/v1/sites/${id}`)
  },

  /**
   * 创建站点
   */
  createSite: (data: SiteCreate) => {
    return request.post<Site>('/api/v1/sites', data)
  },

  /**
   * 更新站点
   */
  updateSite: (id: number, data: SiteUpdate) => {
    return request.put<Site>(`/api/v1/sites/${id}`, data)
  },

  /**
   * 删除站点
   */
  deleteSite: (id: number) => {
    return request.delete(`/api/v1/sites/${id}`)
  },

  /**
   * 切换站点启用状态
   */
  toggleSite: (id: number) => {
    return request.post<Site>(`/api/v1/sites/${id}/toggle`)
  },

  /**
   * 测试站点连接
   */
  testSite: (data: TestSiteRequest) => {
    return request.post<TestSiteResponse>('/api/v1/sites/test', data)
  }
}