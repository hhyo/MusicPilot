import { http } from '@/services/http';
import type { ApiMusicResolveDetailResponse, MusicMediaInput } from '@/types/music-media';

export async function resolveMusicMediaDetail(input: MusicMediaInput): Promise<ApiMusicResolveDetailResponse> {
  const { data } = await http.post<ApiMusicResolveDetailResponse>('/media/resolve/detail', {
    input,
  });
  return data;
}
