import api from '../request'

export interface OrganizeTask {
  id: number
  download_task_id: number
  source_path: string
  target_path: string
  status: 'pending' | 'processing' | 'completed' | 'failed'
  created_at: string
}

export const organizeApi = {
  // 获取整理任务列表
  getTasks() {
    return api.get<OrganizeTask[]>('/api/v1/organize/tasks')
  },

  // 获取整理任务详情
  getTask(id: number) {
    return api.get<OrganizeTask>(`/api/v1/organize/tasks/${id}`)
  },

  // 重新整理
  retryTask(id: number) {
    return api.post(`/api/v1/organize/tasks/${id}/retry`)
  },
}