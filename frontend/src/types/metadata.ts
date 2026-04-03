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
  country?: string | null;
  duration_seconds?: number | null;
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
