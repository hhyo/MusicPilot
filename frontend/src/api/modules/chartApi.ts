import api from '../request'

export interface ChartEntry {
  rank: number
  title: string
  artist: string
  album?: string
  mbid?: string
}

export interface ChartData {
  source: string
  chart_type: string
  updated_at: string
  entries: ChartEntry[]
}

export const chartApi = {
  // 获取支持的榜单源
  getSources() {
    return api.get('/api/v1/chart/sources')
  },

  // 获取榜单数据
  getChart(source: string, chartType: string, limit: number = 50) {
    return api.get<ChartData>(`/api/v1/chart/${source}/${chartType}`, { params: { limit } })
  },

  // 获取支持的榜单类型
  getChartTypes(source: string) {
    return api.get(`/api/v1/chart/${source}/types`)
  },
}