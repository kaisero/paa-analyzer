import { useState, useMemo } from 'react';
import { Table, Tag, Input } from 'antd';
import { SearchOutlined } from '@ant-design/icons';
import type { StateEntry } from '../../api/types';
import { RawJsonView } from './RawJsonView';

interface FirewallRule {
  name: string;
  enabled: boolean;
  direction: string;
  action: string;
  protocol: string;
  local_addresses?: string;
  remote_addresses?: string;
  profiles?: string[];
}

interface Props {
  entry: StateEntry | undefined;
  viewMode: 'Table' | 'Raw' | 'JSON';
}

const mono = { fontFamily: '"JetBrains Mono", monospace', fontSize: 11 };

const directionColors: Record<string, string> = { kIn: 'orange', kOut: 'blue' };
const actionColors: Record<string, string> = { kAllow: 'green', kBlock: 'red' };

// eslint-disable-next-line react-refresh/only-export-components
export function cleanLabel(v: string): string {
  return v.replace(/^k/, '');
}

const columns = [
  {
    title: 'Enabled',
    dataIndex: 'enabled',
    key: 'enabled',
    width: 72,
    render: (v: boolean) => (
      <span style={{ color: v ? 'var(--ok)' : 'var(--text-dim)' }}>
        {v ? '\u2713' : '\u2717'}
      </span>
    ),
    filters: [{ text: 'Enabled', value: true }, { text: 'Disabled', value: false }],
    onFilter: (value: unknown, record: FirewallRule) => record.enabled === value,
  },
  {
    title: 'Name',
    dataIndex: 'name',
    key: 'name',
    render: (v: string) => {
      // Clean up long UWP app names
      const display = v.startsWith('@{') ? v.split('?')[0].replace('@{', '').split('_')[0] : v;
      return <span style={{ ...mono, fontWeight: 500 }} title={v}>{display}</span>;
    },
    ellipsis: true,
  },
  {
    title: 'Direction',
    dataIndex: 'direction',
    key: 'direction',
    width: 80,
    render: (v: string) => <Tag color={directionColors[v] || 'default'} style={{ fontSize: 10 }}>{cleanLabel(v)}</Tag>,
    filters: [{ text: 'In', value: 'kIn' }, { text: 'Out', value: 'kOut' }],
    onFilter: (value: unknown, record: FirewallRule) => record.direction === value,
  },
  {
    title: 'Action',
    dataIndex: 'action',
    key: 'action',
    width: 80,
    render: (v: string) => <Tag color={actionColors[v] || 'default'} style={{ fontSize: 10 }}>{cleanLabel(v)}</Tag>,
    filters: [{ text: 'Allow', value: 'kAllow' }, { text: 'Block', value: 'kBlock' }],
    onFilter: (value: unknown, record: FirewallRule) => record.action === value,
  },
  {
    title: 'Protocol',
    dataIndex: 'protocol',
    key: 'protocol',
    width: 90,
    render: (v: string) => <span style={mono}>{v}</span>,
  },
];

export function FirewallRulesTab({ entry, viewMode }: Props) {
  const [search, setSearch] = useState('');

  const { allRules, filtered } = useMemo(() => {
    const rules = entry
      ? ((entry.data as { rules?: FirewallRule[]; total?: number }).rules ?? [])
      : [];
    if (!search) return { allRules: rules, filtered: rules };
    const needle = search.toLowerCase();
    return { allRules: rules, filtered: rules.filter((r) => r.name.toLowerCase().includes(needle)) };
  }, [entry, search]);

  if (!entry) {
    return <div style={{ color: 'var(--text-dim)', fontSize: 12, padding: 16 }}>No firewall rules available.</div>;
  }

  if (viewMode !== 'Table') {
    return <RawJsonView entry={entry} viewMode={viewMode} />;
  }

  return (
    <div>
      <div style={{ display: 'flex', alignItems: 'center', gap: 12, marginBottom: 12 }}>
        <Input
          prefix={<SearchOutlined style={{ color: 'var(--text-dim)' }} />}
          placeholder="Filter by name..."
          value={search}
          onChange={(e) => setSearch(e.target.value)}
          allowClear
          size="small"
          style={{ maxWidth: 320 }}
        />
        <span style={{ fontSize: 11, color: 'var(--text-dim)' }}>
          {filtered.length} of {allRules.length} rules
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
