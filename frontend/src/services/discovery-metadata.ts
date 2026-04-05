import { fetchMetadataDetail } from '@/services/metadata';
import type { DiscoveryTarget } from '@/types/orchestration';

export async function fetchDiscoveryTargetDetail(target: DiscoveryTarget) {
  if (!target.conversion_ready) {
    throw new Error(target.conversion_note || '当前榜单项暂不支持 metadata detail。');
  }

  return fetchMetadataDetail(target.target_kind, target.provider_id);
}
