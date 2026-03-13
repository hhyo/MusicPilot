import api from '../request'

export interface MediaServer {
  type: 'jellyfin' | 'plex'
  name: string
  url: string
  enabled: boolean
}

export const mediaServerApi = {
  // 获取媒体服务器列表
  getServers() {
    return api.get<MediaServer[]>('/api/v1/mediaserver/servers')
  },

  // 添加媒体服务器
  addServer(data: Omit<MediaServer, 'enabled'> & { api_key: string }) {
    return api.post<MediaServer>('/api/v1/mediaserver/servers', data)
  },

  // 刷新媒体库
  refreshLibrary(serverId: string) {
    return api.post(`/api/v1/mediaserver/servers/${serverId}/refresh`)
  },

  // 通知所有服务器
  notifyAll() {
    return api.post('/api/v1/mediaserver/notify-all')
  },
}