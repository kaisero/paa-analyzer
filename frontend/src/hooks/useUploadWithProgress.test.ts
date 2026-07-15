import { describe, it, expect } from 'vitest';
import { renderHook, act, waitFor } from '@testing-library/react';
import { http, HttpResponse } from 'msw';
import { server } from '../test/handlers';
import { useUploadWithProgress } from './useUploadWithProgress';
import { TestWrapper } from '../test/wrapper';

function renderUpload() {
  return renderHook(() => useUploadWithProgress(), { wrapper: TestWrapper });
}

function makeTestFile(name = 'test.zip') {
  return new File(['fake-zip-content'], name, { type: 'application/zip' });
}

/** Helper: create a readable SSE stream from a sequence of events. */
function sseStream(events: Array<Record<string, unknown>>) {
  const text = events.map((e) => `data: ${JSON.stringify(e)}\n\n`).join('');
  return new HttpResponse(text, {
    headers: { 'Content-Type': 'text/event-stream' },
  });
}

describe('useUploadWithProgress', () => {
  it('starts in idle state', () => {
    const { result } = renderUpload();
    expect(result.current.status).toBe('idle');
    expect(result.current.progress).toBe(0);
    expect(result.current.session).toBeNull();
    expect(result.current.error).toBeNull();
  });

  it('transitions to uploading on upload()', async () => {
    server.use(
      http.post('/api/v1/sessions/upload', () =>
        sseStream([{ stage: 'complete', progress: 100, detail: 'Done', session: { id: 'abc' } }]),
      ),
    );
    const { result } = renderUpload();
    act(() => { result.current.upload(makeTestFile()); });
    // Should immediately be in uploading state
    expect(result.current.status).toBe('uploading');
  });

  it('completes with session data on complete event', async () => {
    const session = { id: 'sess1', filename: 'bundle.zip', parse_status: 'complete' };
    server.use(
      http.post('/api/v1/sessions/upload', () =>
        sseStream([
          { stage: 'parsing', progress: 50, detail: 'Parsing...' },
          { stage: 'complete', progress: 100, detail: 'Done', session },
        ]),
      ),
    );
    const { result } = renderUpload();
    await act(async () => { await result.current.upload(makeTestFile()); });
    await waitFor(() => expect(result.current.status).toBe('complete'));
    expect(result.current.session).toEqual(session);
    expect(result.current.progress).toBe(100);
  });

  it('transitions to error on error event', async () => {
    server.use(
      http.post('/api/v1/sessions/upload', () =>
        sseStream([
          { stage: 'parsing', progress: 30, detail: 'Parsing...' },
          { stage: 'error', progress: -1, detail: 'ZIP is corrupt' },
        ]),
      ),
    );
    const { result } = renderUpload();
    await act(async () => { await result.current.upload(makeTestFile()); });
    await waitFor(() => expect(result.current.status).toBe('error'));
    expect(result.current.error).toBe('ZIP is corrupt');
  });

  it('transitions to error on HTTP error response', async () => {
    server.use(
      http.post('/api/v1/sessions/upload', () =>
        HttpResponse.json({ detail: 'Only .zip files accepted' }, { status: 400 }),
      ),
    );
    const { result } = renderUpload();
    await act(async () => { await result.current.upload(makeTestFile()); });
    await waitFor(() => expect(result.current.status).toBe('error'));
    expect(result.current.error).toBe('Only .zip files accepted');
  });

  it('transitions to error on network failure', async () => {
    server.use(
      http.post('/api/v1/sessions/upload', () => HttpResponse.error()),
    );
    const { result } = renderUpload();
    await act(async () => { await result.current.upload(makeTestFile()); });
    await waitFor(() => expect(result.current.status).toBe('error'));
    expect(result.current.error).toBeTruthy();
  });

  it('reset() returns to idle state', async () => {
    const session = { id: 'r1' };
    server.use(
      http.post('/api/v1/sessions/upload', () =>
        sseStream([{ stage: 'complete', progress: 100, detail: 'Done', session }]),
      ),
    );
    const { result } = renderUpload();
    await act(async () => { await result.current.upload(makeTestFile()); });
    await waitFor(() => expect(result.current.status).toBe('complete'));
    act(() => result.current.reset());
    expect(result.current.status).toBe('idle');
    expect(result.current.progress).toBe(0);
    expect(result.current.session).toBeNull();
  });

  it('updates progress during intermediate events', async () => {
    server.use(
      http.post('/api/v1/sessions/upload', () =>
        sseStream([
          { stage: 'extracting', progress: 10, detail: 'Opening ZIP...' },
          { stage: 'parsing', progress: 55, detail: 'Parsing file 5 of 10' },
          { stage: 'complete', progress: 100, detail: 'Done', session: { id: 'x' } },
        ]),
      ),
    );
    const { result } = renderUpload();
    await act(async () => { await result.current.upload(makeTestFile()); });
    await waitFor(() => expect(result.current.status).toBe('complete'));
    // After completion, progress should be 100
    expect(result.current.progress).toBe(100);
  });
});
