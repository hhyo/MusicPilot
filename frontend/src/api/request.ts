import axios from 'axios'

// 根据环境自动选择 API 基础 URL
const getBaseURL = () => {
  // 优先使用环境变量
  if (import.meta.env.VITE_API_BASE_URL) {
    return import.meta.env.VITE_API_BASE_URL
  }
  // 默认使用本地后端（开发测试）
  return 'http://localhost:8000'
}

const api = axios.create({
  baseURL: getBaseURL(),
  timeout: 30000,
})

// 请求拦截器
api.interceptors.request.use(
  (config) => {
    return config
  },
  (error) => {
    return Promise.reject(error)
  }
)

// 响应拦截器
api.interceptors.response.use(
  (response) => {
    return response.data
  },
  (error) => {
    console.error('API Error:', error)
    return Promise.reject(error)
  }
)

export default api
