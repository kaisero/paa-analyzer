import { useState, useMemo } from 'react';
import { Table, Tag, Input, Badge } from 'antd';
import { SearchOutlined } from '@ant-design/icons';
import type { StateEntry } from '../../api/types';
import { RawJsonView } from './RawJsonView';

interface Driver {
  module: string;
  display_name: string;
  driver_type: string;
  start_mode: string;
  state: string;
  status: string;
}

interface Props {
  entry: StateEntry | undefined;
  viewMode: 'Table' | 'Raw' | 'JSON';
}

const mono = { fontFamily: '"JetBrains Mono", monospace', fontSize: 11 };

const columns = [
  {
    title: 'State',
    dataIndex: 'state',
    key: 'state',
    width: 80,
    render: (v: string) => (
      <Badge status={v === 'Running' ? 'success' : 'default'} text={<span style={{ fontSize: 11 }}>{v}</span>} />
    ),
    sorter: (a: Driver, b: Driver) => a.state.localeCompare(b.state),
  },
  {
    title: 'Module',
    dataIndex: 'module',
    key: 'module',
    width: 140,
    render: (v: string) => {
      const isPalo = v.toLowerCase().includes('pa') && v.toLowerCase().includes('srv');
      return <span style={{ ...mono, fontWeight: isPalo ? 600 : 400, color: isPalo ? 'var(--blue)' : undefined }}>{v}</span>;
    },
    sorter: (a: Driver, b: Driver) => a.module.localeCompare(b.module),
  },
  {
    title: 'Display Name',
    dataIndex: 'display_name',
    key: 'display_name',
    render: (v: string) => <span style={{ fontWeight: 500 }}>{v}</span>,
    sorter: (a: Driver, b: Driver) => a.display_name.localeCompare(b.display_name),
  },
  {
    title: 'Type',
    dataIndex: 'driver_type',
    key: 'driver_type',
    width: 100,
    render: (v: string) => <Tag style={{ fontSize: 10 }}>{v}</Tag>,
  },
  {
    title: 'Start Mode',
    dataIndex: 'start_mode',
    key: 'start_mode',
    width: 100,
    render: (v: string) => <span style={mono}>{v}</span>,
  },
  {
    title: 'Status',
    dataIndex: 'status',
    key: 'status',
    width: 60,
    render: (v: string) => (
      <Tag color={v === 'OK' ? 'green' : 'red'} style={{ fontSize: 10 }}>{v}</Tag>
    ),
  },
];

export function InstalledDriversTab({ entry, viewMode }: Props) {
  const [search, setSearch] = useState('');

  const filtered = useMemo(() => {
    const allDrivers = entry
      ? (Array.isArray(entry.data) ? entry.data : []) as Driver[]
      : [];
    if (!search) return allDrivers;
    const needle = search.toLowerCase();
    return allDrivers.filter((d) =>
      d.module.toLowerCase().includes(needle) ||
      d.display_name.toLowerCase().includes(needle),
    );
  }, [entry, search]);

  if (!entry) {
    return <div style={{ color: 'var(--text3)', fontSize: 12, padding: 16 }}>No driver data available.</div>;
  }

  if (viewMode !== 'Table') {
    return <RawJsonView entry={entry} viewMode={viewMode} />;
  }

  return (
    <div>
      <div style={{ marginBottom: 12 }}>
        <Input
          prefix={<SearchOutlined style={{ color: 'var(--text3)' }} />}
          placeholder="Filter by module or name..."
          value={search}
          onChange={(e) => setSearch(e.target.value)}
          allowClear
          size="small"
          style={{ maxWidth: 320 }}
        />
      </div>
      <Table
        dataSource={filtered}
        columns={columns}
        rowKey="module"
        size="small"
        pagination={{ pageSize: 50, showSizeChanger: false, size: 'small' }}
      />
    </div>
  );
}
