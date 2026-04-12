import type { ApiResponse, EntityType, MetadataDetail } from '@/types/metadata';

export interface MusicMediaInput {
  entity_hint?: EntityType | null;
  source_kind: string;
  title?: string | null;
  subtitle?: string | null;
  artist_names: string[];
  album_title?: string | null;
  album_artist_names: string[];
  release_date?: string | null;
  year?: number | null;
  track_number?: number | null;
  disc_number?: number | null;
  external_refs: Record<string, string>;
  source_context: Record<string, unknown>;
  raw_context: Record<string, unknown>;
}

export interface MusicMetaBase {
  entity_type: EntityType;
  canonical_title?: string | null;
  canonical_artist_names: string[];
  canonical_album_title?: string | null;
  canonical_album_artist_names: string[];
  canonical_release_date?: string | null;
  canonical_year?: number | null;
  track_number?: number | null;
  disc_number?: number | null;
  alias_titles: string[];
  alias_artist_names: string[];
  alias_album_titles: string[];
  featuring_artist_names: string[];
  external_refs: Record<string, string>;
  source_refs: Record<string, string>;
  evidence: Array<Record<string, unknown>>;
  normalization_notes: string[];
  confidence_hint?: number | null;
}

export interface MusicRecognitionAssessment {
  state: string;
  note?: string | null;
}

export interface MusicMediaInfo {
  entity_type: EntityType;
  provider: string;
  provider_id: string;
  title?: string | null;
  artist_names: string[];
  album_title?: string | null;
  album_artist_names: string[];
  release_date?: string | null;
  year?: number | null;
  track_number?: number | null;
  disc_number?: number | null;
  related_artist_ids: string[];
  related_album_id?: string | null;
  related_track_ids: string[];
  external_refs: Record<string, string>;
  match_confidence?: number | null;
  match_strategy?: string | null;
  match_evidence: Array<Record<string, unknown>>;
  diagnostics: string[];
  cover_url?: string | null;
  disambiguation?: string | null;
  release_context: Record<string, unknown>;
}

export interface MusicResolveDetailData {
  base: MusicMetaBase;
  assessment: MusicRecognitionAssessment;
  media: MusicMediaInfo;
  detail: MetadataDetail;
}

export type ApiMusicResolveDetailResponse = ApiResponse<MusicResolveDetailData>;
