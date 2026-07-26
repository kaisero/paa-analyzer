import { describe, it, expect } from 'vitest';
import { render, screen } from '@testing-library/react';
import { hipFixture } from '../../test/handlers';
import type { HipData } from '../../api/types';
import { NotDetectedStrip } from './NotDetectedStrip';

const macos = hipFixture.macos as unknown as HipData;
const empty = macos.cycles[0].report!.categories.filter((c) => c.products.length === 0);

describe('NotDetectedStrip', () => {
  it('names every zero-product category in one strip', () => {
    render(<NotDetectedStrip categories={empty} />);

    expect(screen.getByText('not detected:')).toBeInTheDocument();
    expect(screen.getByText('data-loss-prevention')).toBeInTheDocument();
    expect(screen.getByText('certificate')).toBeInTheDocument();
  });

  it('renders nothing when every category found products', () => {
    const { container } = render(<NotDetectedStrip categories={[]} />);
    expect(container).toBeEmptyDOMElement();
  });
});
