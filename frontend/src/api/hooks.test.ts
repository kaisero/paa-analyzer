import { describe, it, expect } from 'vitest';
import { renderHook, waitFor } from '@testing-library/react';
import { http, HttpResponse } from 'msw';
import { server } from '../test/handlers';
import { useLogs, useStateBatch, useSession } from './hooks';
import { TestWrapper } from '../test/wrapper';

describe('useLogs — query param construction', () => {
  it('sends source, level, search, page, page_size as query params', async () => {
    let capturedUrl = '';
    server.use(
      http.get('/api/v1/sessions/:id/logs', ({ request }) => {
        capturedUrl = request.url;
        return HttpResponse.json({ data: [], meta: { total: 0, page: 1, page_size: 50, has_next: false } });
      }),
    );
    const { result } = renderHook(
      () => useLogs('s1', { source: 'Agent.Core.PAS', level: 'error', search: 'tunnel', page: 2, page_size: 50 }),
      { wrapper: TestWrapper },
    );
    await waitFor(() => expect(result.current.isFetched).toBe(true));
    const url = new URL(capturedUrl);
    expect(url.searchParams.get('source')).toBe('Agent.Core.PAS');
    expect(url.searchParams.get('level')).toBe('error');
    expect(url.searchParams.get('search')).toBe('tunnel');
    expect(url.searchParams.get('page')).toBe('2');
    expect(url.searchParams.get('page_size')).toBe('50');
  });

  it('omits level param when value is "all"', async () => {
    let capturedUrl = '';
    server.use(
      http.get('/api/v1/sessions/:id/logs', ({ request }) => {
        capturedUrl = request.url;
        return HttpResponse.json({ data: [], meta: { total: 0, page: 1, page_size: 100, has_next: false } });
      }),
    );
    const { result } = renderHook(
      () => useLogs('s1', { level: 'all' }),
      { wrapper: TestWrapper },
    );
    await waitFor(() => expect(result.current.isFetched).toBe(true));
    const url = new URL(capturedUrl);
    expect(url.searchParams.has('level')).toBe(false);
  });

  it('omits empty search param', async () => {
    let capturedUrl = '';
    server.use(
      http.get('/api/v1/sessions/:id/logs', ({ request }) => {
        capturedUrl = request.url;
        return HttpResponse.json({ data: [], meta: { total: 0, page: 1, page_size: 100, has_next: false } });
      }),
    );
    const { result } = renderHook(
      () => useLogs('s1', { search: '' }),
      { wrapper: TestWrapper },
    );
    await waitFor(() => expect(result.current.isFetched).toBe(true));
    const url = new URL(capturedUrl);
    expect(url.searchParams.has('search')).toBe(false);
  });

  it('is disabled when sessionId is undefined', () => {
    const { result } = renderHook(
      () => useLogs(undefined, {}),
      { wrapper: TestWrapper },
    );
    expect(result.current.isFetching).toBe(false);
  });
});

describe('useStateBatch', () => {
  it('joins keys with comma in URL', async () => {
    let capturedUrl = '';
    server.use(
      http.get('/api/v1/sessions/:id/state/batch', ({ request }) => {
        capturedUrl = request.url;
        return HttpResponse.json({ data: {} });
      }),
    );
    const { result } = renderHook(
      () => useStateBatch('s1', ['Agent.Core.status', 'Agent.Core.version']),
      { wrapper: TestWrapper },
    );
    await waitFor(() => expect(result.current.isFetched).toBe(true));
    const url = new URL(capturedUrl);
    const keys = url.searchParams.get('keys');
    expect(keys).toContain('Agent.Core.status');
    expect(keys).toContain('Agent.Core.version');
  });

  it('is disabled when keys array is empty', () => {
    const { result } = renderHook(
      () => useStateBatch('s1', []),
      { wrapper: TestWrapper },
    );
    expect(result.current.isFetching).toBe(false);
  });

  it('is disabled when sessionId is undefined', () => {
    const { result } = renderHook(
      () => useStateBatch(undefined, ['Agent.Core.status']),
      { wrapper: TestWrapper },
    );
    expect(result.current.isFetching).toBe(false);
  });
});

describe('useSession', () => {
  it('is disabled when id is undefined', () => {
    const { result } = renderHook(
      () => useSession(undefined),
      { wrapper: TestWrapper },
    );
    expect(result.current.isFetching).toBe(false);
  });
});
