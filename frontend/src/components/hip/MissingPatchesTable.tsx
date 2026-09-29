import { Table } from 'antd';
import type { TableColumnsType } from 'antd';
import type { MissingPatch } from '../../api/types';
import { titleCase } from './hipVerdict';

const SEVERITY_COLOR: Record<string, string> = {
  critical: 'var(--err)',
  important: 'var(--warn)',
  moderate: 'var(--info)',
  low: 'var(--text-sec)',
};

interface Row extends MissingPatch {
  key: number;
  /**
   * Owning HIP category, index-aligned with the incoming `categoryNames` prop
   * (null when the table is used inside a single category's checklist row,
   * where `categoryNames` is omitted because the category is already obvious
   * from context).
   */
  hipCategory: string | null;
}

const BASE_COLUMNS: TableColumnsType<Row> = [
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
  /**
   * Owning HIP category per patch, index-aligned with `patches`. Supplied only
   * when patches are aggregated across categories; the patch itself carries no
   * such field (`MissingPatch.category` is the patch's own kind, e.g. "update").
   */
  categoryNames?: Array<string | null>;
}

export function MissingPatchesTable({ patches, source, categoryNames }: Props) {
  const rows: Row[] = patches.map((p, i) => ({
    ...p,
    key: i,
    hipCategory: categoryNames?.[i] ?? null,
  }));

  const columns: TableColumnsType<Row> = [
    ...(categoryNames
      ? [{
          title: 'Category',
          dataIndex: 'hipCategory',
          key: 'hipCategory',
          width: 150,
          render: (v: string | null) => titleCase(v),
        }]
      : []),
    ...BASE_COLUMNS,
  ];

  return (
    <div>
      {source && (
        <div style={{ fontFamily: 'var(--mono)', fontSize: 10, color: 'var(--text-dim)', padding: '6px 12px' }}>
          from {source}
        </div>
      )}
      <Table<Row> columns={columns} dataSource={rows} size="small" pagination={false} />
    </div>
  );
}
