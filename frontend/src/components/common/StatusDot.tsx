import { Tooltip } from 'antd';

/**
 * The HIP status vocabulary (Decision 9). Products only ever carry the first
 * three; `not-detected` is category-only.
 */
export type HipStatusValue = 'ok' | 'warn' | 'unknown' | 'not-detected';

const COLOR: Record<HipStatusValue, string> = {
  ok: 'var(--ok)',
  warn: 'var(--warn)',
  // The colour scale tracks `_SEVERITY` (paa_analyzer/hip/status.py): a
  // known-bad value (`warn`) outranks an unmeasurable one (`unknown`)
  // because it is actionable, while `unknown` is only a collection gap.
  unknown: 'var(--info)',
  'not-detected': 'var(--text-dim)',
};

interface Props {
  status: HipStatusValue;
  /** `status_reason` from the model — the "show its work" sentence. */
  reason?: string | null;
}

export function StatusDot({ status, reason }: Props) {
  const color = COLOR[status] ?? 'var(--text-dim)';

  const body = (
    <span
      style={{
        display: 'inline-flex',
        alignItems: 'center',
        gap: 6,
        cursor: reason ? 'help' : undefined,
      }}
    >
      <span
        role="img"
        aria-label={`status ${status}`}
        style={{
          width: 8,
          height: 8,
          borderRadius: '50%',
          flexShrink: 0,
          background: color,
          boxShadow: `0 0 5px ${color}`,
        }}
      />
    </span>
  );

  if (!reason) return body;

  return (
    <Tooltip title={reason} placement="top">
      {body}
    </Tooltip>
  );
}
