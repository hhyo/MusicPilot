import { http } from '@/services/http';
import type { ApiResponse } from '@/types/metadata';

export interface HealthPayload {
  status: string;
  service: string;
  version: string;
  api_prefix: string;
  phase: string;
  host_integration: Record<string, unknown>;
  validation_matrix?: Record<string, unknown> | null;
}

export interface DashboardSummaryPayload {
  [key: string]: unknown;
}

export async function fetchHealth(): Promise<ApiResponse<HealthPayload>> {
  const { data } = await http.get<ApiResponse<HealthPayload>>('/health');
  return data;
}

export async function fetchDashboardSummary(): Promise<ApiResponse<DashboardSummaryPayload>> {
  const { data } = await http.get<ApiResponse<DashboardSummaryPayload>>('/dashboard/summary');
  return data;
}
