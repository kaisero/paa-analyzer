import { describe, it, expect } from 'vitest';
import { screen, waitFor } from '@testing-library/react';
import { Routes, Route } from 'react-router-dom';
import { renderWithProviders } from '../test/wrapper';
import { AgentStatusPage } from './AgentStatusPage';

function renderAgentStatusPage(sessionId = 'test123') {
  return renderWithProviders(
    <Routes>
      <Route path="/s/:sessionId/agent-status" element={<AgentStatusPage />} />
    </Routes>,
    { route: `/s/${sessionId}/agent-status` },
  );
}

describe('AgentStatusPage', () => {
  it('renders each section heading exactly once', async () => {
    renderAgentStatusPage();

    await waitFor(() => {
      expect(screen.getByText('System Overview')).toBeInTheDocument();
    });

    // The reported defect: SystemDetails, ForwardingTable and PacliTerminal
    // each rendered their own heading on top of the page's SectionTitle.
    expect(screen.getAllByText('System Details')).toHaveLength(1);
    expect(screen.getAllByText('Forwarding Profile')).toHaveLength(1);
    expect(screen.getAllByText('PACLI Terminal')).toHaveLength(1);
  });

  it('renders the lifted view toggles on the section titles', async () => {
    renderAgentStatusPage();

    await waitFor(() => {
      expect(screen.getByText('Forwarding Profile')).toBeInTheDocument();
    });

    // Two toggles are now on the page: System Details' View|Raw|JSON and
    // PacliTerminal's Raw|JSON, so 'Raw' and 'JSON' each appear twice and
    // 'View' (details-only) appears once.
    expect(screen.getByText('View')).toBeInTheDocument();
    expect(screen.getAllByText('Raw')).toHaveLength(2);
    expect(screen.getAllByText('JSON')).toHaveLength(2);
  });
});
