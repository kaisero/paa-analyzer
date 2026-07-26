import { Tooltip } from 'antd';
import type { HipCategory } from '../../api/types';
import { StatusDot } from '../common/StatusDot';

interface Props {
  categories: HipCategory[];
}

/**
 * Categories the report carried with zero products. They get one shared strip
 * rather than a card each (Decision 11) — an empty card per category leaves
 * ragged holes in the grid and overstates the finding.
 */
export function NotDetectedStrip({ categories }: Props) {
  if (categories.length === 0) return null;

  return (
    <div
      style={{
        display: 'flex',
        alignItems: 'center',
        flexWrap: 'wrap',
        gap: 8,
        padding: '7px 12px',
        border: '1px solid var(--border-soft)',
        background: 'var(--surface)',
        fontFamily: 'var(--mono)',
        fontSize: 11,
        color: 'var(--text-dim)',
      }}
    >
      <StatusDot status="not-detected" />
      <span>not detected:</span>
      {categories.map((category, i) => (
        <span key={category.name ?? i} style={{ color: 'var(--text-sec)' }}>
          {i > 0 && <span style={{ color: 'var(--text-dim)', marginRight: 8 }}>·</span>}
          <Tooltip title={category.status_reason} placement="top">
            <span style={{ cursor: category.status_reason ? 'help' : undefined }}>
              {category.name ?? 'unnamed category'}
            </span>
          </Tooltip>
        </span>
      ))}
    </div>
  );
}
