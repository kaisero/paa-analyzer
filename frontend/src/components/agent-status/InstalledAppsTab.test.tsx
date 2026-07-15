import { describe, it, expect } from 'vitest';
import { render, screen } from '@testing-library/react';
import { InstalledAppsTab } from './InstalledAppsTab';
import type { StateEntry } from '../../api/types';

const meta = { type: 'state', module: 'System', component: 'Core', source_file: 'test', name: 'installed_applications' };

describe('InstalledAppsTab — format detection', () => {
  it('renders Name+Version table for Windows format', () => {
    const entry = {
      _meta: meta,
      data: [
        { name: 'Prisma Access Agent', version: '26.1.2.4' },
        { name: 'Microsoft Edge', version: '146.0.3856.109' },
      ],
    } as unknown as StateEntry;
    render(<InstalledAppsTab entry={entry} viewMode="Table" />);
    expect(screen.getByText('Version')).toBeInTheDocument();
    expect(screen.getByText('Prisma Access Agent')).toBeInTheDocument();
    expect(screen.getByText('26.1.2.4')).toBeInTheDocument();
  });

  it('renders simple Application list for macOS format', () => {
    const entry = {
      _meta: meta,
      data: ['Google Chrome', 'Safari', 'Slack'],
    } as unknown as StateEntry;
    render(<InstalledAppsTab entry={entry} viewMode="Table" />);
    expect(screen.getByText('Application')).toBeInTheDocument();
    expect(screen.getByText('Google Chrome')).toBeInTheDocument();
    expect(screen.queryByText('Version')).not.toBeInTheDocument();
  });

  it('shows empty message when entry is undefined', () => {
    render(<InstalledAppsTab entry={undefined} viewMode="Table" />);
    expect(screen.getByText('No application data available.')).toBeInTheDocument();
  });
});
