import { describe, it, expect } from 'vitest';
import { render, screen } from '@testing-library/react';
import { RoutingTableTab } from './RoutingTableTab';
import type { StateEntry } from '../../api/types';

const macEntry: StateEntry = {
  _meta: { type: 'state', module: 'System', component: 'Networking', source_file: 'routing.txt', name: 'routing' },
  data: {
    ipv4: [
      { destination: 'default', gateway: '198.18.1.1', flags: 'UGScg', netif: 'en0', expire: null },
      { destination: '127.0.0.1', gateway: '127.0.0.1', flags: 'UH', netif: 'lo0', expire: null },
    ],
    ipv6: [],
  },
};

const winEntry: StateEntry = {
  _meta: { type: 'state', module: 'System', component: 'Networking', source_file: 'route.log', name: 'route' },
  data: {
    interfaces: [],
    ipv4: [
      { destination: '0.0.0.0', netmask: '0.0.0.0', gateway: '198.18.1.1', interface: '198.18.1.209', metric: 15 },
      { destination: '127.0.0.0', netmask: '255.0.0.0', gateway: 'On-link', interface: '127.0.0.1', metric: 331 },
    ],
    ipv6: [
      { destination: '::/0', gateway: 'fe80::602b:33ff:fefd:aa08', interface: 'Ethernet Adapter', metric: 31 },
    ],
  },
};

describe('RoutingTableTab — format detection', () => {
  it('renders macOS columns when data has flags field', () => {
    render(<RoutingTableTab entry={macEntry} viewMode="Table" />);
    expect(screen.getByText('Flags')).toBeInTheDocument();
    expect(screen.queryByText('Netmask')).not.toBeInTheDocument();
    expect(screen.getByText('default')).toBeInTheDocument();
  });

  it('renders Windows IPv4 with CIDR notation (no Netmask column)', () => {
    render(<RoutingTableTab entry={winEntry} viewMode="Table" />);
    // Netmask merged into Network column as CIDR: 0.0.0.0/0
    expect(screen.queryByText('Netmask')).not.toBeInTheDocument();
    expect(screen.getByText('Network')).toBeInTheDocument();
    expect(screen.getByText('Metric')).toBeInTheDocument();
    expect(screen.getByText('0.0.0.0/0')).toBeInTheDocument();
  });

  it('uses Windows IPv6 columns with Destination for IPv6 tab', () => {
    render(<RoutingTableTab entry={winEntry} viewMode="Table" />);
    const ipv6Btn = screen.getByText('IPv6');
    ipv6Btn.click();
    // IPv6 has Destination, Gateway, Interface, Metric
    expect(screen.getByText('Metric')).toBeInTheDocument();
    expect(screen.getByText('Gateway')).toBeInTheDocument();
    expect(screen.queryByText('Flags')).not.toBeInTheDocument();
    expect(screen.getByText('::/0')).toBeInTheDocument();
  });

  it('shows empty message when entry is undefined', () => {
    render(<RoutingTableTab entry={undefined} viewMode="Table" />);
    expect(screen.getByText('No routing data available.')).toBeInTheDocument();
  });
});
