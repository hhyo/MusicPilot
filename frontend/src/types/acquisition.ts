import type { ApiResponse, EntityType } from '@/types/metadata';
import type {
  MusicMediaInfo,
  MusicMediaInput,
  MusicMetaBase,
  MusicRecognitionAssessment,
} from '@/types/music-media';

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
export type AdapterSelectionMode = 'mock' | 'prefer_host' | 'strict_host';
export type VerificationState = 'verified' | 'unverified' | 'placeholder';

export interface AdapterResolution {
  adapter_key: string;
  adapter_mode: AdapterMode;
  selection_mode: AdapterSelectionMode;
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
  entity_type: EntityType;
  provider: string;
  provider_id: string;
  title: string;
  artist_names: string[];
  album_title?: string | null;
  album_artist_names: string[];
  year?: number | null;
  track_number?: number | null;
  disc_number?: number | null;
  external_refs: Record<string, string>;
  match_strategy?: string | null;
  note: string;
  summary: string;
}

export interface QueryBuildResult {
  entity_type: EntityType;
  provider: string;
  provider_id: string;
  music_media_info: MusicMediaInfo;
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
  music_media_input: MusicMediaInput;
  music_meta_base: MusicMetaBase;
  music_recognition_assessment: MusicRecognitionAssessment;
  music_media_info: MusicMediaInfo;
  trigger_source: TriggerSource;
  profile_id: string;
  mode: string;
  status: JobStatus;
  created_at: string;
  updated_at: string;
  started_at?: string | null;
  finished_at?: string | null;
  mock: boolean;
  note?: string | null;
  query_build?: QueryBuildResult | null;
  summary: Record<string, unknown>;
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
}

export interface SearchJobCreatePayload {
  input: MusicMediaInput;
  trigger_source?: TriggerSource;
  profile_id?: string;
  mode?: 'manual' | 'auto';
  preferences?: Partial<QueryPreferences>;
}

export interface QueryBuildPayload {
  input: MusicMediaInput;
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
  path_handoff?: PathHandoffInfo | null;
  host_response_summary: Record<string, unknown>;
  adapter_resolution?: AdapterResolution | null;
}

export type ApiQueryBuildResponse = ApiResponse<QueryBuildResult>;
export type ApiSearchJobListResponse = ApiResponse<SearchJobSummary[]>;
export type ApiSearchJobResponse = ApiResponse<SearchJobSummary>;
export type ApiSearchCandidatesResponse = ApiResponse<SearchCandidateListData>;
export type ApiDispatchResponse = ApiResponse<DispatchResult>;
