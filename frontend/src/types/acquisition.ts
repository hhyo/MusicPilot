import type { ApiResponse, EntityType, MetadataDetail } from '@/types/metadata';

export type TriggerSource = 'manual' | 'chart' | 'subscription' | 'artist_watch';
export type JobStatus =
  | 'queued'
  | 'running'
  | 'matched'
  | 'manual_pending'
  | 'dispatched'
  | 'completed'
  | 'no_result'
  | 'failed';
export type DecisionStatus = 'auto_download' | 'manual_confirm' | 'reject' | 'pending';
export type AdapterMode = 'mock' | 'host';
export type AdapterStrategy = 'mock' | 'prefer_host' | 'strict_host';
export type VerificationState = 'verified' | 'unverified' | 'placeholder';
export type MatrixStatus = 'stable' | 'single_sample' | 'flaky' | 'blocked' | 'unknown';

export interface HostStrategyDecision {
  stage: 'dispatch_endpoint' | 'path_handoff' | 'organize_apply';
  selected_path: string;
  matrix_status: MatrixStatus;
  risk_level: 'low' | 'medium' | 'high' | 'blocked';
  recommended_action: string;
  reason: string;
  note: string;
  blocked: boolean;
  source_sample_ids: string[];
}

export interface HostStrategySummary {
  preferred_dispatch_endpoint: string;
  preferred_handoff_source: string;
  preferred_organize_path: string;
  caution_paths: string[];
  blocked_paths: string[];
  note: string;
}

export interface AdapterResolution {
  adapter_key: string;
  adapter_mode: AdapterMode;
  strategy: AdapterStrategy;
  capability_source: string;
  verification_state: VerificationState;
  fallback_reason?: string | null;
  integration_point: string;
  host_integration_enabled: boolean;
}

export interface PathHandoffInfo {
  download_hash?: string | null;
  source_path?: string | null;
  source_filetype?: string | null;
  source_name?: string | null;
  source_basename?: string | null;
  source_extension?: string | null;
  handoff_source: string;
  handoff_status: string;
  verification_state: VerificationState;
  note: string;
  raw_summary: Record<string, unknown>;
}

export interface QueryPreferences {
  preferred_formats: string[];
  prefer_lossless: boolean;
  include_aliases: boolean;
  include_year: boolean;
  allow_live: boolean;
  allow_remaster: boolean;
  negative_keywords: string[];
  auto_download_threshold: number;
  manual_confirm_threshold: number;
}

export interface QueryClause {
  query_type: 'canonical' | 'alias' | 'relaxed' | 'negative';
  source: string;
  query: string;
  explanation: string;
  priority: number;
}

export interface QueryContext {
  query_source_type: EntityType;
  query_source_id: string;
  entity_title: string;
  artist_name?: string | null;
  album_title?: string | null;
  track_title?: string | null;
  year?: number | null;
  release_type?: string | null;
  aliases: string[];
  genres: string[];
  external_ids: Record<string, string>;
  provider: string;
  source_type: string;
  note: string;
  summary: string;
}

export interface QueryBuildResult {
  query_source_type: EntityType;
  query_source_id: string;
  provider: string;
  source_type: string;
  mock: boolean;
  preferences: QueryPreferences;
  canonical_queries: QueryClause[];
  alias_queries: QueryClause[];
  relaxed_queries: QueryClause[];
  negative_queries: QueryClause[];
  ordered_queries: QueryClause[];
  query_context: QueryContext;
  note: string;
  integration_point: string;
  todo: string[];
}

export interface SearchJobSummary {
  id: string;
  query_source_type: EntityType;
  query_source_id: string;
  trigger_source: TriggerSource;
  profile_id: string;
  strategy: string;
  mode: string;
  status: JobStatus;
  created_at: string;
  updated_at: string;
  started_at?: string | null;
  finished_at?: string | null;
  mock: boolean;
  note?: string | null;
  query_build?: QueryBuildResult | null;
  metadata_snapshot?: MetadataDetail | null;
  summary: Record<string, unknown>;
  strategy_summary?: HostStrategySummary | null;
  error_message?: string | null;
  adapter_resolution?: AdapterResolution | null;
}

export interface ScoreBreakdownItem {
  score: number;
  reason: string;
}

export interface SearchCandidateDetail {
  id: string;
  job_id: string;
  site_id: string;
  site_name: string;
  title: string;
  normalized_title: string;
  size_bytes: number;
  seeders: number;
  peers: number;
  format_tag?: string | null;
  bitrate_kbps?: number | null;
  source_tags: string[];
  raw_score: number;
  score_total: number;
  score_breakdown: Record<string, ScoreBreakdownItem>;
  decision: DecisionStatus;
  reason_codes: string[];
  dispatchable: boolean;
  dispatch_status: string;
  mock: boolean;
  note?: string | null;
  created_at: string;
  adapter_resolution?: AdapterResolution | null;
  strategy_decision?: HostStrategyDecision | null;
  path_handoff?: PathHandoffInfo | null;
  raw_payload?: Record<string, unknown>;
}

export interface SearchCandidateListData {
  job_id: string;
  items: SearchCandidateDetail[];
  total: number;
  mock: boolean;
  note: string;
  adapter_resolution?: AdapterResolution | null;
  strategy_summary?: HostStrategySummary | null;
}

export interface SearchJobCreatePayload {
  query_source_type: EntityType;
  query_source_id: string;
  trigger_source?: TriggerSource;
  profile_id?: string;
  strategy?: string;
  mode?: 'manual' | 'auto';
  preferences?: Partial<QueryPreferences>;
}

export interface DispatchPayload {
  result_id: string;
  downloader_id?: string;
  save_path_policy?: 'auto' | 'manual';
  manual_confirm?: boolean;
}

export interface DispatchResult {
  candidate_id: string;
  job_id: string;
  dispatchable: boolean;
  dispatch_status: string;
  target_downloader: string;
  downloader_task_id?: string | null;
  note: string;
  integration_point: string;
  mock: boolean;
  binding_id?: string | null;
  dispatch_backend: AdapterMode;
  capability_source: string;
  fallback_reason?: string | null;
  failure_reason?: string | null;
  verification_state: VerificationState;
  strategy_decision?: HostStrategyDecision | null;
  path_handoff?: PathHandoffInfo | null;
  host_response_summary: Record<string, unknown>;
  adapter_resolution?: AdapterResolution | null;
}

export type ApiQueryBuildResponse = ApiResponse<QueryBuildResult>;
export type ApiSearchJobResponse = ApiResponse<SearchJobSummary>;
export type ApiSearchCandidatesResponse = ApiResponse<SearchCandidateListData>;
export type ApiDispatchResponse = ApiResponse<DispatchResult>;
