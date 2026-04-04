import type {
  AdapterMode,
  AdapterResolution,
  PathHandoffInfo,
  SearchCandidateDetail,
  SearchJobSummary,
  VerificationState,
} from '@/types/acquisition';
import type { ApiResponse, EntityType, MetadataDetail } from '@/types/metadata';

export type SubscriptionType = 'artist' | 'album' | 'track' | 'chart_entry';
export type SubscriptionState = 'active' | 'paused' | 'archived';
export type SubscriptionMode = 'manual' | 'scheduled_placeholder';
export type SubscriptionRunStatus =
  | 'queued'
  | 'running'
  | 'matched'
  | 'manual_pending'
  | 'no_result'
  | 'failed';
export type OrganizeStatus =
  | 'planned'
  | 'preview_ready'
  | 'apply_pending'
  | 'applied'
  | 'fallback_applied'
  | 'skipped'
  | 'failed';
export type OrganizeConflictPolicy = 'skip_existing' | 'overwrite' | 'append_suffix';

export interface ChartProviderInfo {
  id: string;
  chart_source: string;
  display_name: string;
  enabled: boolean;
  mock: boolean;
  note: string;
  integration_point: string;
}

export interface ChartInfo {
  id: string;
  chart_source: string;
  chart_name: string;
  chart_type: EntityType;
  region?: string | null;
  category?: string | null;
  refresh_hint?: string | null;
  item_count: number;
  updated_at: string;
  mock: boolean;
  note: string;
}

export interface ChartEntryInfo {
  item_id: string;
  chart_id: string;
  chart_source: string;
  chart_name: string;
  rank: number;
  item_type: EntityType;
  target_id: string;
  target_name: string;
  subtitle?: string | null;
  provider: string;
  source_type: string;
  mock: boolean;
  note: string;
}

export interface ChartListData {
  items: ChartInfo[];
  total: number;
  mock: boolean;
  note: string;
  integration_point: string;
}

export interface ChartDetailData {
  chart: ChartInfo;
  items: ChartEntryInfo[];
  item_count: number;
  mock: boolean;
  note: string;
  integration_point: string;
}

export interface CreateChartEntrySubscriptionPayload {
  chart_item_id: string;
  mode?: SubscriptionMode;
  preference_json?: Record<string, unknown>;
}

export interface CreateSubscriptionPayload {
  subscription_type: SubscriptionType;
  target_id: string;
  target_name?: string;
  target_entity_type?: EntityType;
  mode?: SubscriptionMode;
  preference_json?: Record<string, unknown>;
  target_payload?: Record<string, unknown>;
}

export interface UpdateSubscriptionPayload {
  status?: SubscriptionState;
  mode?: SubscriptionMode;
  preference_json?: Record<string, unknown> | null;
}

export interface SubscriptionSummary {
  id: string;
  subscription_type: SubscriptionType;
  target_id: string;
  target_name: string;
  target_entity_type?: EntityType | null;
  chart_source?: string | null;
  chart_name?: string | null;
  status: SubscriptionState;
  mode: SubscriptionMode;
  preference_json: Record<string, unknown>;
  target_payload: Record<string, unknown>;
  latest_run_status?: string | null;
  last_run_at?: string | null;
  mock: boolean;
  note?: string | null;
  created_at: string;
  updated_at: string;
}

export interface OrganizeStrategySnapshot {
  strategy_name: string;
  library_type: string;
  root_path: string;
  artist_dir_template: string;
  album_dir_template: string;
  track_file_template: string;
  conflict_policy: OrganizeConflictPolicy;
  template_note: string;
}

export interface OrganizePreviewResult {
  id: string;
  subscription_run_id?: string | null;
  search_job_id?: string | null;
  candidate_id?: string | null;
  binding_id?: string | null;
  organizeable: boolean;
  organize_backend: AdapterMode;
  adapter_mode: AdapterMode;
  strategy: string;
  strategy_snapshot: OrganizeStrategySnapshot;
  organize_status: OrganizeStatus;
  target_library_path: string;
  target_relative_path: string;
  strategy_note: string;
  integration_point: string;
  capability_source: string;
  fallback_reason?: string | null;
  failure_reason?: string | null;
  path_handoff?: PathHandoffInfo | null;
  verification_state: VerificationState;
  adapter_resolution?: AdapterResolution | null;
  mock: boolean;
  note?: string | null;
  created_at: string;
  updated_at: string;
}

export interface SubscriptionRunSummary {
  id: string;
  subscription_id: string;
  search_job_id?: string | null;
  execution_status: SubscriptionRunStatus;
  matched_candidates_count: number;
  organize_record_id?: string | null;
  started_at?: string | null;
  finished_at?: string | null;
  summary_json: Record<string, unknown>;
  mock: boolean;
  note?: string | null;
  error_message?: string | null;
  created_at: string;
  updated_at: string;
}

export interface SubscriptionDetail extends SubscriptionSummary {
  recent_runs: SubscriptionRunSummary[];
}

export interface SubscriptionListData {
  items: SubscriptionSummary[];
  total: number;
  mock: boolean;
  note: string;
}

export interface SubscriptionRunListData {
  subscription_id: string;
  items: SubscriptionRunSummary[];
  total: number;
  mock: boolean;
  note: string;
}

export interface SubscriptionRunDetail extends SubscriptionRunSummary {
  subscription: SubscriptionSummary;
  metadata_target?: MetadataDetail | null;
  search_job?: SearchJobSummary | null;
  candidates: SearchCandidateDetail[];
  organize_preview?: OrganizePreviewResult | null;
}

export interface OrganizePreviewPayload {
  candidate_id?: string;
  binding_id?: string;
}

export interface OrganizeApplyPayload {
  organize_job_id: string;
}

export interface OrganizeRecordListData {
  items: OrganizePreviewResult[];
  total: number;
  mock: boolean;
  note: string;
}

export type ApiChartProvidersResponse = ApiResponse<ChartProviderInfo[]>;
export type ApiChartListResponse = ApiResponse<ChartListData>;
export type ApiChartDetailResponse = ApiResponse<ChartDetailData>;
export type ApiSubscriptionResponse = ApiResponse<SubscriptionSummary>;
export type ApiSubscriptionDetailResponse = ApiResponse<SubscriptionDetail>;
export type ApiSubscriptionListResponse = ApiResponse<SubscriptionListData>;
export type ApiSubscriptionRunResponse = ApiResponse<SubscriptionRunDetail>;
export type ApiSubscriptionRunsResponse = ApiResponse<SubscriptionRunListData>;
export type ApiOrganizePreviewResponse = ApiResponse<OrganizePreviewResult>;
export type ApiOrganizeRecordResponse = ApiResponse<OrganizePreviewResult>;
export type ApiOrganizeJobsResponse = ApiResponse<OrganizeRecordListData>;
