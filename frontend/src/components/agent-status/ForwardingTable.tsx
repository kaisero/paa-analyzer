import { Table, Tooltip, Spin } from 'antd';
import { Link, useParams } from 'react-router-dom';
import { useForwardingProfile } from '../../api/hooks';
import type { ForwardingRule } from '../../api/types';

function EllipsisCell({ value }: { value: string }) {
  return (
    <Tooltip
      title={<span style={{ whiteSpace: 'pre-wrap', wordBreak: 'break-all' }}>{value}</span>}
      overlayStyle={{ maxWidth: 480 }}
    >
      <div style={{
        fontFamily: '"JetBrains Mono", monospace',
        fontSize: 11,
        overflow: 'hidden',
        textOverflow: 'ellipsis',
        whiteSpace: 'nowrap',
      }}>
        {value}
      </div>
    </Tooltip>
  );
}

export function ForwardingTable() {
  const { sessionId } = useParams<{ sessionId: string }>();
  const { data, isLoading } = useForwardingProfile(sessionId);

  if (isLoading) {
    return (
      <div style={{ display: 'flex', justifyContent: 'center', padding: 48 }}>
        <Spin />
      </div>
    );
  }

  const profile = data?.data;
  if (!profile) {
    return <div style={{ color: 'var(--text-dim)', fontSize: 12 }}>No forwarding profile data available.</div>;
  }

  const columns = [
    {
      title: 'Prio',
      dataIndex: 'priority',
      key: 'priority',
      width: 60,
    },
    {
      title: 'Name',
      dataIndex: 'name',
      key: 'name',
      width: 200,
      render: (v: string) => <span style={{ fontWeight: 500 }}>{v}</span>,
    },
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
    },
    {
      title: 'Source Apps',
      dataIndex: 'source_apps',
      key: 'source_apps',
      render: (v: string) => <EllipsisCell value={v} />,
    },
    {
      title: 'Destinations',
      dataIndex: 'destinations',
      key: 'destinations',
      render: (v: string) => <EllipsisCell value={v} />,
    },
    {
      title: 'Type',
      dataIndex: 'connection_type',
      key: 'connection_type',
      width: 120,
    },
    {
      title: 'Action',
      dataIndex: 'connect_through',
      key: 'connect_through',
      width: 130,
    },
    {
      title: 'Hitcount',
      dataIndex: 'traffic_log_hits',
      key: 'traffic_log_hits',
      width: 90,
      render: (v: number, record: ForwardingRule) => {
        if (v === 0) {
          return <span style={{ fontFamily: '"JetBrains Mono", monospace', fontSize: 11, color: 'var(--text-dim)' }}>0</span>;
        }
        const search = `Rule priority ${record.priority} matched`;
        return (
          <Link
            to={`/s/${sessionId}?source=Agent.Core.traffic_log_json&search=${encodeURIComponent(search)}`}
            style={{ fontFamily: '"JetBrains Mono", monospace', fontSize: 11, color: 'var(--info)' }}
          >
            {v.toLocaleString()}
          </Link>
        );
      },
    },
  ];

  return (
    <div>
      <div style={{ fontSize: 13, fontWeight: 600, color: 'var(--text)', marginBottom: 12 }}>
        Forwarding Profile
      </div>
      <Table
        dataSource={profile.rules}
        columns={columns}
        rowKey="priority"
        size="small"
        pagination={false}
      />
    </div>
  );
}
