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
  error_message?: string | null;
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
}

export interface SearchCandidateListData {
  job_id: string;
  items: SearchCandidateDetail[];
  total: number;
  mock: boolean;
  note: string;
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
}

export type ApiQueryBuildResponse = ApiResponse<QueryBuildResult>;
export type ApiSearchJobResponse = ApiResponse<SearchJobSummary>;
export type ApiSearchCandidatesResponse = ApiResponse<SearchCandidateListData>;
export type ApiDispatchResponse = ApiResponse<DispatchResult>;
