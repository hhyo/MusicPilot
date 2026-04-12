import type { SearchJobCreatePayload } from '@/types/acquisition';
import type { MetadataDetail, MetadataSummary } from '@/types/metadata';
import type { MusicMediaInput } from '@/types/music-media';
import type { DiscoveryEntryView, SubscriptionSummary } from '@/types/orchestration';

export function buildMusicMediaInputFromMetadataSummary(summary: MetadataSummary): MusicMediaInput {
  return {
    entity_hint: summary.entity_type,
    source_kind: 'search',
    title: summary.title,
    subtitle: summary.note,
    artist_names: summary.artist_name ? [summary.artist_name] : [],
    album_title: summary.album_title || null,
    album_artist_names: summary.artist_name ? [summary.artist_name] : [],
    release_date: null,
    year: summary.year ?? null,
    track_number: null,
    disc_number: null,
    external_refs: summary.external_ids || {},
    source_context: {
      provider: summary.provider,
      source_type: summary.source_type,
      metadata_id: summary.id,
    },
    raw_context: {
      metadata_summary: summary,
    },
  };
}

export function buildMusicMediaInputFromMetadataDetail(detail: MetadataDetail): MusicMediaInput {
  return {
    entity_hint: detail.entity_type,
    source_kind: 'metadata_detail',
    title: detail.title,
    subtitle: detail.note,
    artist_names: detail.artist_name ? [detail.artist_name] : [],
    album_title: detail.album_title || null,
    album_artist_names: detail.artist_name ? [detail.artist_name] : [],
    release_date: null,
    year: detail.year ?? null,
    track_number: null,
    disc_number: null,
    external_refs: detail.external_ids || {},
    source_context: {
      provider: detail.provider,
      source_type: detail.source_type,
      metadata_id: detail.id,
    },
    raw_context: {
      metadata_detail: detail,
    },
  };
}

export function buildSearchJobPayload(input: MusicMediaInput): SearchJobCreatePayload {
  return {
    input,
    trigger_source: 'manual',
    mode: 'manual',
  };
}

export function buildSubscriptionPayloadFromMetadataDetail(detail: MetadataDetail) {
  return {
    subscription_type: detail.entity_type,
    target_id: detail.id,
    target_name: detail.title,
    target_entity_type: detail.entity_type,
    target_payload: {
      provider: detail.provider,
      provider_id: detail.id,
      source_type: detail.source_type,
      external_ids: detail.external_ids,
    },
  } as const;
}

export function buildChartEntryResolveInput(entry: DiscoveryEntryView): MusicMediaInput {
  return entry.media_input;
}

export function inferSubscriptionInput(subscription: SubscriptionSummary): MusicMediaInput | null {
  const payload = subscription.target_payload || {};
  const input = payload.music_media_input;
  if (input && typeof input === 'object') {
    return input as MusicMediaInput;
  }
  return null;
}
