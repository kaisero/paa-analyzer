import { useState, useCallback } from 'react';
import { useQueryClient } from '@tanstack/react-query';
import type { Session } from '../api/types';

interface UploadState {
  status: 'idle' | 'uploading' | 'complete' | 'error';
  stage: string;
  progress: number;
  detail: string;
  error: string | null;
  session: Session | null;
}

const INITIAL: UploadState = {
  status: 'idle',
  stage: '',
  progress: 0,
  detail: '',
  error: null,
  session: null,
};

export function useUploadWithProgress() {
  const [state, setState] = useState<UploadState>(INITIAL);
  const qc = useQueryClient();

  const upload = useCallback(async (file: File) => {
    setState({ ...INITIAL, status: 'uploading', detail: 'Uploading...' });

    const fd = new FormData();
    fd.append('file', file);

    try {
      const res = await fetch('/api/v1/sessions/upload', { method: 'POST', body: fd });

      if (!res.ok) {
        const text = await res.text();
        let detail = text;
        try { detail = JSON.parse(text).detail; } catch { /* use raw */ }
        setState((s) => ({ ...s, status: 'error', error: detail }));
        return;
      }

      const reader = res.body!.getReader();
      const decoder = new TextDecoder();
      let buffer = '';

      while (true) {
        const { done, value } = await reader.read();
        if (done) break;
        buffer += decoder.decode(value, { stream: true });

        const chunks = buffer.split('\n\n');
        buffer = chunks.pop()!;

        for (const chunk of chunks) {
          const match = chunk.match(/^data: (.+)$/m);
          if (!match) continue;
          try {
            const event = JSON.parse(match[1]);
            if (event.stage === 'complete') {
              setState((s) => ({
                ...s,
                status: 'complete',
                stage: 'complete',
                progress: 100,
                detail: 'Done',
                session: event.session,
              }));
              qc.invalidateQueries({ queryKey: ['sessions'] });
            } else if (event.stage === 'error') {
              setState((s) => ({ ...s, status: 'error', error: event.detail }));
            } else {
              setState((s) => ({
                ...s,
                stage: event.stage,
                progress: event.progress,
                detail: event.detail,
              }));
            }
          } catch { /* skip malformed */ }
        }
      }
    } catch (err) {
      setState((s) => ({ ...s, status: 'error', error: err instanceof Error ? err.message : 'Upload failed' }));
    }
  }, [qc]);

  const reset = useCallback(() => setState(INITIAL), []);

  return { ...state, upload, reset };
}
