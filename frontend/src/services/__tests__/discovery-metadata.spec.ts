import { describe, expect, it, vi } from 'vitest';

import type { DiscoveryTarget } from '@/types/orchestration';
import { fetchDiscoveryTargetDetail } from '@/services/discovery-metadata';
import * as metadataService from '@/services/metadata';

describe('fetchDiscoveryTargetDetail', () => {
  it('uses target_kind and provider_id to request metadata detail', async () => {
    const target: DiscoveryTarget = {
      target_kind: 'track',
      provider: 'musicbrainz',
      provider_id: 'recording-123',
      display_title: 'Hello',
      display_subtitle: 'Adele',
      source_context: {
        chart_source: 'listenbrainz',
        chart_id: 'chart-1',
        chart_name: 'Top Tracks',
        rank: 1,
        chart_type: 'track',
      },
      conversion_ready: true,
      conversion_note: null,
      discovery_badges: ['top_track'],
    };

    const spy = vi
      .spyOn(metadataService, 'fetchMetadataDetail')
      .mockResolvedValue({ success: true, code: 'OK', message: 'ok', data: {} as never });

    await fetchDiscoveryTargetDetail(target);

    expect(spy).toHaveBeenCalledWith('track', 'recording-123');
  });

  it('throws when conversion_ready is false', async () => {
    const target: DiscoveryTarget = {
      target_kind: 'artist',
      provider: 'musicbrainz',
      provider_id: 'artist-1',
      display_title: 'Unknown Artist',
      display_subtitle: null,
      source_context: {
        chart_source: 'listenbrainz',
        chart_id: 'chart-1',
        chart_name: 'Top Artists',
        rank: 2,
        chart_type: 'artist',
      },
      conversion_ready: false,
      conversion_note: 'provider id missing',
      discovery_badges: [],
    };

    await expect(fetchDiscoveryTargetDetail(target)).rejects.toThrow('provider id missing');
  });
});
