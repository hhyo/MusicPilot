import { http } from '@/services/http';
import type { EntityType, MetadataDetail } from '@/types/metadata';
import type { ApiMusicResolveDetailResponse, MusicMediaInfo, MusicMediaInput } from '@/types/music-media';

function resolveMusicBrainzRefKey(entityType: EntityType): string | null {
  if (entityType === 'artist') {
    return 'musicbrainz_artist_id';
  }
  if (entityType === 'album') {
    return 'musicbrainz_release_group_id';
  }
  if (entityType === 'track') {
    return 'musicbrainz_recording_id';
  }
  return null;
}

export function buildMusicMediaInputFromMetadataDetail(
  detail: MetadataDetail,
  sourceKind: string,
  sourceContext: Record<string, unknown> = {},
): MusicMediaInput {
  const externalRefs: Record<string, string> = { ...(detail.external_ids ?? {}) };
  const musicBrainzRefKey = detail.provider === 'musicbrainz' ? resolveMusicBrainzRefKey(detail.entity_type) : null;
  if (musicBrainzRefKey && detail.id) {
    externalRefs[musicBrainzRefKey] = detail.id;
  }

  return {
    entity_hint: detail.entity_type,
    source_kind: sourceKind,
    title: detail.track_title || detail.title,
    subtitle: detail.note,
    artist_names: detail.artist_name ? [detail.artist_name] : [],
    album_title: detail.album_title ?? null,
    album_artist_names: [],
    release_date: null,
    year: detail.year ?? null,
    track_number: null,
    disc_number: null,
    external_refs: externalRefs,
    source_context: sourceContext,
    raw_context: {},
  };
}

export function buildMusicMediaInputFromMusicMediaInfo(
  media: MusicMediaInfo,
  sourceKind: string,
  sourceContext: Record<string, unknown> = {},
): MusicMediaInput {
  const externalRefs: Record<string, string> = { ...(media.external_refs ?? {}) };
  const musicBrainzRefKey = media.provider === 'musicbrainz' ? resolveMusicBrainzRefKey(media.entity_type) : null;
  if (musicBrainzRefKey && media.provider_id) {
    externalRefs[musicBrainzRefKey] = media.provider_id;
  }

  return {
    entity_hint: media.entity_type,
    source_kind: sourceKind,
    title: media.title ?? null,
    subtitle: media.match_strategy ?? null,
    artist_names: [...media.artist_names],
    album_title: media.album_title ?? null,
    album_artist_names: [...media.album_artist_names],
    release_date: media.release_date ?? null,
    year: media.year ?? null,
    track_number: media.track_number ?? null,
    disc_number: media.disc_number ?? null,
    external_refs: externalRefs,
    source_context: sourceContext,
    raw_context: {},
  };
}

export async function resolveMusicMediaDetail(input: MusicMediaInput): Promise<ApiMusicResolveDetailResponse> {
  const { data } = await http.post<ApiMusicResolveDetailResponse>('/media/resolve/detail', {
    input,
  });
  return data;
}
