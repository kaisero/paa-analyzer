import { describe, it, expect } from 'vitest';
import { screen } from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import { renderWithProviders } from '../../test/wrapper';
import hipFixture from '../../test/fixtures/hip.json';
import type { HipData } from '../../api/types';
import { ComplianceChecklist } from './ComplianceChecklist';

const macos = hipFixture.macos as unknown as HipData;
const windows = hipFixture.windows as unknown as HipData;

function renderList(hip: HipData) {
  // sessionId is real but view stays Grid in every test below, so useHipRaw
  // stays disabled and no MSW handler is needed for this suite.
  return renderWithProviders(
    <ComplianceChecklist cycle={hip.cycles[0]} sessionId="s1" />,
  );
}

describe('ComplianceChecklist', () => {
  it('renders every category folded, including the empty ones', () => {
    renderList(macos);
    const names = macos.cycles[0].report!.categories.map((c) => c.name);
    expect(names).toHaveLength(7);
    expect(screen.getByText('Anti Malware')).toBeInTheDocument();
    expect(screen.getByText('Certificate')).toBeInTheDocument();
    // Folded: no product detail on screen before any interaction.
    expect(screen.queryByText('Cortex XDR')).not.toBeInTheDocument();
  });

  it('carries a synthesized verdict on the folded row', () => {
    renderList(macos);
    expect(
      screen.getByText(
        'Cortex XDR real time on  ·  Xprotect real time off  ·  Gatekeeper unverifiable',
        // RTL's default text normalizer collapses runs of whitespace, which
        // would silently pass even if the two-space separator regressed to
        // one space. Disable collapsing so this genuinely pins the verdict's
        // '  ·  ' separator (per global-constraints: two spaces each side).
        { collapseWhitespace: false },
      ),
    ).toBeInTheDocument();
  });

  it('counts patch-management errors from the flat list, not from products', () => {
    // Regression guard for the shipped bug: two errors carry product: null, so
    // summing product.errors renders "0 errors" for a category that has two.
    renderList(macos);
    expect(screen.getByText('2 errors')).toBeInTheDocument();
  });

  it('expands a row in place', async () => {
    const user = userEvent.setup();
    renderList(macos);
    await user.click(screen.getByText('Anti Malware'));
    expect(screen.getByText('Cortex XDR')).toBeInTheDocument();
  });

  it('expands and collapses every row from its own header', async () => {
    const user = userEvent.setup();
    renderList(macos);
    await user.click(screen.getByText('Expand All'));
    expect(screen.getByText('Cortex XDR')).toBeInTheDocument();
    await user.click(screen.getByText('Collapse All'));
    expect(screen.queryByText('Cortex XDR')).not.toBeInTheDocument();
  });

  it('shows unattached OPSWAT errors that no product row can carry', async () => {
    const user = userEvent.setup();
    renderList(macos);
    await user.click(screen.getByText('Patch Management'));
    expect(screen.getByText(/other opswat errors/i)).toBeInTheDocument();
  });

  it('adds a Missing Patches heading inside the expanded category, now that the table lost its own card title', async () => {
    const user = userEvent.setup();
    renderList(macos);
    await user.click(screen.getByText('Patch Management'));
    expect(screen.getByText('Missing Patches (2)')).toBeInTheDocument();
  });

  it('handles a platform with no custom checks', () => {
    renderList(windows);
    expect(screen.getByText('No custom checks collected for this platform.')).toBeInTheDocument();
  });
});
