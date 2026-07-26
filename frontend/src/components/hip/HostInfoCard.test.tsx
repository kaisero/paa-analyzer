import { describe, it, expect } from 'vitest';
import { render, screen } from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import { hipFixture } from '../../test/handlers';
import type { HipData } from '../../api/types';
import { HostInfoCard } from './HostInfoCard';

const macos = hipFixture.macos as unknown as HipData;
const windows = hipFixture.windows as unknown as HipData;
const macHost = macos.cycles[0].report!.host_info!;
const winHost = windows.cycles[0].report!.host_info!;

describe('HostInfoCard', () => {
  it('labels the macOS host id as a MAC address', () => {
    render(<HostInfoCard hostInfo={macHost} reportVersion={macos.cycles[0].report!.version} />);

    expect(screen.getByText('Apple Mac OS X 15.7.7')).toBeInTheDocument();
    expect(screen.getByText('MAC address')).toBeInTheDocument();
    expect(screen.getByText(macHost.host_id!)).toBeInTheDocument();
    // macOS carries no domain -- the row is omitted rather than shown empty.
    expect(screen.queryByText('domain')).not.toBeInTheDocument();
  });

  it('labels the Windows host id as a machine GUID and shows the domain', () => {
    render(<HostInfoCard hostInfo={winHost} />);

    expect(screen.getByText('machine GUID')).toBeInTheDocument();
    expect(screen.getByText('domain')).toBeInTheDocument();
    expect(screen.getByText(winHost.domain!)).toBeInTheDocument();
  });

  it('pairs fields two-across in the full-width layout', () => {
    // Windows is the real case that drives `wide`: no custom checks beside
    // it, so CategoryGrid gives host info the full span-4 row.
    render(<HostInfoCard hostInfo={winHost} wide />);

    const grid = screen.getByText('machine GUID').parentElement;
    expect(grid?.style.gridTemplateColumns).toBe(
      'minmax(0, auto) minmax(0, 1fr) minmax(0, auto) minmax(0, 1fr)',
    );
  });

  it('keeps interfaces collapsed until the toggle is used', async () => {
    const user = userEvent.setup();
    render(<HostInfoCard hostInfo={macHost} />);

    const toggle = screen.getByRole('button', { name: `show ${macHost.interfaces.length} interfaces` });
    expect(screen.queryByText(macHost.interfaces[0].name!)).not.toBeInTheDocument();

    await user.click(toggle);
    expect(screen.getByText(macHost.interfaces[0].name!)).toBeInTheDocument();
    expect(
      screen.getByRole('button', { name: `hide ${macHost.interfaces.length} interfaces` }),
    ).toBeInTheDocument();
  });
});
