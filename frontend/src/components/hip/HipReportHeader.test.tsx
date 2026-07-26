import { describe, it, expect, vi } from 'vitest';
import { screen, within } from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import { renderWithProviders } from '../../test/wrapper';
import hipFixture from '../../test/fixtures/hip.json';
import type { HipData } from '../../api/types';
import { HipReportHeader } from './HipReportHeader';

const macos = hipFixture.macos as unknown as HipData;

function renderHeader(onSelect = () => {}) {
  return renderWithProviders(
    <HipReportHeader
      hip={macos}
      selectedIndex={macos.cycles[0].index}
      onSelect={onSelect}
    />,
  );
}

describe('HipReportHeader', () => {
  it('is titled HIP Report', () => {
    renderHeader();
    expect(screen.getByRole('heading', { name: 'HIP Report' })).toBeInTheDocument();
  });

  it('shows platform and cycle count in the meta line', () => {
    // Requirement 4 removed the platform *toggle*, not the platform *fact* —
    // HipPage used to show this in its own banner; that banner is gone
    // (Task 9), so the fact moves here.
    renderHeader();
    expect(screen.getByText(/MACOS/)).toBeInTheDocument();
    expect(screen.getByText(/2 cycles/)).toBeInTheDocument();
  });

  it('shows the counts for the selected cycle', () => {
    renderHeader();
    const counts = macos.cycles[0].counts;
    expect(counts).toEqual({ warn: 2, unknown: 3, errors: 6, missing_patches: 2 });
    // 'Warn' and 'Missing Patches' both carry the value 2, so a bare
    // getByText('2') is ambiguous — scope each assertion to its own Count.
    expect(within(screen.getByText('Warn').parentElement!).getByText('2')).toBeInTheDocument();
    expect(within(screen.getByText('Unknown').parentElement!).getByText('3')).toBeInTheDocument();
    expect(within(screen.getByText('Errors').parentElement!).getByText('6')).toBeInTheDocument();
    expect(within(screen.getByText('Missing Patches').parentElement!).getByText('2')).toBeInTheDocument();
  });

  it('marks a partial cycle', () => {
    // The fixture carries no partial cycle (Global Constraints: never invent
    // HIP test data). This flips one boolean on a real fixture cycle purely
    // to exercise the rendering branch — it fabricates no diagnostic content.
    const partialMacos: HipData = {
      ...macos,
      cycles: [{ ...macos.cycles[0], partial: true }, ...macos.cycles.slice(1)],
    };
    renderWithProviders(
      <HipReportHeader hip={partialMacos} selectedIndex={partialMacos.cycles[0].index} onSelect={() => {}} />,
    );
    expect(screen.getByText('partial')).toBeInTheDocument();
  });

  it('lists every cycle and reports the chosen one', async () => {
    const onSelect = vi.fn();
    const user = userEvent.setup();
    renderHeader(onSelect);
    await user.click(screen.getByRole('combobox'));
    const second = macos.cycles[1];
    await user.click(await screen.findByTitle(new RegExp(`Cycle ${second.index}`)));
    // antd's Select calls onChange(value, option); only the value matters
    // here.
    expect(onSelect.mock.calls[0][0]).toBe(second.index);
  });

  it('does not render a platform switch — platform is fixed by the bundle', () => {
    renderHeader();
    expect(screen.queryByText('Windows')).not.toBeInTheDocument();
    expect(screen.queryByText('macOS')).not.toBeInTheDocument();
  });
});
