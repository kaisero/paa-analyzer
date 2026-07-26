import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import { api } from './client';
import type {
  Session, LogSource, LogEntry, DataResponse, PaginatedResponse,
  StateKeyInfo, StateEntry, StateBatchResponse, ForwardingProfile,
  HipData, HipRaw,
} from './types';

const BASE = '/api/v1';

// Sessions
export function useSessions() {
  return useQuery({
    queryKey: ['sessions'],
    queryFn: () => api.get<DataResponse<Session[]>>(`${BASE}/sessions`),
  });
}

export function useSession(id: string | undefined) {
  return useQuery({
    queryKey: ['session', id],
    queryFn: () => api.get<DataResponse<Session>>(`${BASE}/sessions/${id}`),
    enabled: !!id,
  });
}

export function useCreateSession() {
  const qc = useQueryClient();
  return useMutation({
    mutationFn: async (file: File) => {
      const fd = new FormData();
      fd.append('file', file);
      return api.post<DataResponse<Session>>(`${BASE}/sessions`, fd);
    },
    onSuccess: () => qc.invalidateQueries({ queryKey: ['sessions'] }),
  });
}

export function useDeleteSession() {
  const qc = useQueryClient();
  return useMutation({
    mutationFn: (id: string) => api.del<DataResponse<{ deleted: boolean }>>(`${BASE}/sessions/${id}`),
    onSuccess: () => qc.invalidateQueries({ queryKey: ['sessions'] }),
  });
}

// Log sources
export function useLogSources(sessionId: string | undefined) {
  return useQuery({
    queryKey: ['logSources', sessionId],
    queryFn: () => api.get<DataResponse<LogSource[]>>(`${BASE}/sessions/${sessionId}/logs/sources`),
    enabled: !!sessionId,
  });
}

// Log entries
export interface LogQueryParams {
  source?: string;
  level?: string;
  search?: string;
  date_from?: string;
  date_to?: string;
  sort?: string;
  page?: number;
  page_size?: number;
}

// State
export function useStateKeys(sessionId: string | undefined) {
  return useQuery({
    queryKey: ['stateKeys', sessionId],
    queryFn: () => api.get<DataResponse<StateKeyInfo[]>>(`${BASE}/sessions/${sessionId}/state`),
    enabled: !!sessionId,
  });
}

export function useStateBatch(sessionId: string | undefined, keys: string[]) {
  const keysParam = keys.join(',');
  return useQuery({
    queryKey: ['stateBatch', sessionId, keysParam],
    queryFn: () => api.get<DataResponse<StateBatchResponse>>(
      `${BASE}/sessions/${sessionId}/state/batch?keys=${encodeURIComponent(keysParam)}`
    ),
    enabled: !!sessionId && keys.length > 0,
  });
}

export function useStateEntry(sessionId: string | undefined, key: string | undefined) {
  return useQuery({
    queryKey: ['stateEntry', sessionId, key],
    queryFn: () => api.get<DataResponse<StateEntry>>(
      `${BASE}/sessions/${sessionId}/state/${encodeURIComponent(key!)}`
    ),
    enabled: !!sessionId && !!key,
  });
}

export function useForwardingProfile(sessionId: string | undefined) {
  return useQuery({
    queryKey: ['forwardingProfile', sessionId],
    queryFn: () => api.get<DataResponse<ForwardingProfile>>(
      `${BASE}/sessions/${sessionId}/state/forwarding-profile`
    ),
    enabled: !!sessionId,
  });
}

// HIP (Host Information Profile)
export function useHip(sessionId: string | undefined) {
  return useQuery({
    queryKey: ['hip', sessionId],
    queryFn: () => api.get<DataResponse<HipData>>(`${BASE}/sessions/${sessionId}/hip`),
    enabled: !!sessionId,
  });
}

export function useHipRaw(sessionId: string | undefined, index: string | undefined, enabled: boolean) {
  return useQuery({
    queryKey: ['hipRaw', sessionId, index],
    queryFn: () => api.get<DataResponse<HipRaw>>(
      `${BASE}/sessions/${sessionId}/hip/cycles/${index}/raw`
    ),
    enabled: !!sessionId && index !== undefined && enabled,
  });
}

// Log entries
export function useLogs(sessionId: string | undefined, params: LogQueryParams) {
  const qs = new URLSearchParams();
  if (params.source) qs.set('source', params.source);
  if (params.level && params.level !== 'all') qs.set('level', params.level);
  if (params.search) qs.set('search', params.search);
  if (params.date_from) qs.set('date_from', params.date_from);
  if (params.date_to) qs.set('date_to', params.date_to);
  if (params.sort) qs.set('sort', params.sort);
  if (params.page) qs.set('page', String(params.page));
  if (params.page_size !== undefined) qs.set('page_size', String(params.page_size));

  return useQuery({
    queryKey: ['logs', sessionId, Object.fromEntries(qs)],
    queryFn: () => api.get<PaginatedResponse<LogEntry>>(`${BASE}/sessions/${sessionId}/logs?${qs}`),
    enabled: !!sessionId,
    placeholderData: (prev) => prev,
  });
}
