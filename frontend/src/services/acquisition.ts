import { http } from '@/services/http';
import type {
  ApiDispatchResponse,
  ApiQueryBuildResponse,
  ApiSearchCandidatesResponse,
  ApiSearchJobResponse,
  DispatchPayload,
  SearchJobCreatePayload,
} from '@/types/acquisition';
import type { MusicMediaInput } from '@/types/music-media';

export async function previewQueryBuild(input: MusicMediaInput): Promise<ApiQueryBuildResponse> {
  const { data } = await http.post<ApiQueryBuildResponse>('/jobs/query-preview', {
    input,
  });
  return data;
}

export async function createSearchJob(payload: SearchJobCreatePayload): Promise<ApiSearchJobResponse> {
  const { data } = await http.post<ApiSearchJobResponse>('/jobs', payload);
  return data;
}

export async function executeSearchJob(jobId: string): Promise<ApiSearchJobResponse> {
  const { data } = await http.post<ApiSearchJobResponse>(`/jobs/${jobId}/run`);
  return data;
}

export async function fetchSearchJob(jobId: string): Promise<ApiSearchJobResponse> {
  const { data } = await http.get<ApiSearchJobResponse>(`/jobs/${jobId}`);
  return data;
}

export async function fetchSearchCandidates(jobId: string): Promise<ApiSearchCandidatesResponse> {
  const { data } = await http.get<ApiSearchCandidatesResponse>(`/jobs/${jobId}/results`);
  return data;
}

export async function dispatchCandidate(payload: DispatchPayload): Promise<ApiDispatchResponse> {
  const { data } = await http.post<ApiDispatchResponse>('/downloads/dispatch', payload);
  return data;
}
