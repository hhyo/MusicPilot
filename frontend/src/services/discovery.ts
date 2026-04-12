import { http } from '@/services/http';
import type {
  ApiChartDetailResponse,
  ApiChartListResponse,
  ApiChartProvidersResponse,
  ApiSubscriptionResponse,
  CreateChartEntrySubscriptionPayload,
  SubscriptionType,
} from '@/types/orchestration';
import type { EntityType } from '@/types/metadata';

export async function fetchChartProviders(): Promise<ApiChartProvidersResponse> {
  const { data } = await http.get<ApiChartProvidersResponse>('/charts/providers');
  return data;
}

export async function fetchCharts(params?: {
  provider?: string;
  chart_type?: EntityType;
  region?: string;
}): Promise<ApiChartListResponse> {
  const { data } = await http.get<ApiChartListResponse>('/charts', { params });
  return data;
}

export async function fetchChartDetail(chartId: string): Promise<ApiChartDetailResponse> {
  const { data } = await http.get<ApiChartDetailResponse>(`/charts/${chartId}`);
  return data;
}

export async function subscribeFromChartEntry(
  chartId: string,
  payload: CreateChartEntrySubscriptionPayload,
) : Promise<ApiSubscriptionResponse> {
  const { data } = await http.post<ApiSubscriptionResponse>(`/charts/${chartId}/subscribe`, payload);
  return data;
}

export function normalizeSubscriptionTypeLabel(type: SubscriptionType): string {
  switch (type) {
    case 'artist':
      return '艺人';
    case 'album':
      return '专辑';
    case 'track':
      return '歌曲';
    case 'chart_entry':
      return '榜单项';
  }
}
