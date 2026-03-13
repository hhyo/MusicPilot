import api from './request'

export const systemApi = {
  getConfig() {
    return api.get('/api/v1/system/config')
  },

  updateConfig(data: any) {
    return api.put('/api/v1/system/config', data)
  },

  getStats() {
    return api.get('/api/v1/system/stats')
  },

  scanAll() {
    return api.post('/api/v1/system/scan-all')
  },

  getLogs() {
    return api.get('/api/v1/system/logs')
  },
}

export const libraryApi = {
  getList() {
    return api.get('/api/v1/libraries/')
  },

  getById(id: number) {
    return api.get(`/api/v1/libraries/${id}`)
  },

  create(data: any) {
    return api.post('/api/v1/libraries/', data)
  },

  update(id: number, data: any) {
    return api.put(`/api/v1/libraries/${id}`, data)
  },

  delete(id: number) {
    return api.delete(`/api/v1/libraries/${id}`)
  },

  scan(id: number, data?: { recursive?: boolean }) {
    return api.post(`/api/v1/libraries/${id}/scan`, data || {})
  },
}

export const downloadApi = {
  create(data: any) {
    return api.post('/api/v1/download/', data)
  },

  getHistory(params?: { skip?: number; limit?: number }) {
    return api.get('/api/v1/download/history', { params })
  },

  getById(id: number) {
    return api.get(`/api/v1/download/${id}`)
  },

  retry(id: number) {
    return api.post(`/api/v1/download/${id}/retry`)
  },
}

export const subscribeApi = {
  getList() {
    return api.get('/api/v1/subscribes/')
  },

  getById(id: number) {
    return api.get(`/api/v1/subscribes/${id}`)
  },

  create(data: any) {
    return api.post('/api/v1/subscribes/', data)
  },

  update(id: number, data: any) {
    return api.put(`/api/v1/subscribes/${id}`, data)
  },

  delete(id: number) {
    return api.delete(`/api/v1/subscribes/${id}`)
  },

  check(id: number) {
    return api.post(`/api/v1/subscribes/${id}/check`)
  },

  getReleases(id: number) {
    return api.get(`/api/v1/subscribes/${id}/releases`)
  },
}

export const mediaApi = {
  getServers() {
    return api.get('/api/v1/media/servers')
  },

  getServer(id: number) {
    return api.get(`/api/v1/media/servers/${id}`)
  },

  create(data: any) {
    return api.post('/api/v1/media/servers', data)
  },

  update(id: number, data: any) {
    return api.put(`/api/v1/media/servers/${id}`, data)
  },

  delete(id: number) {
    return api.delete(`/api/v1/media/servers/${id}`)
  },

  scan(id: number) {
    return api.post(`/api/v1/media/servers/${id}/scan`)
  },

  getStatus(id: number) {
    return api.get(`/api/v1/media/servers/${id}/status`)
  },
}

export * from './artist'
export * from './album'
export * from './track'
export * from './playlist'