import { useState } from 'react';
import type { HipData } from '../../api/types';
import { ComplianceChecklist } from './ComplianceChecklist';
import { GatewayCard } from './GatewayCard';
import { HipReportHeader } from './HipReportHeader';
import { MissingPatchesPanel } from './MissingPatchesPanel';
import { SystemCard } from './SystemCard';

interface Props {
  hip: HipData;
  sessionId: string | undefined;
}

export function HipReportPanel({ hip, sessionId }: Props) {
  // Cycles arrive newest first (Decision 7): open on the latest.
  const [selectedIndex, setSelectedIndex] = useState(hip.cycles[0].index);
  const cycle = hip.cycles.find((c) => c.index === selectedIndex) ?? hip.cycles[0];

  return (
    <div>
      <HipReportHeader hip={hip} selectedIndex={cycle.index} onSelect={setSelectedIndex} />

      <div
        style={{
          display: 'grid',
          gridTemplateColumns: 'repeat(auto-fit, minmax(380px, 1fr))',
          gap: 16,
          // stretch (the grid default): the two header cards match heights
          // rather than leaving a ragged bottom edge.
          alignItems: 'stretch',
          marginBottom: 20,
        }}
      >
        {cycle.report && <SystemCard report={cycle.report} />}
        <GatewayCard gateways={hip.gateways} />
      </div>

      <div style={{ display: 'flex', flexDirection: 'column', gap: 20 }}>
        <ComplianceChecklist cycle={cycle} sessionId={sessionId} />
        <MissingPatchesPanel cycle={cycle} sessionId={sessionId} />
      </div>
    </div>
  );
}
