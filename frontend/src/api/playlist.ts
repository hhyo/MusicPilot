import api from './request'

export const playlistApi = {
  getList(params?: { skip?: number; limit?: number }) {
    return api.get('/api/v1/playlists/', { params })
  },

  getSmart() {
    return api.get('/api/v1/playlists/smart')
  },

  getById(id: number) {
    return api.get(`/api/v1/playlists/${id}`)
  },

  create(data: any) {
    return api.post('/api/v1/playlists/', data)
  },

  update(id: number, data: any) {
    return api.put(`/api/v1/playlists/${id}`, data)
  },

  delete(id: number) {
    return api.delete(`/api/v1/playlists/${id}`)
  },

  addTrack(id: number, trackId: number, position?: number) {
    return api.post(`/api/v1/playlists/${id}/tracks`, {
      track_id: trackId,
      position,
    })
  },

  removeTrack(id: number, trackId: number) {
    return api.delete(`/api/v1/playlists/${id}/tracks/${trackId}`)
  },

  reorderTracks(id: number, trackIds: number[]) {
    return api.put(`/api/v1/playlists/${id}/tracks/reorder`, {
      track_ids: trackIds,
    })
  },
}