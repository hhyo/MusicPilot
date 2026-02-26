import api from './request'

export const artistApi = {
  getList(params?: { skip?: number; limit?: number; search?: string }) {
    return api.get('/api/v1/artists/', { params })
  },

  getTop(limit: number = 50) {
    return api.get('/api/v1/artists/top', { params: { limit } })
  },

  getById(id: number) {
    return api.get(`/api/v1/artists/${id}`)
  },

  create(data: any) {
    return api.post('/api/v1/artists/', data)
  },

  update(id: number, data: any) {
    return api.put(`/api/v1/artists/${id}`, data)
  },

  delete(id: number) {
    return api.delete(`/api/v1/artists/${id}`)
  },
}