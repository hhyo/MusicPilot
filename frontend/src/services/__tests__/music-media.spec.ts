import { describe, expect, it, vi } from 'vitest';

const { post } = vi.hoisted(() => ({
  post: vi.fn(),
}));

vi.mock('@/services/http', () => ({
  http: {
    post,
  },
}));

import { resolveMusicMediaDetail } from '@/services/music-media';

describe('resolveMusicMediaDetail', () => {
  it('posts unified music media input to the media chain detail endpoint', async () => {
    post.mockResolvedValue({
      data: {
        success: true,
        code: 'MUSIC_MEDIA_DETAIL_OK',
        message: 'ok',
        data: {
          media: {
            entity_type: 'track',
            provider: 'musicbrainz',
            provider_id: 'recording-123',
            artist_names: ['Adele'],
            album_artist_names: [],
            related_artist_ids: [],
            related_track_ids: [],
            external_refs: {},
            match_evidence: [],
            diagnostics: [],
            release_context: {},
          },
          detail: {} as never,
        },
      },
    });

    const input = {
      entity_hint: 'track' as const,
      source_kind: 'discovery',
      title: 'Hello',
      subtitle: 'Adele',
      artist_names: ['Adele'],
      album_title: '25',
      album_artist_names: [],
      release_date: '2015-11-20',
      external_refs: {
        source_id: 'rss-entry-1',
      },
      source_context: {
        chart_id: 'rss-feed-1',
        chart_source: 'rss_feed',
      },
      raw_context: {
        family: 'netease_playlist_tracks',
      },
    };

    await resolveMusicMediaDetail(input);

    expect(post).toHaveBeenCalledWith('/media/resolve/detail', {
      input,
    });
  });
});
