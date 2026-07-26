import type { HipReport } from '../../api/types';
import { HipCard } from './HipCard';

type CustomChecks = NonNullable<HipReport['custom_checks']>;

function isRecord(val: unknown): val is Record<string, unknown> {
  return typeof val === 'object' && val !== null && !Array.isArray(val);
}

function scalarText(val: unknown): string | null {
  if (val == null || val === '') return null;
  if (isRecord(val) || Array.isArray(val)) return null;
  return String(val);
}

/** `exist` is the one field whose value reads as a verdict. */
function existColor(exist: string | null): string {
  if (exist === 'yes') return 'var(--ok)';
  if (exist === 'no') return 'var(--warn)';
  return 'var(--text-dim)';
}

function CheckLine({
  name,
  exist,
  value,
  indent,
}: {
  name: string;
  exist: string | null;
  value: string | null;
  indent?: boolean;
}) {
  return (
    <div
      style={{
        display: 'flex',
        alignItems: 'baseline',
        gap: 8,
        padding: '3px 0',
        marginLeft: indent ? 12 : 0,
      }}
    >
      <span
        style={{
          color: indent ? 'var(--text-sec)' : 'var(--text)',
          fontFamily: 'var(--mono)',
          fontSize: 11,
          fontWeight: indent ? 400 : 600,
          wordBreak: 'break-all',
        }}
      >
        {name}
      </span>
      {exist && (
        <span style={{ color: existColor(exist), fontFamily: 'var(--mono)', fontSize: 10 }}>
          exist {exist}
        </span>
      )}
      {value && (
        <span
          style={{
            color: 'var(--text-sec)',
            fontFamily: 'var(--mono)',
            fontSize: 11,
            wordBreak: 'break-all',
            marginLeft: 'auto',
          }}
        >
          {value}
        </span>
      )}
    </div>
  );
}

interface Props {
  customChecks: CustomChecks;
}

/**
 * Renders whatever the custom-check subtree contains. The shape differs per
 * platform (`plist` on macOS, `registry` on Windows), so nothing here is keyed
 * on a specific member name: scalars become a line, nested arrays become
 * indented lines.
 */
export function CustomChecksCard({ customChecks }: Props) {
  const entries = customChecks.entries ?? [];

  return (
    <HipCard
      title="custom checks"
      extra={
        <span style={{ fontFamily: 'var(--mono)', fontSize: 10, color: 'var(--text-dim)' }}>
          {customChecks.kind}
        </span>
      }
    >
      {entries.length === 0 && (
        <div style={{ color: 'var(--text-dim)', fontSize: 11 }}>No custom checks reported.</div>
      )}
      {entries.filter(isRecord).map((entry, i) => {
        const name = scalarText(entry.name) ?? `check ${i + 1}`;
        const nested = Object.entries(entry).filter(([, val]) => Array.isArray(val));
        return (
          <div key={`${name}-${i}`} style={{ marginBottom: i === entries.length - 1 ? 0 : 6 }}>
            <CheckLine
              name={name}
              exist={scalarText(entry.exist)}
              value={scalarText(entry.value)}
            />
            {nested.map(([key, val]) =>
              (val as unknown[]).filter(isRecord).map((member, j) => (
                <CheckLine
                  key={`${key}-${j}`}
                  indent
                  name={scalarText(member.name) ?? key}
                  exist={scalarText(member.exist)}
                  value={scalarText(member.value)}
                />
              )),
            )}
          </div>
        );
      })}
    </HipCard>
  );
}
