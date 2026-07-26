import { Tooltip } from 'antd';

/**
 * The HIP status vocabulary (Decision 9). Products only ever carry the first
 * three; `not-detected` is category-only.
 */
export type HipStatusValue = 'ok' | 'warn' | 'unknown' | 'not-detected';

const COLOR: Record<HipStatusValue, string> = {
  ok: 'var(--ok)',
  warn: 'var(--warn)',
  // `unknown` means the value could not be queried at all — a harder failure
  // to trust than a bad-but-known value, so it takes the error colour.
  unknown: 'var(--err)',
  'not-detected': 'var(--text-dim)',
};

interface Props {
  status: HipStatusValue;
  /** `status_reason` from the model — the "show its work" sentence. */
  reason?: string | null;
  /** Optional text rendered beside the dot in the status colour. */
  label?: string;
  size?: number;
}

export function StatusDot({ status, reason, label, size = 8 }: Props) {
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
          width: size,
          height: size,
          borderRadius: '50%',
          flexShrink: 0,
          background: color,
          boxShadow: `0 0 5px ${color}`,
        }}
      />
      {label != null && (
        <span style={{ color, fontFamily: 'var(--mono)', fontSize: 11, fontWeight: 600 }}>
          {label}
        </span>
      )}
    </span>
  );

  if (!reason) return body;

  return (
    <Tooltip title={reason} placement="top">
      {body}
    </Tooltip>
  );
}
