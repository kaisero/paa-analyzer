import { describe, it, expect, vi } from 'vitest';
import { render, screen } from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import { hipFixture } from '../../test/handlers';
import type { HipData } from '../../api/types';
import { CycleHeader, fmtCycleTime } from './CycleHeader';

const macos = hipFixture.macos as unknown as HipData;
const windows = hipFixture.windows as unknown as HipData;

function renderHeader(data: HipData, onSelect = vi.fn(), onViewMode = vi.fn()) {
  render(
    <CycleHeader
      cycles={data.cycles}
      selectedIndex={data.cycles[0].index}
      onSelect={onSelect}
      viewMode="Grid"
      onViewMode={onViewMode}
    />,
  );
  return { onSelect, onViewMode };
}

describe('CycleHeader', () => {
  it('shows the position, duration and non-zero counts of the selected cycle', () => {
    renderHeader(macos);
    const cycle = macos.cycles[0];

    expect(screen.getByText('1 of 2')).toBeInTheDocument();
    expect(screen.getByText(`${cycle.duration_s}s`)).toBeInTheDocument();
    expect(screen.getByText(`${cycle.counts.warn} warn`)).toBeInTheDocument();
    expect(screen.getByText(`${cycle.counts.unknown} unknown`)).toBeInTheDocument();
    expect(screen.getByText(`${cycle.counts.errors} errors`)).toBeInTheDocument();
    expect(screen.getByText(`${cycle.counts.missing_patches} missing patches`)).toBeInTheDocument();
  });

  it('hides counts that are zero', () => {
    // The Windows cycle has no warnings and no missing patches.
    renderHeader(windows);
    expect(screen.queryByText(/warn/)).not.toBeInTheDocument();
    expect(screen.queryByText(/missing patches/)).not.toBeInTheDocument();
    expect(screen.getByText('5 unknown')).toBeInTheDocument();
  });

  it('labels the selector with the cycle generate time, newest first', async () => {
    const user = userEvent.setup();
    const { onSelect } = renderHeader(macos);

    expect(screen.getByText(fmtCycleTime(macos.cycles[0].generate_time))).toBeInTheDocument();

    await user.click(screen.getByRole('combobox'));
    const older = await screen.findByText(fmtCycleTime(macos.cycles[1].generate_time));
    await user.click(older);

    // antd's Select passes (value, option); only the value matters here.
    expect(onSelect.mock.calls[0][0]).toBe(macos.cycles[1].index);
  });

  it('offers the Grid / XML / JSON toggle', async () => {
    const user = userEvent.setup();
    const { onViewMode } = renderHeader(macos);

    await user.click(screen.getByText('XML'));
    expect(onViewMode).toHaveBeenCalledWith('XML');
  });
});
