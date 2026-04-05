export type EntityType = 'artist' | 'album' | 'track';

export type ReleaseType =
  | 'single'
  | 'ep'
  | 'album'
  | 'compilation'
  | 'live'
  | 'remaster'
  | 'deluxe';

export interface ApiResponse<T> {
  success: boolean;
  code: string;
  message: string;
  data: T;
  request_id: string;
  timestamp: string;
  mock: boolean;
  note?: string | null;
  todo?: string[] | null;
}

export interface MetadataReference {
  id: string;
  title: string;
  entity_type: EntityType;
  subtitle?: string | null;
  track_number?: number | null;
  disc_number?: number | null;
}

export interface MetadataSummary {
  entity_type: EntityType;
  id: string;
  title: string;
  artist_name?: string | null;
  album_title?: string | null;
  track_title?: string | null;
  aliases: string[];
  year?: number | null;
  release_type?: ReleaseType | null;
  genres: string[];
  external_ids: Record<string, string>;
  provider: string;
  source_type: string;
  mock: boolean;
  note: string;
}

export interface MetadataDetail extends MetadataSummary {
  sort_name?: string | null;
  artist_type?: string | null;
  country?: string | null;
  area_name?: string | null;
  begin_area_name?: string | null;
  end_area_name?: string | null;
  ended?: boolean | null;
  duration_seconds?: number | null;
  disambiguation?: string | null;
  release_count?: number | null;
  release_group_count?: number | null;
  status?: string | null;
  barcode?: string | null;
  media_format?: string | null;
  track_count?: number | null;
  disc_count?: number | null;
  label_names: string[];
  secondary_types: string[];
  primary_release_types: string[];
  featured_albums: MetadataReference[];
  featured_singles: MetadataReference[];
  featured_other_releases: MetadataReference[];
  featured_release_group_counts: Record<string, number>;
  metadata_stage: string;
  integration_point: string;
  related_artists: MetadataReference[];
  related_album?: MetadataReference | null;
  related_albums: MetadataReference[];
  tracks: MetadataReference[];
  todo: string[];
}

export interface MetadataSearchData {
  keyword: string;
  entity_type: EntityType;
  page: number;
  page_size: number;
  total: number;
  provider: string;
  source_type: string;
  integration_point: string;
  items: MetadataSummary[];
}

export interface MetadataSearchPayload {
  keyword: string;
  type: EntityType;
  page?: number;
  page_size?: number;
}
