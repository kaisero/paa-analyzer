import { useState, useMemo } from 'react';
import { Table, Tag, Badge, Input } from 'antd';
import { SearchOutlined } from '@ant-design/icons';
import type { StateEntry } from '../../api/types';
import type { ViewMode } from '../common/ViewToggle';
import { RawJsonView } from './RawJsonView';

interface LaunchItem {
  pid: number | null;
  status: number;
  label: string;
}

interface Props {
  entry: StateEntry | undefined;
  viewMode: ViewMode;
}

const mono = { fontFamily: '"JetBrains Mono", monospace', fontSize: 11 };

function statusColor(status: number): string {
  if (status === 0) return 'green';
  if (status < 0) return 'orange';
  return 'red';
}

const columns = [
  {
    title: 'PID',
    dataIndex: 'pid',
    key: 'pid',
    width: 80,
    render: (v: number | null) =>
      v !== null ? (
        <span style={mono}>
          <Badge status="success" style={{ marginRight: 6 }} />
          {v}
        </span>
      ) : (
        <span style={{ ...mono, color: 'var(--text-dim)' }}>--</span>
      ),
    sorter: (a: LaunchItem, b: LaunchItem) => {
      if (a.pid !== null && b.pid === null) return -1;
      if (a.pid === null && b.pid !== null) return 1;
      return (a.pid ?? 0) - (b.pid ?? 0);
    },
    defaultSortOrder: 'ascend' as const,
  },
  {
    title: 'Status',
    dataIndex: 'status',
    key: 'status',
    width: 80,
    render: (v: number) => (
      <Tag color={statusColor(v)} style={{ fontSize: 11 }}>
        {v}
      </Tag>
    ),
    sorter: (a: LaunchItem, b: LaunchItem) => a.status - b.status,
  },
  {
    title: 'Label',
    dataIndex: 'label',
    key: 'label',
    render: (v: string) => {
      const isPalo = v.includes('paloaltonetworks');
      return (
        <span style={{ ...mono, fontWeight: isPalo ? 600 : 400, color: isPalo ? 'var(--info)' : undefined }}>
          {v}
        </span>
      );
    },
    sorter: (a: LaunchItem, b: LaunchItem) => a.label.localeCompare(b.label),
  },
];

export function LaunchctlTab({ entry, viewMode }: Props) {
  const [search, setSearch] = useState('');

  const filtered = useMemo(() => {
    const allItems = entry
      ? (Array.isArray(entry.data) ? entry.data : []) as LaunchItem[]
      : [];
    if (!search) return allItems;
    const needle = search.toLowerCase();
    return allItems.filter((item) => item.label.toLowerCase().includes(needle));
  }, [entry, search]);

  if (!entry) {
    return <div style={{ color: 'var(--text-dim)', fontSize: 12, padding: 16 }}>No autostart data available.</div>;
  }

  if (viewMode !== 'View') {
    return <RawJsonView entry={entry} viewMode={viewMode} />;
  }

  return (
    <div>
      <div style={{ marginBottom: 12 }}>
        <Input
          prefix={<SearchOutlined style={{ color: 'var(--text-dim)' }} />}
          placeholder="Filter by label..."
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
        rowKey="label"
        size="small"
        pagination={{ pageSize: 50, showSizeChanger: false, size: 'small' }}
      />
    </div>
  );
}
