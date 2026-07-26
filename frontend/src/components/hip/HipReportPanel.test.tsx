import { describe, it, expect } from 'vitest';
import { screen, waitFor } from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import { http, HttpResponse } from 'msw';
import { renderWithProviders } from '../../test/wrapper';
import { server, hipFixture } from '../../test/handlers';
import type { HipData } from '../../api/types';
import { HipReportPanel } from './HipReportPanel';

const macos = hipFixture.macos as unknown as HipData;
const windows = hipFixture.windows as unknown as HipData;
const macosRaw = hipFixture.macosRaw as Record<string, { raw_xml: string }>;

function renderPanel(hip: HipData) {
  return renderWithProviders(<HipReportPanel hip={hip} sessionId="test123" />);
}

describe('HipReportPanel', () => {
  it('opens on the newest cycle in Grid mode without fetching raw documents', () => {
    // Raw is only fetched on toggle; the MSW server errors on unhandled
    // requests, so an unexpected fetch would fail the suite anyway.
    renderPanel(macos);

    expect(screen.getByText('1 of 2')).toBeInTheDocument();
    expect(screen.getByText('Cortex XDR')).toBeInTheDocument();
    expect(screen.queryByText(/hip-report/)).not.toBeInTheDocument();
  });

  it('switches to the selected cycle', async () => {
    const user = userEvent.setup();
    renderPanel(macos);

    await user.click(screen.getByRole('combobox'));
    const options = await screen.findAllByText(/^\d{4}-\d{2}-\d{2} /);
    await user.click(options[options.length - 1]);

    expect(await screen.findByText('2 of 2')).toBeInTheDocument();
  });

  it('fetches and labels both raw documents in XML mode', async () => {
    const user = userEvent.setup();
    renderPanel(macos);

    await user.click(screen.getByText('XML'));

    expect(await screen.findByText('hip-report — PACompliance')).toBeInTheDocument();
    expect(screen.getByText('missing-patches — PAComplianceMp')).toBeInTheDocument();
    await waitFor(() =>
      expect(screen.getByText(new RegExp('<hip-report'))).toBeInTheDocument(),
    );
    expect(macosRaw['0'].raw_xml).toContain('<hip-report');
  });

  it('shows the parsed model with the raw documents in JSON mode', async () => {
    const user = userEvent.setup();
    renderPanel(macos);

    await user.click(screen.getByText('JSON'));

    expect(await screen.findByText('cycle 0 — parsed model')).toBeInTheDocument();
    expect(screen.getByText(/"raw_patches_xml"/)).toBeInTheDocument();
  });

  it('notes the absent missing-patches document on the Windows bundle', async () => {
    server.use(
      http.get('/api/v1/sessions/:id/hip/cycles/:index/raw', () =>
        HttpResponse.json({ data: hipFixture.windowsRaw['0'] }),
      ),
    );
    const user = userEvent.setup();
    renderPanel(windows);

    await user.click(screen.getByText('XML'));

    expect(
      await screen.findByText('No missing-patches document was captured for this cycle.'),
    ).toBeInTheDocument();
  });
});
