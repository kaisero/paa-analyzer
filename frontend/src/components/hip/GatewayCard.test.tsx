import { describe, it, expect } from 'vitest';
import { screen } from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import { renderWithProviders } from '../../test/wrapper';
import hipFixture from '../../test/fixtures/hip.json';
import type { HipData } from '../../api/types';
import { GatewayCard } from './GatewayCard';

const macos = hipFixture.macos as unknown as HipData;
const windows = hipFixture.windows as unknown as HipData;

describe('GatewayCard', () => {
  it('summarises gateways by outcome', () => {
    renderWithProviders(<GatewayCard gateways={macos.gateways} />);
    expect(macos.gateways).toHaveLength(10);
    // Each status word appears once in the summary bar and again per visible
    // row carrying that status (top 5 by rank: South Korea/Finland failed,
    // UK/EPM sent, Israel-gw not needed), so assert counts, not presence.
    expect(screen.getAllByText('sent')).toHaveLength(3); // summary + UK + EPM
    expect(screen.getAllByText('not needed')).toHaveLength(2); // summary + Israel-gw
    expect(screen.getAllByText('failed')).toHaveLength(3); // summary + South Korea + Finland
  });

  it('surfaces failures first so a stale failure is not buried', () => {
    renderWithProviders(<GatewayCard gateways={macos.gateways} />);
    // South Korea is the oldest failure in the fixture and must be visible
    // before the user expands anything.
    expect(screen.getByText('South Korea')).toBeInTheDocument();
  });

  it('hides the tail behind a show-all control', async () => {
    const user = userEvent.setup();
    renderWithProviders(<GatewayCard gateways={macos.gateways} />);
    expect(screen.queryByText('amsterdam-gw')).not.toBeInTheDocument();
    await user.click(screen.getByText(/show all 10/i));
    expect(screen.getByText('amsterdam-gw')).toBeInTheDocument();
  });

  it('renders a calm empty state when the bundle has no gateway table', () => {
    expect(windows.gateways).toHaveLength(0);
    renderWithProviders(<GatewayCard gateways={windows.gateways} />);
    expect(screen.getByText(/no gateway data/i)).toBeInTheDocument();
  });
});
