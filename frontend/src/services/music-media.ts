import { http } from '@/services/http';
import type { ApiResponse } from '@/types/metadata';
import type {
  MusicMediaInput,
  MusicResolveDetailResponseData,
  MusicResolveResponseData,
} from '@/types/music-media';

export async function resolveMusicMedia(input: MusicMediaInput): Promise<ApiResponse<MusicResolveResponseData>> {
  const { data } = await http.post<ApiResponse<MusicResolveResponseData>>('/media/resolve', { input });
  return data;
}

export async function resolveMusicMediaDetail(
  input: MusicMediaInput,
): Promise<ApiResponse<MusicResolveDetailResponseData>> {
  const { data } = await http.post<ApiResponse<MusicResolveDetailResponseData>>('/media/resolve/detail', { input });
  return data;
}
