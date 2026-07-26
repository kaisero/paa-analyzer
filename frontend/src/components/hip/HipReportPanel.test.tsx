import { describe, it, expect } from 'vitest';
import { fireEvent, screen, within } from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import { http, HttpResponse } from 'msw';
import { renderWithProviders } from '../../test/wrapper';
import { server } from '../../test/handlers';
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
    // The checklist and patches titles stay fixed in every view mode
    // (Tasks 7-8); their counts are separate notes, not part of the title.
    expect(screen.getByText('Compliance Checklist', { selector: '.ant-card-head-title' })).toBeInTheDocument();
    expect(screen.getByText('Missing Patches', { selector: '.ant-card-head-title' })).toBeInTheDocument();
  });

  it('lands with every checklist row folded', () => {
    renderWithProviders(<HipReportPanel hip={macos} sessionId="s1" />);
    expect(screen.queryByText('Cortex XDR')).not.toBeInTheDocument();
  });

  it('each module switches view independently', async () => {
    const user = userEvent.setup();
    renderWithProviders(<HipReportPanel hip={macos} sessionId="s1" />);
    // Panel renders the title into the antd Card's own header element;
    // `.closest('div')` on the title text returns that same div (it holds no
    // toggle) — scope to the whole card instead.
    const systemCard = screen.getByText('System').closest('.ant-card') as HTMLElement;
    await user.click(within(systemCard).getByText('JSON'));
    // The checklist stays in View: its rows are still listed.
    expect(screen.getByText('Anti Malware')).toBeInTheDocument();
  });

  it('renders the Windows slice without gateways or custom checks', () => {
    renderWithProviders(<HipReportPanel hip={windows} sessionId="s1" />);
    expect(screen.getByText(/no gateway data/i)).toBeInTheDocument();
    expect(screen.getByText('No custom checks collected for this platform.')).toBeInTheDocument();
  });

  it('gives Panel no inline height, so a shorter header card cannot be stretched to fill its grid row', () => {
    // I1: Panel used to declare `height: '100%'`. Once HipReportPanel made
    // the `.ant-card` the direct grid item, that percentage resolved against
    // the grid row's block size (the taller card), filling the shorter card
    // with dead space regardless of `alignItems: 'start'` on the grid
    // container — a declared height overrides align-self. jsdom cannot
    // measure the resulting layout, so this test cannot assert the visual
    // outcome directly; it pins the actual mechanism instead. The grid
    // container still needs `alignItems: 'start'` (so a card's height stays
    // content-driven rather than stretching to `1fr` in the first place) —
    // that half is checked here too, but it is not sufficient on its own.
    renderWithProviders(<HipReportPanel hip={macos} sessionId="s1" />);
    const systemCard = screen.getByText('System').closest('.ant-card') as HTMLElement;
    const gatewayCard = screen.getByText('Gateways').closest('.ant-card') as HTMLElement;
    expect(systemCard.style.height).toBe('');
    expect(gatewayCard.style.height).toBe('');
    const headerCards = systemCard.parentElement!;
    expect(headerCards.style.display).toBe('grid');
    expect(headerCards.style.alignItems).toBe('start');
  });

  it('dedupes the raw-document fetch when both modules switch to Raw', async () => {
    // I4: this claim ("TanStack Query dedupes on queryKey, so this is still
    // one request even when both modules want Raw at once") was previously
    // asserted only in comments in ComplianceChecklist.tsx and
    // MissingPatchesPanel.tsx — nothing failed if it stopped being true.
    let requestCount = 0;
    server.use(
      http.get('/api/v1/sessions/:id/hip/cycles/:index/raw', ({ params }) => {
        requestCount += 1;
        const raw = (hipFixture.macosRaw as Record<string, unknown>)[params.index as string];
        return HttpResponse.json({ data: raw });
      }),
    );
    renderWithProviders(<HipReportPanel hip={macos} sessionId="s1" />);
    const checklistCard = screen
      .getByText('Compliance Checklist', { selector: '.ant-card-head-title' })
      .closest('.ant-card') as HTMLElement;
    const patchesCard = screen
      .getByText('Missing Patches', { selector: '.ant-card-head-title' })
      .closest('.ant-card') as HTMLElement;

    // Flip both modules to Raw in the same tick, before either fetch
    // resolves — `fireEvent` (unlike `userEvent`) doesn't await anything
    // between the two clicks, so the shared queryKey has to dedupe the
    // in-flight request rather than each panel firing its own.
    fireEvent.click(within(checklistCard).getByText('Raw'));
    fireEvent.click(within(patchesCard).getByText('Raw'));
    await screen.findByText('hip-report — PACompliance');
    await screen.findByText('missing-patches — PAComplianceMp');

    expect(requestCount).toBe(1);
  });
});
