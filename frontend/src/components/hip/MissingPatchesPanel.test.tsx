import { describe, it, expect } from 'vitest';
import { screen } from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import { http, HttpResponse } from 'msw';
import { renderWithProviders } from '../../test/wrapper';
import { server } from '../../test/handlers';
import hipFixture from '../../test/fixtures/hip.json';
import type { HipData } from '../../api/types';
import { MissingPatchesPanel } from './MissingPatchesPanel';

const macos = hipFixture.macos as unknown as HipData;
const windows = hipFixture.windows as unknown as HipData;

function renderPanel(hip: HipData) {
  // sessionId is real but view stays Grid in every test below, so useHipRaw
  // stays disabled and no MSW handler is needed for this suite.
  return renderWithProviders(
    <MissingPatchesPanel cycle={hip.cycles[0]} sessionId="s1" />,
  );
}

describe('MissingPatchesPanel', () => {
  it('aggregates patches across categories', () => {
    renderPanel(macos);
    expect(macos.cycles[0].counts.missing_patches).toBe(2);
    // Exact title: "macOS Tahoe" alone also matches the description and the
    // vendor/product cell, since the table renders all three.
    expect(screen.getByText('macOS Tahoe 26.5.2-25F84')).toBeInTheDocument();
  });

  it("renders the owning HIP category, titlecased, not the patch's own classification", () => {
    renderPanel(macos);
    // MissingPatch.category is the patch's own kind ("update"), not the HIP
    // category it came from ("patch-management") — the aggregated table has
    // to thread the HIP category in separately and titleCase it to match the
    // checklist row labels.
    // Both fixture patches come from the same category, so the column
    // renders "Patch Management" once per row (getByText would throw on the
    // multiple match) — see MissingPatchesTable.test.tsx's identical pattern.
    expect(screen.getAllByText('Patch Management').length).toBe(2);
  });

  it('always offers an XML view, even before a document is fetched', () => {
    renderPanel(macos);
    expect(screen.getByText('XML')).toBeInTheDocument();
  });

  it('reports an empty patch list plainly', () => {
    renderPanel(windows);
    expect(windows.cycles[0].counts.missing_patches).toBe(0);
    expect(screen.getByText(/no missing patches/i)).toBeInTheDocument();
  });

  it('flips to XML and renders the labelled missing-patches document', async () => {
    const user = userEvent.setup();
    renderPanel(macos);
    await user.click(screen.getByText('XML'));
    expect(await screen.findByText('missing-patches — PAComplianceMp')).toBeInTheDocument();
    expect(screen.queryByText(/no missing-patches document/i)).not.toBeInTheDocument();
  });

  it('shows the "no missing-patches document" note on Windows, which ships none', async () => {
    // The default handler only ever serves the macOS raw slice; override it
    // with the Windows raw slice (windowsRaw.raw_patches_xml is null in the
    // real parser output) to exercise the platform this note exists for.
    server.use(
      http.get('/api/v1/sessions/:id/hip/cycles/:index/raw', ({ params }) => {
        const raw = (hipFixture.windowsRaw as Record<string, unknown>)[params.index as string];
        return HttpResponse.json({ data: raw });
      }),
    );
    const user = userEvent.setup();
    renderPanel(windows);
    await user.click(screen.getByText('XML'));
    expect(await screen.findByText(/no missing-patches document/i)).toBeInTheDocument();
  });
});
