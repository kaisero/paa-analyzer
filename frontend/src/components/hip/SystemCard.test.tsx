import { describe, it, expect } from 'vitest';
import { screen } from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import { renderWithProviders } from '../../test/wrapper';
import hipFixture from '../../test/fixtures/hip.json';
import type { HipData } from '../../api/types';
import { SystemCard } from './SystemCard';

const macos = hipFixture.macos as unknown as HipData;
const windows = hipFixture.windows as unknown as HipData;

describe('SystemCard', () => {
  it('labels the host id by kind on macOS', () => {
    renderWithProviders(<SystemCard report={macos.cycles[0].report!} />);
    expect(screen.getByText(/MAC address/i)).toBeInTheDocument();
  });

  it('labels the host id by kind on Windows', () => {
    renderWithProviders(<SystemCard report={windows.cycles[0].report!} />);
    expect(screen.getByText(/machine GUID/i)).toBeInTheDocument();
    expect(screen.getByText(windows.cycles[0].report!.host_info!.domain!)).toBeInTheDocument();
  });

  it('keeps interfaces behind a toggle', async () => {
    const user = userEvent.setup();
    renderWithProviders(<SystemCard report={macos.cycles[0].report!} />);
    const count = macos.cycles[0].report!.host_info!.interfaces.length;
    expect(count).toBe(23);
    await user.click(screen.getByText(new RegExp(`${count} interfaces`, 'i')));
    expect(screen.getByText('en0')).toBeInTheDocument();
  });

  it('switches to JSON without offering XML', async () => {
    const user = userEvent.setup();
    renderWithProviders(<SystemCard report={macos.cycles[0].report!} />);
    expect(screen.queryByText('XML')).not.toBeInTheDocument();
    await user.click(screen.getByText('JSON'));
    expect(screen.getByText(/"host_name"/)).toBeInTheDocument();
  });
});
