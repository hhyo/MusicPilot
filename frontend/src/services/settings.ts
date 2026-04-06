import { http } from '@/services/http';
import type {
  ProviderSettingsResponse,
  ProviderSettingsUpdatePayload,
} from '@/types/settings';

export async function fetchProviderSettings(): Promise<ProviderSettingsResponse> {
  const { data } = await http.get<ProviderSettingsResponse>('/settings/providers');
  return data;
}

export async function updateProviderSettings(
  payload: ProviderSettingsUpdatePayload,
): Promise<ProviderSettingsResponse> {
  const { data } = await http.put<ProviderSettingsResponse>('/settings/providers', payload);
  return data;
}
