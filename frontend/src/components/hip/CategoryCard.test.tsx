import { describe, it, expect } from 'vitest';
import { render, screen } from '@testing-library/react';
import { hipFixture } from '../../test/handlers';
import type { HipData } from '../../api/types';
import { CategoryCard } from './CategoryCard';

const macos = hipFixture.macos as unknown as HipData;
const cycle = macos.cycles[0];
const antiMalware = cycle.report!.categories.find((c) => c.name === 'anti-malware')!;

describe('CategoryCard', () => {
  it('renders the category name, product count and every product', () => {
    render(<CategoryCard category={antiMalware} timingS={cycle.category_timings['anti-malware']} />);

    expect(screen.getByText('anti-malware')).toBeInTheDocument();
    expect(screen.getByText('3 products')).toBeInTheDocument();
    for (const product of antiMalware.products) {
      expect(screen.getByText(product.name!)).toBeInTheDocument();
    }
  });

  it('carries the category status dot', () => {
    render(<CategoryCard category={antiMalware} />);
    // anti-malware is `warn` on the macOS fixture; product dots add ok/warn/unknown.
    expect(screen.getAllByLabelText(`status ${antiMalware.status}`).length).toBeGreaterThan(0);
  });

  it('singularises the count for a one-product category', () => {
    const diskEncryption = cycle.report!.categories.find((c) => c.name === 'disk-encryption')!;
    render(<CategoryCard category={diskEncryption} />);
    expect(screen.getByText('1 product')).toBeInTheDocument();
  });
});
