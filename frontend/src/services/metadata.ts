import { http } from '@/services/http';
import type {
  ApiResponse,
  EntityType,
  MetadataDetail,
  MetadataSearchData,
  MetadataSearchPayload,
} from '@/types/metadata';

export async function searchMetadata(payload: MetadataSearchPayload): Promise<ApiResponse<MetadataSearchData>> {
  const { data } = await http.post<ApiResponse<MetadataSearchData>>('/metadata/search', payload);
  return data;
}

export async function fetchMetadataDetail(
  entityType: EntityType,
  entityId: string,
): Promise<ApiResponse<MetadataDetail>> {
  const routeMap: Record<EntityType, string> = {
    artist: `/metadata/artists/${entityId}`,
    album: `/metadata/albums/${entityId}`,
    track: `/metadata/tracks/${entityId}`,
  };

  const { data } = await http.get<ApiResponse<MetadataDetail>>(routeMap[entityType]);
  return data;
}
