import { describe, it, expect } from 'vitest';
import { render, screen } from '@testing-library/react';
import { hipFixture } from '../../test/handlers';
import type { HipData } from '../../api/types';
import { ProductRow } from './ProductRow';

const macos = hipFixture.macos as unknown as HipData;
const categories = macos.cycles[0].report!.categories;
const antiMalware = categories.find((c) => c.name === 'anti-malware')!;
const diskEncryption = categories.find((c) => c.name === 'disk-encryption')!;

describe('ProductRow', () => {
  it('renders name, version, vendor and labelled attributes', () => {
    const product = antiMalware.products.find((p) => p.name === 'Cortex XDR')!;
    render(<ProductRow product={product} />);

    expect(screen.getByText('Cortex XDR')).toBeInTheDocument();
    expect(screen.getByText(/9\.0\.0 · Palo Alto Networks, Inc\./)).toBeInTheDocument();
    expect(screen.getByText('real-time protection')).toBeInTheDocument();
    expect(screen.getByText('yes')).toBeInTheDocument();
    expect(screen.getByText('last full scan')).toBeInTheDocument();
  });

  it('shows the OPSWAT error count for a product that has errors', () => {
    const product = antiMalware.products.find((p) => p.errors.length > 0)!;
    render(<ProductRow product={product} />);
    expect(screen.getByText(`${product.errors.length} err`)).toBeInTheDocument();
  });

  it('omits the error marker for a clean product', () => {
    const product = antiMalware.products.find((p) => p.errors.length === 0)!;
    render(<ProductRow product={product} />);
    expect(screen.queryByText(/ err$/)).not.toBeInTheDocument();
  });

  it('renders the definitions version and date extras', () => {
    const product = antiMalware.products.find((p) => p.name === 'Cortex XDR')!;
    render(<ProductRow product={product} />);

    expect(screen.getByText('definitions')).toBeInTheDocument();
    expect(screen.getByText(product.def_version!)).toBeInTheDocument();
    expect(screen.getByText('definition date')).toBeInTheDocument();
    expect(screen.getByText(product.def_date!)).toBeInTheDocument();
  });

  it('lists per-drive encryption state instead of the raw drives attribute', () => {
    const product = diskEncryption.products[0];
    render(<ProductRow product={product} />);

    expect(screen.getByText('Macintosh HD')).toBeInTheDocument();
    expect(screen.getAllByText('encrypted').length).toBe(product.drives!.length);
    expect(screen.queryByText('drives')).not.toBeInTheDocument();
  });
});
