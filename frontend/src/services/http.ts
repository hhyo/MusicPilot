import axios from 'axios';

export const http = axios.create({
  baseURL: import.meta.env.VITE_API_BASE_URL ?? '/api/v1/plugin/musicpilot',
  timeout: 10_000,
});

// TODO(Phase 1): 在此基础上补统一拦截器、错误码映射、request_id 透传与真实 API service。

