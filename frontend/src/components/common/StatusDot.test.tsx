import { describe, it, expect } from 'vitest';
import { render, screen } from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import { hipFixture } from '../../test/handlers';
import type { HipData } from '../../api/types';
import { StatusDot } from './StatusDot';

const macos = hipFixture.macos as unknown as HipData;
const antiMalware = macos.cycles[0].report!.categories.find((c) => c.name === 'anti-malware')!;

describe('StatusDot', () => {
  it('renders each status the fixture carries', () => {
    render(
      <div>
        {antiMalware.products.map((p) => (
          <StatusDot key={p.name} status={p.status} />
        ))}
      </div>,
    );

    // Cortex XDR ok, Xprotect warn, Gatekeeper unknown.
    expect(screen.getByLabelText('status ok')).toBeInTheDocument();
    expect(screen.getByLabelText('status warn')).toBeInTheDocument();
    expect(screen.getByLabelText('status unknown')).toBeInTheDocument();
  });

  it('renders the not-detected state used by empty categories', () => {
    const empty = macos.cycles[0].report!.categories.find((c) => c.products.length === 0)!;
    render(<StatusDot status={empty.status} reason={empty.status_reason} />);
    expect(screen.getByLabelText('status not-detected')).toBeInTheDocument();
  });

  it('shows status_reason as a tooltip on hover', async () => {
    const user = userEvent.setup();
    const product = antiMalware.products.find((p) => p.status === 'unknown')!;
    render(<StatusDot status={product.status} reason={product.status_reason} />);

    await user.hover(screen.getByLabelText('status unknown'));
    expect(await screen.findByText(product.status_reason!)).toBeInTheDocument();
  });
});
