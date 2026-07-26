import { describe, it, expect } from 'vitest';
import { render, screen } from '@testing-library/react';
import { hipFixture } from '../../test/handlers';
import type { HipData } from '../../api/types';
import { CategoryGrid, CATEGORY_LAYOUT } from './CategoryGrid';

const macos = hipFixture.macos as unknown as HipData;
const windows = hipFixture.windows as unknown as HipData;

function gridItems(container: HTMLElement): HTMLElement[] {
  return Array.from(container.querySelectorAll<HTMLElement>('.hip-grid > div'));
}

function cardTitles(container: HTMLElement): string[] {
  return Array.from(container.querySelectorAll('.ant-card-head-title')).map(
    (el) => el.textContent ?? '',
  );
}

describe('CategoryGrid — macOS', () => {
  it('lays cards out in the configured order with their span hints', () => {
    const { container } = render(<CategoryGrid cycle={macos.cycles[0]} />);

    expect(cardTitles(container)).toEqual([
      'custom checks',
      'anti-malware',
      'firewall',
      'disk-encryption',
      'disk-backup',
      'patch-management',
      'missing patches (2)',
    ]);

    const spans = gridItems(container).map((el) => el.style.getPropertyValue('--hip-span'));
    // host info 2 + custom checks 2 | anti-malware 2 + firewall 1 + disk-encryption 1
    // | disk-backup 2 + patch-management 2 | missing patches 4 -- four full rows.
    expect(spans).toEqual(['2', '2', '2', '1', '1', '2', '2', '4']);
    expect(spans.reduce((sum, s) => sum + Number(s), 0) % 4).toBe(0);
  });

  it('routes zero-product categories to the not-detected strip, not to cards', () => {
    const { container } = render(<CategoryGrid cycle={macos.cycles[0]} />);

    expect(screen.getByText('not detected:')).toBeInTheDocument();
    expect(screen.getByText('data-loss-prevention')).toBeInTheDocument();
    expect(cardTitles(container)).not.toContain('data-loss-prevention');
  });
});

describe('CategoryGrid — Windows', () => {
  it('gives host info the full width when there are no custom checks', () => {
    const { container } = render(<CategoryGrid cycle={windows.cycles[0]} />);

    expect(cardTitles(container)).toEqual([
      'anti-malware',
      'firewall',
      'disk-encryption',
      'disk-backup',
      'patch-management',
    ]);

    const spans = gridItems(container).map((el) => el.style.getPropertyValue('--hip-span'));
    expect(spans).toEqual(['4', '2', '1', '1', '2', '2']);
    expect(spans.reduce((sum, s) => sum + Number(s), 0) % 4).toBe(0);
  });

  it('passes wide to HostInfoCard so its fields pair up two-across', () => {
    render(<CategoryGrid cycle={windows.cycles[0]} />);

    const grid = screen.getByText('machine GUID').parentElement;
    expect(grid?.style.gridTemplateColumns).toBe(
      'minmax(0, auto) minmax(0, 1fr) minmax(0, auto) minmax(0, 1fr)',
    );
  });

  it('omits the missing-patches block when the cycle reported none', () => {
    render(<CategoryGrid cycle={windows.cycles[0]} />);
    expect(screen.queryByText(/missing patches/)).not.toBeInTheDocument();
  });

  it('renders Windows products through the same data-driven cards', () => {
    render(<CategoryGrid cycle={windows.cycles[0]} />);
    expect(screen.getByText('BitLocker Drive Encryption')).toBeInTheDocument();
    expect(screen.getByText('Dell Command | Update')).toBeInTheDocument();
  });
});

describe('CategoryGrid — cycle with no report', () => {
  // A cycle whose XML was not well-formed (e.g. an unescaped "&") now
  // degrades to report: null instead of failing the whole bundle's parse
  // (paa_analyzer/hip/report.py's ET.ParseError fix) -- this was previously
  // unreachable from any real fixture, since none is malformed. Built from a
  // real cycle with only `report` overridden, not fabricated data.
  const cycleWithNoReport = { ...macos.cycles[0], report: null };

  it('explains the missing report instead of crashing', () => {
    render(<CategoryGrid cycle={cycleWithNoReport} />);
    expect(
      screen.getByText(/This cycle carries no HIP report/),
    ).toBeInTheDocument();
  });
});

describe('CategoryGrid — layout config', () => {
  it('covers every category the fixtures report with products', () => {
    const named = new Set(CATEGORY_LAYOUT.map((l) => l.name));
    for (const data of [macos, windows]) {
      for (const cycle of data.cycles) {
        for (const category of cycle.report!.categories) {
          if (category.products.length > 0) expect(named.has(category.name!)).toBe(true);
        }
      }
    }
  });
});
