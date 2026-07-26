import { useState, useMemo } from 'react';
import { Table, Tag, Input } from 'antd';
import { SearchOutlined } from '@ant-design/icons';
import type { StateEntry } from '../../api/types';
import type { ViewMode } from '../common/ViewToggle';
import { RawJsonView } from './RawJsonView';

interface Connection {
  proto: string;
  local_address: string;
  foreign_address: string;
  state: string;
  process: string;
}

interface Props {
  entry: StateEntry | undefined;
  viewMode: ViewMode;
}

const mono = { fontFamily: '"JetBrains Mono", monospace', fontSize: 11 };

const stateColors: Record<string, string> = {
  LISTENING: 'blue',
  ESTABLISHED: 'green',
  TIME_WAIT: 'orange',
  CLOSE_WAIT: 'orange',
  FIN_WAIT_2: 'orange',
};

const columns = [
  {
    title: 'Proto',
    dataIndex: 'proto',
    key: 'proto',
    width: 60,
    render: (v: string) => <span style={mono}>{v}</span>,
    filters: [{ text: 'TCP', value: 'TCP' }, { text: 'UDP', value: 'UDP' }],
    onFilter: (value: unknown, record: Connection) => record.proto === value,
  },
  {
    title: 'Local Address',
    dataIndex: 'local_address',
    key: 'local_address',
    render: (v: string) => <span style={mono}>{v}</span>,
  },
  {
    title: 'Foreign Address',
    dataIndex: 'foreign_address',
    key: 'foreign_address',
    render: (v: string) => <span style={mono}>{v}</span>,
  },
  {
    title: 'State',
    dataIndex: 'state',
    key: 'state',
    width: 120,
    render: (v: string) => <Tag color={stateColors[v] || 'default'} style={{ fontSize: 10 }}>{v}</Tag>,
    filters: [
      { text: 'LISTENING', value: 'LISTENING' },
      { text: 'ESTABLISHED', value: 'ESTABLISHED' },
      { text: 'TIME_WAIT', value: 'TIME_WAIT' },
    ],
    onFilter: (value: unknown, record: Connection) => record.state === value,
  },
  {
    title: 'Process',
    dataIndex: 'process',
    key: 'process',
    render: (v: string) => {
      const isPalo = v.toLowerCase().includes('pasrv') || v.toLowerCase().includes('palo');
      return <span style={{ ...mono, fontWeight: isPalo ? 600 : 400, color: isPalo ? 'var(--info)' : undefined }}>{v || '--'}</span>;
    },
  },
];

export function NetstatTab({ entry, viewMode }: Props) {
  const [search, setSearch] = useState('');

  const filtered = useMemo(() => {
    const allConns = entry
      ? ((entry.data as { connections?: Connection[] }).connections ?? [])
      : [];
    if (!search) return allConns;
    const needle = search.toLowerCase();
    return allConns.filter((c) =>
      c.local_address.includes(needle) ||
      c.foreign_address.includes(needle) ||
      c.process.toLowerCase().includes(needle),
    );
  }, [entry, search]);

  if (!entry) {
    return <div style={{ color: 'var(--text-dim)', fontSize: 12, padding: 16 }}>No network connection data available.</div>;
  }

  if (viewMode !== 'View') {
    return <RawJsonView entry={entry} viewMode={viewMode} />;
  }

  return (
    <div>
      <div style={{ display: 'flex', alignItems: 'center', gap: 12, marginBottom: 12 }}>
        <Input
          prefix={<SearchOutlined style={{ color: 'var(--text-dim)' }} />}
          placeholder="Filter by address or process..."
          value={search}
          onChange={(e) => setSearch(e.target.value)}
          allowClear
          size="small"
          style={{ maxWidth: 320 }}
        />
        <span style={{ fontSize: 11, color: 'var(--text-dim)' }}>
          {filtered.length} connections
        </span>
      </div>
      <Table
        dataSource={filtered}
        columns={columns}
        rowKey={(_, idx) => String(idx)}
        size="small"
        pagination={{ pageSize: 50, showSizeChanger: false, size: 'small' }}
      />
    </div>
  );
}
