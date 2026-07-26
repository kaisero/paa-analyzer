import type { ReactNode } from 'react';
import { StatusDot } from '../common/StatusDot';
import type { HipStatusValue } from '../common/StatusDot';

interface Props {
  status: HipStatusValue;
  name: string;
  verdict: string;
  stats: ReactNode;
  recede?: boolean;
  expandable: boolean;
  open: boolean;
  onToggle: () => void;
  children?: ReactNode;
}

/**
 * One row of the compliance checklist. Collapsed height is uniform regardless
 * of how much detail the category carries — that uniformity is the whole point
 * of the layout, so the collapsed row must never grow to fit its content.
 */
export function ChecklistRow({
  status, name, verdict, stats, recede = false, expandable, open, onToggle, children,
}: Props) {
  return (
    <div className="hip-row">
      <div
        role={expandable ? 'button' : undefined}
        tabIndex={expandable ? 0 : undefined}
        onClick={expandable ? onToggle : undefined}
        onKeyDown={
          expandable
            ? (e) => { if (e.key === 'Enter' || e.key === ' ') { e.preventDefault(); onToggle(); } }
            : undefined
        }
        className={expandable ? 'hip-row-summary' : undefined}
        style={{
          display: 'flex', alignItems: 'center', gap: 12,
          padding: '10px 14px',
          cursor: expandable ? 'pointer' : 'default',
          opacity: recede ? 0.62 : 1,
        }}
      >
        <StatusDot status={status} />
        <span style={{ width: 170, flexShrink: 0, fontSize: 12.5, fontWeight: 600 }}>{name}</span>
        <span
          style={{
            flex: 1, minWidth: 0, fontSize: 12, color: 'var(--text-sec)',
            overflow: 'hidden', textOverflow: 'ellipsis', whiteSpace: 'nowrap',
          }}
          title={verdict}
        >
          {verdict}
        </span>
        <span style={{ display: 'flex', gap: 14, fontFamily: 'var(--mono)', fontSize: 10.5, color: 'var(--text-dim)' }}>
          {stats}
        </span>
        <span style={{ width: 12, color: 'var(--text-dim)', fontSize: 10 }}>
          {expandable ? (open ? '▾' : '▸') : ''}
        </span>
      </div>
      {open && children && <div style={{ padding: '4px 14px 16px 40px' }}>{children}</div>}
    </div>
  );
}
