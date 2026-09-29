import { useState } from 'react';
import { useParams } from 'react-router-dom';
import { Spin } from 'antd';
import { useStateBatch } from '../api/hooks';
import { OverviewCards } from '../components/agent-status/OverviewCards';
import { FeaturesPanel } from '../components/agent-status/FeaturesPanel';
import { SystemDetails } from '../components/agent-status/SystemDetails';
import { ForwardingTable } from '../components/agent-status/ForwardingTable';
import { PacliTerminal } from '../components/agent-status/PacliTerminal';
import { ViewToggle } from '../components/common/ViewToggle';
import type { ViewMode } from '../components/common/ViewToggle';

function SectionTitle({ children, right }: { children: React.ReactNode; right?: React.ReactNode }) {
  return (
    <div
      style={{
        display: 'flex', alignItems: 'center', gap: 12,
        margin: '28px 0 14px',
      }}
    >
      <div
        style={{
          fontSize: 11, fontWeight: 700, letterSpacing: '0.14em',
          textTransform: 'uppercase', borderLeft: '3px solid var(--accent)',
          paddingLeft: 10, color: 'var(--text-sec)',
        }}
      >
        {children}
      </div>
      {right && <div style={{ marginLeft: 'auto' }}>{right}</div>}
    </div>
  );
}

const BATCH_KEYS = [
  'Agent.Core.status',
  'Agent.Core.version',
  'Agent.Core.sw_vers',
  'System.Core.uname',
  'System.Networking.external_ip',
  'Agent.Networking.tunnel',
  'Agent.Explicit Proxy.ep',
  'Agent.ADNS Resolver.adns',
  'Agent.ADEM.adem_status',
  'Agent.DLP.dlp_status',
  'Agent.Core.epm_status',
  // Windows equivalents
  'System.Core.systeminfo',
  'System.Networking.ipconfig',
];

export function AgentStatusPage() {
  const { sessionId } = useParams<{ sessionId: string }>();
  const { data, isLoading } = useStateBatch(sessionId, BATCH_KEYS);
  const stateData = data?.data;
  const [detailsView, setDetailsView] = useState<ViewMode>('View');
  const [terminalView, setTerminalView] = useState<ViewMode>('Raw');

  if (isLoading && !stateData) {
    return (
      <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'center', height: '100%' }}>
        <Spin size="large" />
      </div>
    );
  }

  return (
    <div style={{ height: '100%', overflowY: 'auto', padding: 24 }}>
      <div style={{ maxWidth: 1200, margin: '0 auto', display: 'flex', flexDirection: 'column' }}>
        {/* Report Header */}
        <div style={{ borderWidth: 1, borderStyle: 'solid', borderColor: 'var(--border)',
          borderLeftWidth: 3, borderLeftColor: 'var(--accent)',
          background: 'var(--surface)', padding: '18px 22px', marginBottom: 28 }}>
          <h2 style={{ fontSize: 18, fontWeight: 700, margin: 0 }}>
            Prisma Access Agent — <span style={{ color: 'var(--accent)' }}>Diagnostic Report</span>
          </h2>
          <div style={{ marginTop: 8, fontFamily: 'var(--mono)', fontSize: 11, color: 'var(--text-sec)' }}>
            SESSION: {sessionId}
          </div>
        </div>
        <SectionTitle>System Overview</SectionTitle>
        <OverviewCards stateData={stateData} loading={isLoading} />
        <SectionTitle>Modules</SectionTitle>
        <FeaturesPanel stateData={stateData} loading={isLoading} />
        <SectionTitle right={<ViewToggle modes={['View', 'Raw', 'JSON']} value={detailsView} onChange={setDetailsView} />}>
          System Details
        </SectionTitle>
        <SystemDetails viewMode={detailsView} />

        <SectionTitle>Forwarding Profile</SectionTitle>
        <ForwardingTable />

        <SectionTitle right={<ViewToggle modes={['Raw', 'JSON']} value={terminalView} onChange={setTerminalView} />}>
          PACLI Terminal
        </SectionTitle>
        <PacliTerminal viewMode={terminalView} />
      </div>
    </div>
  );
}
