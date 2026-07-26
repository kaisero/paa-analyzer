import { Table } from 'antd';
import type { TableColumnsType } from 'antd';
import type { MissingPatch } from '../../api/types';
import { HipCard } from './HipCard';

const SEVERITY_COLOR: Record<string, string> = {
  critical: 'var(--err)',
  important: 'var(--warn)',
  moderate: 'var(--info)',
  low: 'var(--text-sec)',
};

interface Row extends MissingPatch {
  key: number;
}

const columns: TableColumnsType<Row> = [
  {
    title: 'Severity',
    dataIndex: 'severity',
    key: 'severity',
    width: 110,
    render: (v: string | null) => (
      <span
        style={{
          fontFamily: 'var(--mono)',
          fontSize: 11,
          fontWeight: 600,
          color: v ? (SEVERITY_COLOR[v.toLowerCase()] ?? 'var(--text-sec)') : 'var(--text-dim)',
        }}
      >
        {v ?? '—'}
      </span>
    ),
  },
  {
    title: 'Patch',
    dataIndex: 'title',
    key: 'title',
    render: (v: string | null, row: Row) => (
      <div>
        <div style={{ color: 'var(--text)', fontSize: 12 }}>{v ?? '—'}</div>
        {row.description && (
          <div style={{ color: 'var(--text-dim)', fontSize: 11 }}>{row.description}</div>
        )}
      </div>
    ),
  },
  {
    title: 'Vendor / Product',
    key: 'product',
    width: 160,
    render: (_: unknown, row: Row) => (
      <span style={{ fontFamily: 'var(--mono)', fontSize: 11, color: 'var(--text-sec)' }}>
        {[row.vendor, row.product].filter(Boolean).join(' · ') || '—'}
      </span>
    ),
  },
  {
    title: 'Reference',
    key: 'reference',
    width: 130,
    render: (_: unknown, row: Row) => (
      <span style={{ fontFamily: 'var(--mono)', fontSize: 11, color: 'var(--text-sec)' }}>
        {row.kb_article_id ?? row.security_bulletin_id ?? '—'}
      </span>
    ),
  },
  {
    title: 'Reboot',
    dataIndex: 'reboot_required',
    key: 'reboot_required',
    width: 80,
    render: (v: boolean) => (
      <span
        style={{
          fontFamily: 'var(--mono)',
          fontSize: 11,
          color: v ? 'var(--warn)' : 'var(--text-dim)',
        }}
      >
        {v ? 'yes' : 'no'}
      </span>
    ),
  },
];

interface Props {
  patches: MissingPatch[];
  /** Which log the patches came from — they arrive in a separate document. */
  source?: string | null;
}

export function MissingPatchesTable({ patches, source }: Props) {
  const rows: Row[] = patches.map((p, i) => ({ ...p, key: i }));

  return (
    <HipCard
      title={`missing patches (${patches.length})`}
      bodyPadding={0}
      extra={
        source ? (
          <span style={{ fontFamily: 'var(--mono)', fontSize: 10, color: 'var(--text-dim)' }}>
            from {source}
          </span>
        ) : undefined
      }
    >
      <Table<Row> columns={columns} dataSource={rows} size="small" pagination={false} />
    </HipCard>
  );
}
