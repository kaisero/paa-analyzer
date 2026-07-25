import { useState } from 'react';
import { Table, Segmented, Tooltip } from 'antd';
import type { StateEntry } from '../../api/types';
import { RawJsonView } from './RawJsonView';

// macOS route entry
interface MacRoute {
  destination: string;
  gateway: string;
  flags: string;
  netif: string;
  expire: string | null;
}

// Windows route entry
interface WinRoute {
  destination: string;
  netmask: string;
  gateway: string;
  interface: string;
  metric: number;
}

interface Props {
  entry: StateEntry | undefined;
  viewMode: 'Table' | 'Raw' | 'JSON';
}

// macOS routing flags descriptions
const FLAG_DESCRIPTIONS: Record<string, string> = {
  U: 'Up — route is usable',
  G: 'Gateway — route to a gateway',
  H: 'Host — destination is a host',
  S: 'Static — manually added route',
  c: 'Clone — generates new routes on use',
  L: 'Link — link-level address present',
  W: 'Wascloned — was cloned from another route',
  I: 'Interface — route to interface',
  R: 'Reject — packets discarded',
  D: 'Dynamic — created by redirect',
  b: 'Blackhole — packets silently discarded',
  i: 'ifscope — scoped to interface',
};

function FlagsCell({ flags }: { flags: string }) {
  if (!flags) return <span style={{ fontFamily: '"JetBrains Mono", monospace', fontSize: 11 }}>--</span>;
  const descriptions = flags.split('').map((f) => {
    const desc = FLAG_DESCRIPTIONS[f];
    return desc ? `${f} = ${desc}` : f;
  });
  return (
    <Tooltip title={<div style={{ whiteSpace: 'pre-line', fontSize: 11 }}>{descriptions.join('\n')}</div>}>
      <span style={{ fontFamily: '"JetBrains Mono", monospace', fontSize: 11, cursor: 'help' }}>
        {flags}
      </span>
    </Tooltip>
  );
}

const mono = { fontFamily: '"JetBrains Mono", monospace', fontSize: 11 };

const macColumns = [
  {
    title: 'Destination', dataIndex: 'destination', key: 'destination',
    render: (v: string) => <span style={{ ...mono, fontWeight: v === 'default' ? 600 : 400, color: v === 'default' ? 'var(--info)' : undefined }}>{v}</span>,
  },
  { title: 'Gateway', dataIndex: 'gateway', key: 'gateway', render: (v: string) => <span style={mono}>{v}</span> },
  { title: 'Flags', dataIndex: 'flags', key: 'flags', width: 100, render: (v: string) => <FlagsCell flags={v} /> },
  { title: 'Interface', dataIndex: 'netif', key: 'netif', width: 100, render: (v: string) => <span style={mono}>{v}</span> },
  { title: 'Expire', dataIndex: 'expire', key: 'expire', width: 80, render: (v: string | null) => <span style={{ ...mono, color: 'var(--text-dim)' }}>{v ?? '--'}</span> },
];

/** Convert dotted netmask to CIDR prefix length (e.g. "255.255.255.0" → 24). */
function netmaskToCidr(mask: string): number {
  if (!mask) return 0;
  return mask.split('.').reduce((bits, octet) => bits + (Number(octet) >>> 0).toString(2).replace(/0/g, '').length, 0);
}

const winIpv4Columns = [
  {
    title: 'Network', dataIndex: 'destination', key: 'destination',
    // eslint-disable-next-line @typescript-eslint/no-explicit-any
    render: (v: string, record: any) => {
      const cidr = record.netmask ? netmaskToCidr(record.netmask) : null;
      const display = cidr !== null ? `${v}/${cidr}` : v;
      const isDefault = v === '0.0.0.0';
      return <span style={{ ...mono, fontWeight: isDefault ? 600 : 400, color: isDefault ? 'var(--info)' : undefined }}>{display}</span>;
    },
  },
  { title: 'Gateway', dataIndex: 'gateway', key: 'gateway', render: (v: string) => <span style={mono}>{v}</span> },
  { title: 'Interface', dataIndex: 'interface', key: 'interface', render: (v: string) => <span style={mono}>{v}</span> },
  { title: 'Metric', dataIndex: 'metric', key: 'metric', width: 80, render: (v: number) => <span style={mono}>{v}</span> },
];

const winIpv6Columns = [
  {
    title: 'Destination', dataIndex: 'destination', key: 'destination',
    render: (v: string) => <span style={{ ...mono, fontWeight: v === '::/0' ? 600 : 400, color: v === '::/0' ? 'var(--info)' : undefined }}>{v}</span>,
  },
  { title: 'Gateway', dataIndex: 'gateway', key: 'gateway', render: (v: string) => <span style={mono}>{v}</span> },
  { title: 'Interface', dataIndex: 'interface', key: 'interface', render: (v: string) => <span style={mono}>{v}</span> },
  { title: 'Metric', dataIndex: 'metric', key: 'metric', width: 80, render: (v: number) => <span style={mono}>{v}</span> },
];

export function RoutingTableTab({ entry, viewMode }: Props) {
  const [family, setFamily] = useState<'IPv4' | 'IPv6'>('IPv4');

  if (!entry) {
    return <div style={{ color: 'var(--text-dim)', fontSize: 12, padding: 16 }}>No routing data available.</div>;
  }

  if (viewMode !== 'Table') {
    return <RawJsonView entry={entry} viewMode={viewMode} />;
  }

  const data = entry.data as { ipv4?: Array<MacRoute | WinRoute>; ipv6?: Array<MacRoute | WinRoute> };
  const routes = family === 'IPv4' ? (data.ipv4 ?? []) : (data.ipv6 ?? []);

  // Detect format from IPv4 routes (always present and have the distinguishing field)
  const ipv4 = data.ipv4 ?? [];
  const isWindows = ipv4.length > 0 && 'netmask' in ipv4[0];

  // Pick columns based on OS and address family
  let columns;
  if (isWindows) {
    columns = family === 'IPv6' ? winIpv6Columns : winIpv4Columns;
  } else {
    columns = macColumns;
  }

  return (
    <div>
      <div style={{ marginBottom: 12 }}>
        <Segmented
          size="small"
          options={['IPv4', 'IPv6'] as const}
          value={family}
          onChange={(v) => setFamily(v as 'IPv4' | 'IPv6')}
        />
      </div>
      <Table
        dataSource={routes}
        columns={columns}
        rowKey={(r, idx) => `${(r as MacRoute).destination || (r as WinRoute).destination}-${idx}`}
        size="small"
        pagination={false}
      />
    </div>
  );
}
