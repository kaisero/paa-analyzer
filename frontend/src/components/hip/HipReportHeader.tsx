import { Select } from 'antd';
import type { HipData } from '../../api/types';

/** Local-time label, matching the log viewer's timestamp convention. */
// eslint-disable-next-line react-refresh/only-export-components
export function fmtCycleTime(iso: string | null): string {
  if (!iso) return 'unknown time';
  const d = new Date(iso);
  if (isNaN(d.getTime())) return iso;
  const pad = (n: number) => String(n).padStart(2, '0');
  return `${d.getFullYear()}-${pad(d.getMonth() + 1)}-${pad(d.getDate())} ${pad(d.getHours())}:${pad(
    d.getMinutes(),
  )}:${pad(d.getSeconds())}`;
}

interface CountProps { label: string; value: number; color?: string }

function Count({ label, value, color }: CountProps) {
  return (
    <span style={{ display: 'inline-flex', gap: 6, alignItems: 'baseline' }}>
      <span style={{ fontSize: 11, color: 'var(--text-sec)' }}>{label}</span>
      <b style={{ fontFamily: 'var(--mono)', fontSize: 13, color: color ?? 'var(--text)' }}>
        {value}
      </b>
    </span>
  );
}

interface Props {
  hip: HipData;
  selectedIndex: number;
  onSelect: (index: number) => void;
}

export function HipReportHeader({ hip, selectedIndex, onSelect }: Props) {
  const cycles = hip.cycles;
  const cycle = cycles.find((c) => c.index === selectedIndex) ?? cycles[0];
  const { warn, unknown, errors, missing_patches: missingPatches } = cycle.counts;
  const cycleCount = cycles.length;

  // Three states, not two: a cycle that never dispatched is not the same as
  // one that dispatched and failed.
  const dispatchText = cycle.dispatch.sent
    ? (cycle.dispatch.succeeded ? 'dispatch succeeded' : 'dispatch failed')
    : 'not dispatched';

  return (
    <div
      style={{
        border: '1px solid var(--border)',
        borderLeft: '3px solid var(--accent)',
        background: 'var(--surface)',
        padding: '16px 20px',
        marginBottom: 20,
      }}
    >
      <div style={{ display: 'flex', alignItems: 'flex-start', gap: 16, flexWrap: 'wrap' }}>
        <div style={{ flex: 1, minWidth: 260 }}>
          <h2 style={{ fontSize: 17, fontWeight: 700, margin: 0 }}>HIP Report</h2>
          <div style={{ marginTop: 6, fontFamily: 'var(--mono)', fontSize: 11, color: 'var(--text-sec)' }}>
            {/* Requirement 4 removed the platform toggle, not the platform
                fact — this and the cycle count used to live in HipPage's own
                banner (Task 9 removes that banner). */}
            {hip.platform.toUpperCase()} &middot; {cycleCount} cycle{cycleCount === 1 ? '' : 's'}
            &nbsp;·&nbsp; collection: {hip.collection ?? 'unknown'} &nbsp;·&nbsp; next check: {fmtCycleTime(hip.next_check)}
            &nbsp;·&nbsp; {dispatchText}
          </div>
        </div>
        <Select
          value={cycle.index}
          onChange={onSelect}
          style={{ minWidth: 300 }}
          options={cycles.map((c) => ({
            value: c.index,
            label: `Cycle ${c.index} — ${fmtCycleTime(c.generate_time)}` +
              (c.duration_s != null ? ` (${c.duration_s}s)` : '') +
              (c.partial ? ' · partial' : ''),
          }))}
        />
      </div>

      <div style={{ display: 'flex', gap: 18, flexWrap: 'wrap', alignItems: 'center', marginTop: 12 }}>
        <Count label="Warn" value={warn} color={warn ? 'var(--warn)' : undefined} />
        {/* unknown is a collection gap, never an error — see Global Constraints */}
        <Count label="Unknown" value={unknown} color={unknown ? 'var(--info)' : undefined} />
        <Count label="Errors" value={errors} color={errors ? 'var(--err)' : undefined} />
        <Count label="Missing Patches" value={missingPatches} />
        <Count label="Duration" value={cycle.duration_s ?? 0} />
        {cycle.partial && (
          <span
            style={{
              fontFamily: 'var(--mono)', fontSize: 10, fontWeight: 700,
              color: 'var(--warn)', border: '1px solid var(--warn)',
              padding: '1px 6px', textTransform: 'uppercase', letterSpacing: '0.06em',
            }}
          >
            partial
          </span>
        )}
      </div>
    </div>
  );
}
