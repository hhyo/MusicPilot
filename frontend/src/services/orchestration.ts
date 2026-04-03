import { http } from '@/services/http';
import type {
  ApiChartDetailResponse,
  ApiChartListResponse,
  ApiChartProvidersResponse,
  ApiOrganizePreviewResponse,
  ApiSubscriptionDetailResponse,
  ApiSubscriptionListResponse,
  ApiSubscriptionResponse,
  ApiSubscriptionRunResponse,
  ApiSubscriptionRunsResponse,
  CreateChartEntrySubscriptionPayload,
  CreateSubscriptionPayload,
  OrganizePreviewPayload,
  SubscriptionState,
  SubscriptionType,
  UpdateSubscriptionPayload,
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
): Promise<ApiSubscriptionResponse> {
  const { data } = await http.post<ApiSubscriptionResponse>(`/charts/${chartId}/subscribe`, payload);
  return data;
}

export async function fetchSubscriptions(params?: {
  subscription_type?: SubscriptionType;
  status?: SubscriptionState;
}): Promise<ApiSubscriptionListResponse> {
  const { data } = await http.get<ApiSubscriptionListResponse>('/subscriptions', { params });
  return data;
}

export async function createSubscription(payload: CreateSubscriptionPayload): Promise<ApiSubscriptionResponse> {
  const { data } = await http.post<ApiSubscriptionResponse>('/subscriptions', payload);
  return data;
}

export async function fetchSubscription(subscriptionId: string): Promise<ApiSubscriptionDetailResponse> {
  const { data } = await http.get<ApiSubscriptionDetailResponse>(`/subscriptions/${subscriptionId}`);
  return data;
}

export async function updateSubscription(
  subscriptionId: string,
  payload: UpdateSubscriptionPayload,
): Promise<ApiSubscriptionResponse> {
  const { data } = await http.patch<ApiSubscriptionResponse>(`/subscriptions/${subscriptionId}`, payload);
  return data;
}

export async function archiveSubscription(subscriptionId: string): Promise<ApiSubscriptionResponse> {
  const { data } = await http.delete<ApiSubscriptionResponse>(`/subscriptions/${subscriptionId}`);
  return data;
}

export async function runSubscription(subscriptionId: string): Promise<ApiSubscriptionRunResponse> {
  const { data } = await http.post<ApiSubscriptionRunResponse>(`/subscriptions/${subscriptionId}/run`);
  return data;
}

export async function fetchSubscriptionRuns(subscriptionId: string): Promise<ApiSubscriptionRunsResponse> {
  const { data } = await http.get<ApiSubscriptionRunsResponse>(`/subscriptions/${subscriptionId}/runs`);
  return data;
}

export async function fetchSubscriptionRun(runId: string): Promise<ApiSubscriptionRunResponse> {
  const { data } = await http.get<ApiSubscriptionRunResponse>(`/subscriptions/runs/${runId}`);
  return data;
}

export async function previewOrganize(payload: OrganizePreviewPayload): Promise<ApiOrganizePreviewResponse> {
  const { data } = await http.post<ApiOrganizePreviewResponse>('/organize/preview', payload);
  return data;
}
