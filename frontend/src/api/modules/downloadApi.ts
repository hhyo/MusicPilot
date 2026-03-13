import api from '../request'

export interface DownloadTask {
  id: number
  torrent_name: string
  torrent_url: string
  status: 'pending' | 'downloading' | 'seeding' | 'completed' | 'error'
  save_path: string
  progress: number
  created_at: string
}

export const downloadApi = {
  // 获取下载任务列表
  getTasks() {
    return api.get<DownloadTask[]>('/api/v1/download/tasks')
  },

  // 添加下载任务
  addTask(data: { torrent_url: string; save_path: string }) {
    return api.post<DownloadTask>('/api/v1/download/tasks', data)
  },

  // 删除下载任务
  deleteTask(id: number) {
    return api.delete(`/api/v1/download/tasks/${id}`)
  },

  // 获取下载器列表
  getClients() {
    return api.get('/api/v1/download/clients')
  },
}