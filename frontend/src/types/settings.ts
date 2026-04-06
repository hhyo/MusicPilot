import type { ApiResponse } from '@/types/metadata';

export type ChartProviderMode = 'mock' | 'listenbrainz' | 'rss_feed';

export interface ChartRssFeedSettings {
  id: string;
  label: string;
  url: string;
  category: string;
  region: string;
  enabled: boolean;
}

export interface ProviderSettingsResponseData {
  chart_provider_mode: ChartProviderMode;
  chart_rss_feeds: ChartRssFeedSettings[];
  metadata_provider_mode: string | null;
}

export interface ProviderSettingsUpdatePayload {
  chart_provider_mode: ChartProviderMode;
  chart_rss_feeds: ChartRssFeedSettings[];
}

export type ProviderSettingsResponse = ApiResponse<ProviderSettingsResponseData>;
