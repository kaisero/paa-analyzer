import { Table } from 'antd';
import type { StateEntry } from '../../api/types';
import type { ViewMode } from '../common/ViewToggle';
import { RawJsonView } from './RawJsonView';

interface Props {
  entry: StateEntry | undefined;
  viewMode: ViewMode;
}

const mono = { fontFamily: '"JetBrains Mono", monospace', fontSize: 11 };

export function InstalledAppsTab({ entry, viewMode }: Props) {
  if (!entry) {
    return <div style={{ color: 'var(--text-dim)', fontSize: 12, padding: 16 }}>No application data available.</div>;
  }

  if (viewMode !== 'View') {
    return <RawJsonView entry={entry} viewMode={viewMode} />;
  }

  const data = entry.data;

  // Windows format: [{name, version}]
  if (Array.isArray(data) && data.length > 0 && typeof data[0] === 'object' && 'version' in data[0]) {
    return (
      <Table
        dataSource={data as Array<{ name: string; version: string }>}
        columns={[
          { title: 'Name', dataIndex: 'name', key: 'name', render: (v: string) => <span style={{ ...mono, fontWeight: 500 }}>{v}</span> },
          { title: 'Version', dataIndex: 'version', key: 'version', width: 200, render: (v: string) => <span style={mono}>{v}</span> },
        ]}
        rowKey="name"
        size="small"
        pagination={false}
      />
    );
  }

  // macOS format: string[]
  if (Array.isArray(data)) {
    const items = (data as string[]).map((name) => ({ name }));
    return (
      <Table
        dataSource={items}
        columns={[
          { title: 'Application', dataIndex: 'name', key: 'name', render: (v: string) => <span style={mono}>{v}</span> },
        ]}
        rowKey="name"
        size="small"
        pagination={{ pageSize: 50, showSizeChanger: false, size: 'small' }}
      />
    );
  }

  return <RawJsonView entry={entry} viewMode="JSON" />;
}
