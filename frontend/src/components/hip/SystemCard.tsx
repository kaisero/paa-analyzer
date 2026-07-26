import { useState } from 'react';
import type { HipReport } from '../../api/types';
import { HipCard } from './HipCard';
import { HostInfoCard } from './HostInfoCard';
import { ModuleToggle } from './ModuleToggle';
import type { HipViewMode } from './ModuleToggle';
import { RawBlock } from './RawBlock';

interface Props {
  report: HipReport;
}

export function SystemCard({ report }: Props) {
  const [view, setView] = useState<HipViewMode>('Grid');

  // HostInfoCard no longer shows its own report-version chrome (companion
  // edit below), so SystemCard carries it in its own `extra` instead.
  const extra = (
    <div style={{ display: 'flex', alignItems: 'center', gap: 10 }}>
      {report.version && (
        <span style={{ fontFamily: 'var(--mono)', fontSize: 10, color: 'var(--text-dim)' }}>
          report v{report.version}
        </span>
      )}
      <ModuleToggle modes={['Grid', 'JSON']} value={view} onChange={setView} />
    </div>
  );

  return (
    <HipCard title="System" extra={extra}>
      {view === 'JSON' ? (
        <RawBlock
          label="host_info — parsed model"
          text={JSON.stringify(report.host_info, null, 2)}
          emptyNote="No host info in this report."
        />
      ) : report.host_info ? (
        // report.host_info is HipHostInfo | null — HostInfoCard's prop is not
        // nullable, so this must be guarded here rather than passed through.
        <HostInfoCard hostInfo={report.host_info} />
      ) : (
        <div style={{ color: 'var(--text-dim)', fontSize: 12 }}>No host info in this report.</div>
      )}
    </HipCard>
  );
}
