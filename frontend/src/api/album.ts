import api from './request'

export const albumApi = {
  getList(params?: { skip?: number; limit?: number; search?: string }) {
    return api.get('/api/v1/albums/', { params })
  },

  getRecent(limit: number = 50) {
    return api.get('/api/v1/albums/recent', { params: { limit } })
  },

  getTop(limit: number = 50) {
    return api.get('/api/v1/albums/top', { params: { limit } })
  },

  getById(id: number) {
    return api.get(`/api/v1/albums/${id}`)
  },

  getTracks(id: number, params?: { skip?: number; limit?: number }) {
    return api.get(`/api/v1/albums/${id}/tracks`, { params })
  },

  getCover(id: number) {
    return `${api.defaults.baseURL}/api/v1/albums/${id}/cover`
  },

  create(data: any) {
    return api.post('/api/v1/albums/', data)
  },

  update(id: number, data: any) {
    return api.put(`/api/v1/albums/${id}`, data)
  },

  delete(id: number) {
    return api.delete(`/api/v1/albums/${id}`)
  },
}

export * from './artist'
export * from './track'
export * from './playlist'