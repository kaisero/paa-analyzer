import { http, HttpResponse } from 'msw';
import { setupServer } from 'msw/node';

// -- Test data factories --

export function makeSession(overrides: Record<string, unknown> = {}) {
  return {
    id: 'test123',
    filename: 'bundle.zip',
    file_size: 1024,
    created_at: '2026-04-03T09:00:00+00:00',
    parse_status: 'complete',
    parse_error: null,
    parse_duration_ms: 150,
    total_log_entries: 500,
    total_log_sources: 5,
    total_state_files: 10,
    ...overrides,
  };
}

export function makeLogSource(overrides: Record<string, unknown> = {}) {
  return {
    source: 'Agent.Core.PAS',
    total_entries: 100,
    levels: { info: 80, error: 15, warning: 5 },
    time_range: { from: '2026-04-03T07:00:00+00:00', to: '2026-04-03T09:00:00+00:00' },
    module: 'Agent',
    component: 'Core',
    ...overrides,
  };
}

export function makeLogEntry(overrides: Record<string, unknown> = {}) {
  return {
    timestamp: '2026-04-03T07:24:40+00:00',
    level: 'info',
    source: 'PAS',
    message: 'Test log message',
    ...overrides,
  };
}

// -- Default handlers --

const handlers = [
  http.get('/api/v1/sessions', () =>
    HttpResponse.json({ data: [makeSession()] }),
  ),

  http.get('/api/v1/sessions/:id', ({ params }) =>
    HttpResponse.json({ data: makeSession({ id: params.id }) }),
  ),

  http.post('/api/v1/sessions', () =>
    HttpResponse.json({ data: makeSession() }, { status: 201 }),
  ),

  http.delete('/api/v1/sessions/:id', () =>
    HttpResponse.json({ data: { deleted: true } }),
  ),

  http.get('/api/v1/sessions/:id/logs/sources', () =>
    HttpResponse.json({
      data: [
        makeLogSource(),
        makeLogSource({ source: 'Agent.Core.traffic_log_json', total_entries: 50, module: 'Agent', component: 'Core' }),
      ],
    }),
  ),

  http.get('/api/v1/sessions/:id/logs', () =>
    HttpResponse.json({
      data: [makeLogEntry(), makeLogEntry({ level: 'error', message: 'Something broke' })],
      meta: { total: 2, page: 1, page_size: 100, has_next: false },
    }),
  ),

  http.get('/api/v1/sessions/:id/state', () =>
    HttpResponse.json({
      data: [
        { key: 'Agent.Core.status', module: 'Agent', component: 'Core', name: 'status' },
      ],
    }),
  ),

  http.get('/api/v1/sessions/:id/state/batch', () =>
    HttpResponse.json({
      data: {
        'Agent.Core.status': {
          _meta: { type: 'state', module: 'Agent', component: 'Core', source_file: 'pacli_status.log', name: 'status' },
          data: { state: 'Enabled', mode: 'Always On', epm_status: 'Up', local_hostname: 'TEST-HOST', username: 'user@example.com' },
        },
      },
    }),
  ),

  http.get('/api/v1/sessions/:id/state/forwarding-profile', () =>
    HttpResponse.json({
      data: { rules: [], flags: [] },
    }),
  ),

  http.get('/api/v1/sessions/:id/dashboard', () =>
    HttpResponse.json({
      data: { session_id: 'test123', filename: 'bundle.zip', total_log_entries: 500, total_log_sources: 5, total_state_files: 10, parse_duration_ms: 150 },
    }),
  ),
];

export const server = setupServer(...handlers);
