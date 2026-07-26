import { Tooltip } from 'antd';
import type { HipProduct, OpswatError } from '../../api/types';
import { StatusDot } from '../common/StatusDot';

// Labels for attribute keys we have seen in real reports. Anything else is
// rendered with its raw key (Decision 4: the attribute dict is a passthrough,
// so the UI must never depend on a fixed key set).
const ATTR_LABELS: Record<string, string> = {
  'real-time-protection': 'real-time protection',
  'last-full-scan-time': 'last full scan',
  'last-backup-time': 'last backup',
  'is-enabled': 'enabled',
  engver: 'engine version',
  prodType: 'product type',
  osType: 'os type',
};

// Attributes rendered first when present; everything else keeps model order.
const ATTR_PRIORITY = [
  'real-time-protection',
  'is-enabled',
  'last-backup-time',
  'last-full-scan-time',
];

function formatValue(val: unknown): string {
  if (Array.isArray(val)) return val.map((v) => String(v)).join(', ');
  return String(val);
}

function sortedAttributes(attributes: Record<string, unknown>): Array<[string, unknown]> {
  const entries = Object.entries(attributes).filter(
    // `drives` is rendered from the typed `drives` field instead.
    ([key, val]) => key !== 'drives' && val != null && val !== '',
  );
  return entries.sort(([a], [b]) => {
    const ia = ATTR_PRIORITY.indexOf(a);
    const ib = ATTR_PRIORITY.indexOf(b);
    return (ia === -1 ? ATTR_PRIORITY.length : ia) - (ib === -1 ? ATTR_PRIORITY.length : ib);
  });
}

function errorTooltip(errors: OpswatError[]) {
  return (
    <div style={{ fontFamily: 'var(--mono)', fontSize: 11, lineHeight: 1.6 }}>
      {errors.map((e, i) => (
        <div key={i}>
          error {e.code} · method {e.method}
          {e.method_name ? ` (${e.method_name})` : ''}
          {e.code_meaning ? ` — ${e.code_meaning}` : ''}
        </div>
      ))}
    </div>
  );
}

function Pair({ label, value }: { label: string; value: string }) {
  return (
    <>
      <div style={{ color: 'var(--text-dim)', fontSize: 11 }}>{label}</div>
      <div
        style={{
          color: 'var(--text-sec)',
          fontFamily: 'var(--mono)',
          fontSize: 11,
          wordBreak: 'break-word',
        }}
      >
        {value}
      </div>
    </>
  );
}

interface Props {
  product: HipProduct;
  /** Rules between rows; the first row in a card sits under the header rule. */
  divider?: boolean;
}

export function ProductRow({ product, divider = true }: Props) {
  const attrs = sortedAttributes(product.attributes ?? {});
  const drives = product.drives ?? [];
  const meta = [product.version, product.vendor].filter(Boolean).join(' · ');
  const extras: Array<[string, string]> = [];
  if (product.def_version) extras.push(['definitions', product.def_version]);
  if (product.def_date) extras.push(['definition date', product.def_date]);

  return (
    <div
      style={{
        padding: '7px 12px',
        borderTop: divider ? '1px solid var(--border-soft)' : undefined,
      }}
    >
      <div style={{ display: 'flex', alignItems: 'baseline', gap: 8 }}>
        <div style={{ paddingTop: 4 }}>
          <StatusDot status={product.status} reason={product.status_reason} />
        </div>
        <div style={{ flex: 1, minWidth: 0 }}>
          <div
            style={{
              color: 'var(--text)',
              fontSize: 12,
              fontWeight: 600,
              wordBreak: 'break-word',
            }}
          >
            {product.name ?? 'Unnamed product'}
          </div>
          {meta && (
            <div style={{ color: 'var(--text-dim)', fontFamily: 'var(--mono)', fontSize: 11 }}>
              {meta}
            </div>
          )}
        </div>
        {product.errors.length > 0 && (
          <Tooltip title={errorTooltip(product.errors)} placement="left">
            <span
              style={{
                color: 'var(--err)',
                fontFamily: 'var(--mono)',
                fontSize: 10,
                fontWeight: 600,
                whiteSpace: 'nowrap',
                cursor: 'help',
              }}
            >
              {product.errors.length} err
            </span>
          </Tooltip>
        )}
      </div>

      {(attrs.length > 0 || drives.length > 0 || extras.length > 0) && (
        <div
          style={{
            display: 'grid',
            gridTemplateColumns: 'minmax(0, auto) minmax(0, 1fr)',
            columnGap: 10,
            rowGap: 2,
            marginTop: 5,
            marginLeft: 16,
          }}
        >
          {attrs.map(([key, val]) => (
            <Pair key={key} label={ATTR_LABELS[key] ?? key} value={formatValue(val)} />
          ))}
          {extras.map(([label, val]) => (
            <Pair key={label} label={label} value={val} />
          ))}
          {drives.map((d, i) => (
            <Pair key={`drive-${i}`} label={d.name ?? 'drive'} value={d.enc_state ?? 'unknown'} />
          ))}
        </div>
      )}
    </div>
  );
}
