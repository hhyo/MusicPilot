import api from './request'

export const trackApi = {
  getList(params?: { skip?: number; limit?: number; search?: string }) {
    return api.get('/api/v1/tracks/', { params })
  },

  getRecent(limit: number = 50) {
    return api.get('/api/v1/tracks/recent', { params: { limit } })
  },

  getById(id: number) {
    return api.get(`/api/v1/tracks/${id}`)
  },

  stream(id: number) {
    return `${api.defaults.baseURL}/api/v1/tracks/${id}/stream`
  },

  getLyrics(id: number) {
    return api.get(`/api/v1/tracks/${id}/lyrics`)
  },

  play(id: number) {
    return api.post(`/api/v1/tracks/${id}/play`)
  },
}