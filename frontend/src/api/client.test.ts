import { describe, it, expect } from 'vitest';
import { http, HttpResponse } from 'msw';
import { server } from '../test/handlers';
import { api, ApiError } from './client';

describe('api.get', () => {
  it('returns parsed JSON on success', async () => {
    server.use(
      http.get('/test/ok', () => HttpResponse.json({ value: 42 })),
    );
    const result = await api.get<{ value: number }>('/test/ok');
    expect(result.value).toBe(42);
  });

  it('throws ApiError with status on non-ok response', async () => {
    server.use(
      http.get('/test/fail', () => HttpResponse.json({ detail: 'Not found' }, { status: 404 })),
    );
    try {
      await api.get('/test/fail');
      expect.fail('should have thrown');
    } catch (err) {
      expect(err).toBeInstanceOf(ApiError);
      expect((err as ApiError).status).toBe(404);
      expect((err as ApiError).detail).toBe('Not found');
    }
  });

  it('extracts detail from JSON error body', async () => {
    server.use(
      http.get('/test/json-err', () =>
        HttpResponse.json({ detail: 'Session not found' }, { status: 404 }),
      ),
    );
    try {
      await api.get('/test/json-err');
      expect.fail('should have thrown');
    } catch (err) {
      expect((err as ApiError).detail).toBe('Session not found');
    }
  });

  it('uses raw text when error body is not JSON', async () => {
    server.use(
      http.get('/test/text-err', () =>
        new HttpResponse('Internal Server Error', { status: 500 }),
      ),
    );
    try {
      await api.get('/test/text-err');
      expect.fail('should have thrown');
    } catch (err) {
      expect((err as ApiError).detail).toBe('Internal Server Error');
    }
  });
});

describe('api.post', () => {
  it('sends JSON body with Content-Type header', async () => {
    let capturedContentType: string | null = null;
    server.use(
      http.post('/test/json', async ({ request }) => {
        capturedContentType = request.headers.get('content-type');
        return HttpResponse.json({ ok: true });
      }),
    );
    await api.post('/test/json', { key: 'value' });
    expect(capturedContentType).toBe('application/json');
  });

  it('does NOT set Content-Type for FormData (browser sets multipart boundary)', async () => {
    let capturedContentType: string | null = null;
    server.use(
      http.post('/test/upload', async ({ request }) => {
        capturedContentType = request.headers.get('content-type');
        return HttpResponse.json({ ok: true });
      }),
    );
    const fd = new FormData();
    fd.append('file', new Blob(['test']), 'test.zip');
    await api.post('/test/upload', fd);
    // Browser automatically sets multipart/form-data with boundary — should NOT be application/json
    expect(capturedContentType).not.toBe('application/json');
  });
});

describe('api.del', () => {
  it('sends DELETE request and returns response', async () => {
    server.use(
      http.delete('/test/item', () => HttpResponse.json({ deleted: true })),
    );
    const result = await api.del<{ deleted: boolean }>('/test/item');
    expect(result.deleted).toBe(true);
  });
});
