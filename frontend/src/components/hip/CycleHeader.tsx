import { Segmented, Select } from 'antd';
import type { HipCycle } from '../../api/types';

export type HipViewMode = 'Grid' | 'XML' | 'JSON';

const VIEW_MODES: HipViewMode[] = ['Grid', 'XML', 'JSON'];

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

function Count({ value, label, color }: { value: number; label: string; color: string }) {
  if (value === 0) return null;
  return (
    <span style={{ color }}>
      {value} {label}
    </span>
  );
}

interface Props {
  cycles: HipCycle[];
  selectedIndex: number;
  onSelect: (index: number) => void;
  viewMode: HipViewMode;
  onViewMode: (mode: HipViewMode) => void;
}

export function CycleHeader({ cycles, selectedIndex, onSelect, viewMode, onViewMode }: Props) {
  const position = cycles.findIndex((c) => c.index === selectedIndex) + 1;
  const cycle = cycles.find((c) => c.index === selectedIndex);
  const counts = cycle?.counts;

  return (
    <div
      style={{
        display: 'flex',
        alignItems: 'center',
        justifyContent: 'space-between',
        flexWrap: 'wrap',
        gap: 12,
        marginBottom: 12,
      }}
    >
      <div style={{ display: 'flex', alignItems: 'center', flexWrap: 'wrap', gap: 12 }}>
        <Select
          size="small"
          value={selectedIndex}
          onChange={onSelect}
          style={{ minWidth: 220 }}
          aria-label="HIP cycle"
          options={cycles.map((c) => ({
            value: c.index,
            label: `${fmtCycleTime(c.generate_time)}${c.partial ? ' (partial)' : ''}`,
          }))}
        />
        <span
          style={{
            display: 'inline-flex',
            alignItems: 'center',
            flexWrap: 'wrap',
            gap: 10,
            fontFamily: 'var(--mono)',
            fontSize: 11,
            color: 'var(--text-dim)',
          }}
        >
          <span>
            {position} of {cycles.length}
          </span>
          {cycle?.duration_s != null && <span>{cycle.duration_s}s</span>}
          {counts && (
            <>
              <Count value={counts.warn} label="warn" color="var(--warn)" />
              <Count value={counts.unknown} label="unknown" color="var(--err)" />
              <Count value={counts.errors} label="errors" color="var(--err)" />
              <Count value={counts.missing_patches} label="missing patches" color="var(--warn)" />
            </>
          )}
        </span>
      </div>
      <Segmented
        size="small"
        options={VIEW_MODES}
        value={viewMode}
        onChange={(v) => onViewMode(v as HipViewMode)}
      />
    </div>
  );
}
