import { useState } from 'react';
import type { HipGateway } from '../../api/types';
import { HipCard } from './HipCard';
import { ModuleToggle } from './ModuleToggle';
import type { HipViewMode } from './ModuleToggle';
import { RawBlock } from './RawBlock';

const COLLAPSED_ROWS = 5;
const STALE_DAYS = 30;
const AGING_DAYS = 7;

function label(kind: HipGateway['status_kind']): string {
  if (kind === 'success') return 'sent';
  if (kind === 'not-needed') return 'not needed';
  if (kind === 'failed') return 'failed';
  return 'unknown';
}

function colorFor(kind: HipGateway['status_kind']): string {
  if (kind === 'success') return 'var(--ok)';
  if (kind === 'failed') return 'var(--err)';
  return 'var(--text-dim)';
}

/** Failures first, then successes, then everything else; oldest first within a rank. */
function rank(kind: HipGateway['status_kind']): number {
  if (kind === 'failed') return 0;
  if (kind === 'success') return 1;
  return 2;
}

function fmtAge(days: number | null): string {
  if (days == null) return '—';
  if (days < 1) {
    const hrs = Math.round(days * 24);
    return `${hrs < 1 ? '<1' : hrs}h ago`;
  }
  return `${Math.round(days * 10) / 10}d ago`;
}

/** Staleness thresholds are a product judgement — the data defines no "stale". */
function ageColor(days: number | null): string {
  if (days == null) return 'var(--text-dim)';
  if (days > STALE_DAYS) return 'var(--warn)';
  if (days > AGING_DAYS) return 'var(--text-sec)';
  return 'var(--text-dim)';
}

interface Props {
  gateways: HipGateway[];
}

export function GatewayCard({ gateways }: Props) {
  const [view, setView] = useState<HipViewMode>('Grid');
  const [showAll, setShowAll] = useState(false);

  const sorted = [...gateways].sort(
    (a, b) => rank(a.status_kind) - rank(b.status_kind) || (b.age_days ?? 0) - (a.age_days ?? 0),
  );
  const shown = showAll ? sorted : sorted.slice(0, COLLAPSED_ROWS);
  const count = (kind: HipGateway['status_kind']) =>
    gateways.filter((g) => g.status_kind === kind).length;

  const extra = <ModuleToggle modes={['Grid', 'JSON']} value={view} onChange={setView} />;

  if (view === 'JSON') {
    return (
      <HipCard title="Gateways" extra={extra}>
        <RawBlock
          label="gateways — parsed model"
          text={gateways.length > 0 ? JSON.stringify(gateways, null, 2) : undefined}
          emptyNote="No gateway data in this bundle."
        />
      </HipCard>
    );
  }

  if (gateways.length === 0) {
    return (
      <HipCard title="Gateways" extra={extra}>
        <div style={{ fontSize: 12 }}>
          <div style={{ fontWeight: 600 }}>No gateway data in this bundle.</div>
          <div style={{ color: 'var(--text-dim)', marginTop: 4 }}>
            {/* HipData.gateways is per-bundle, not per-cycle — don't imply
                a different cycle selection would change this. */}
            This bundle reported zero gateways.
          </div>
        </div>
      </HipCard>
    );
  }

  return (
    <HipCard title="Gateways" extra={extra}>
      <div style={{ display: 'flex', gap: 16, fontFamily: 'var(--mono)', fontSize: 11, marginBottom: 10 }}>
        <span><b style={{ color: 'var(--ok)' }}>{count('success')}</b> sent</span>
        <span><b style={{ color: 'var(--text-dim)' }}>{count('not-needed')}</b> not needed</span>
        <span><b style={{ color: 'var(--err)' }}>{count('failed')}</b> failed</span>
      </div>

      {shown.map((g, i) => (
        <div
          key={g.gateway ?? i}
          style={{
            display: 'flex', alignItems: 'center', gap: 10,
            padding: '6px 0', borderTop: '1px solid var(--border-soft)',
          }}
        >
          <span style={{ flex: 1, fontSize: 12, fontWeight: 600 }}>{g.gateway ?? '—'}</span>
          <span
            title={g.last_report ?? ''}
            style={{ fontFamily: 'var(--mono)', fontSize: 10.5, color: ageColor(g.age_days) }}
          >
            {fmtAge(g.age_days)}
          </span>
          <span
            style={{
              fontFamily: 'var(--mono)', fontSize: 9.5, fontWeight: 600,
              textTransform: 'uppercase', letterSpacing: '0.06em',
              color: colorFor(g.status_kind),
            }}
          >
            {label(g.status_kind)}
          </span>
        </div>
      ))}

      {sorted.length > COLLAPSED_ROWS && (
        <button
          type="button"
          onClick={() => setShowAll((v) => !v)}
          className="hip-ghost-btn"
          style={{ marginTop: 10 }}
        >
          {showAll ? 'Show fewer' : `Show all ${sorted.length}`}
        </button>
      )}
    </HipCard>
  );
}
