import { Table, Tag } from 'antd';
import type { StateEntry } from '../../api/types';
import { RawJsonView } from './RawJsonView';

interface Extension {
  enabled: boolean;
  active: boolean;
  name: string;
  bundle_id: string;
  version: string;
  team_id: string;
  category: string;
  state: string;
}

interface Props {
  entry: StateEntry | undefined;
  viewMode: 'Table' | 'Raw' | 'JSON';
}

const categoryColors: Record<string, string> = {
  network_extension: 'blue',
  endpoint_security: 'green',
};

function stateColor(state: string): string {
  if (state.includes('activated')) return 'green';
  if (state.includes('terminated')) return 'orange';
  return 'red';
}

const columns = [
  {
    title: 'Enabled',
    dataIndex: 'enabled',
    key: 'enabled',
    width: 72,
    render: (v: boolean) => (
      <span style={{ color: v ? 'var(--green)' : 'var(--text3)' }}>
        {v ? '\u2713' : '\u2717'}
      </span>
    ),
  },
  {
    title: 'Active',
    dataIndex: 'active',
    key: 'active',
    width: 64,
    render: (v: boolean) => (
      <span style={{ color: v ? 'var(--green)' : 'var(--text3)' }}>
        {v ? '\u2713' : '\u2717'}
      </span>
    ),
  },
  {
    title: 'Name',
    dataIndex: 'name',
    key: 'name',
    render: (v: string) => <span style={{ fontWeight: 500 }}>{v}</span>,
  },
  {
    title: 'Bundle ID',
    dataIndex: 'bundle_id',
    key: 'bundle_id',
    render: (v: string) => (
      <span style={{ fontFamily: '"JetBrains Mono", monospace', fontSize: 11 }}>{v}</span>
    ),
  },
  {
    title: 'Version',
    dataIndex: 'version',
    key: 'version',
    width: 100,
    render: (v: string) => (
      <span style={{ fontFamily: '"JetBrains Mono", monospace', fontSize: 11 }}>{v}</span>
    ),
  },
  {
    title: 'Category',
    dataIndex: 'category',
    key: 'category',
    width: 160,
    render: (v: string) => (
      <Tag color={categoryColors[v] || 'default'} style={{ fontSize: 11 }}>
        {v.replace('_', ' ')}
      </Tag>
    ),
  },
  {
    title: 'State',
    dataIndex: 'state',
    key: 'state',
    width: 160,
    render: (v: string) => (
      <Tag color={stateColor(v)} style={{ fontSize: 11 }}>
        {v}
      </Tag>
    ),
  },
];

export function SystemExtensionsTab({ entry, viewMode }: Props) {
  if (!entry) {
    return <div style={{ color: 'var(--text3)', fontSize: 12, padding: 16 }}>No system extensions data available.</div>;
  }

  if (viewMode !== 'Table') {
    return <RawJsonView entry={entry} viewMode={viewMode} />;
  }

  const extensions = (Array.isArray(entry.data) ? entry.data : []) as Extension[];

  return (
    <Table
      dataSource={extensions}
      columns={columns}
      rowKey={(r) => r.bundle_id}
      size="small"
      pagination={false}
    />
  );
}
