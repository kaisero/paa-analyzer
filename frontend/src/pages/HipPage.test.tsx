import { describe, it, expect } from 'vitest';
import { screen, waitFor } from '@testing-library/react';
import { http, HttpResponse } from 'msw';
import { Routes, Route } from 'react-router-dom';
import { renderWithProviders } from '../test/wrapper';
import { server, hipFixture } from '../test/handlers';
import { HipPage } from './HipPage';

function renderHipPage(sessionId = 'test123') {
  return renderWithProviders(
    <Routes>
      <Route path="/s/:sessionId/hip" element={<HipPage />} />
    </Routes>,
    { route: `/s/${sessionId}/hip` },
  );
}

describe('HipPage', () => {
  it('renders HIP data from the API', async () => {
    renderHipPage();

    await waitFor(() => {
      expect(screen.getByText('Host Information Profile')).toBeInTheDocument();
    });

    // hipFixture.macos is the real generated fixture -- 2 cycles.
    expect(screen.getByText(/2 cycles/)).toBeInTheDocument();
  });

  it('shows the empty state when the API returns no cycles', async () => {
    server.use(
      http.get('/api/v1/sessions/:id/hip', () =>
        HttpResponse.json({ data: hipFixture.empty }),
      ),
    );

    renderHipPage();

    await waitFor(() => {
      expect(screen.getByText('No HIP Data Found')).toBeInTheDocument();
    });
    expect(screen.getByText(/PACompliance.log/)).toBeInTheDocument();
  });
});
