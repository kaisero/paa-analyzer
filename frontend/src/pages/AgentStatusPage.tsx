import { useParams } from 'react-router-dom';
import { Spin } from 'antd';
import { useStateBatch } from '../api/hooks';
import { OverviewCards } from '../components/agent-status/OverviewCards';
import { FeaturesPanel } from '../components/agent-status/FeaturesPanel';
import { SystemDetails } from '../components/agent-status/SystemDetails';
import { ForwardingTable } from '../components/agent-status/ForwardingTable';
import { PacliTerminal } from '../components/agent-status/PacliTerminal';

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

  if (isLoading && !stateData) {
    return (
      <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'center', height: '100%' }}>
        <Spin size="large" />
      </div>
    );
  }

  return (
    <div style={{
      height: '100%',
      overflowY: 'auto',
      padding: 24,
    }}>
      <div style={{ maxWidth: 1200, margin: '0 auto', display: 'flex', flexDirection: 'column', gap: 24 }}>
        <OverviewCards stateData={stateData} loading={isLoading} />
        <FeaturesPanel stateData={stateData} loading={isLoading} />
        <SystemDetails />
        <ForwardingTable />
        <PacliTerminal />
      </div>
    </div>
  );
}
