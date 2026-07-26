import { describe, it, expect } from 'vitest';
import { screen, within } from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import { renderWithProviders } from '../../test/wrapper';
import hipFixture from '../../test/fixtures/hip.json';
import type { HipData } from '../../api/types';
import { HipReportPanel } from './HipReportPanel';

const macos = hipFixture.macos as unknown as HipData;
const windows = hipFixture.windows as unknown as HipData;

describe('HipReportPanel', () => {
  it('renders header, both header cards, the checklist and the patches module', () => {
    renderWithProviders(<HipReportPanel hip={macos} sessionId="s1" />);
    expect(screen.getByRole('heading', { name: 'HIP Report' })).toBeInTheDocument();
    expect(screen.getByText('System')).toBeInTheDocument();
    expect(screen.getByText('Gateways')).toBeInTheDocument();
    // The checklist title stays "Compliance Checklist" in every view mode
    // (Task 7); the category count is a separate note, not part of the title.
    expect(screen.getByText('Compliance Checklist')).toBeInTheDocument();
    expect(screen.getByText(/Missing Patches ·/)).toBeInTheDocument();
  });

  it('lands with every checklist row folded', () => {
    renderWithProviders(<HipReportPanel hip={macos} sessionId="s1" />);
    expect(screen.queryByText('Cortex XDR')).not.toBeInTheDocument();
  });

  it('each module switches view independently', async () => {
    const user = userEvent.setup();
    renderWithProviders(<HipReportPanel hip={macos} sessionId="s1" />);
    // HipCard renders the title into the antd Card's own header element;
    // `.closest('div')` on the title text returns that same div (it holds no
    // toggle) — scope to the whole card instead.
    const systemCard = screen.getByText('System').closest('.ant-card') as HTMLElement;
    await user.click(within(systemCard).getByText('JSON'));
    // The checklist stays in Grid: its rows are still listed.
    expect(screen.getByText('Anti Malware')).toBeInTheDocument();
  });

  it('renders the Windows slice without gateways or custom checks', () => {
    renderWithProviders(<HipReportPanel hip={windows} sessionId="s1" />);
    expect(screen.getByText(/no gateway data/i)).toBeInTheDocument();
    expect(screen.getByText('No custom checks collected for this platform.')).toBeInTheDocument();
  });

  it('lays the header cards out side by side without stretching the gateway card', () => {
    renderWithProviders(<HipReportPanel hip={macos} sessionId="s1" />);
    // alignItems: 'start' (Step 3) is load-bearing: without it the gateway
    // card stretches to the system card's height and renders as a large
    // empty box on a bundle with no gateways.
    const headerCards = screen.getByText('System').closest('.ant-card')!.parentElement!;
    expect(headerCards.style.display).toBe('grid');
    expect(headerCards.style.alignItems).toBe('start');
  });
});
