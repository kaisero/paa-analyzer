import { Badge, Card, Spin } from 'antd';
import type { StateBatchResponse } from '../../api/types';

interface Props {
  stateData: StateBatchResponse | undefined;
  loading: boolean;
}

interface FeatureConfig {
  label: string;
  stateKey: string;
  getStatus: (data: Record<string, unknown>) => { active: boolean; status: string; details?: string };
}

const FEATURES: FeatureConfig[] = [
  {
    label: 'Tunnel',
    stateKey: 'Agent.Networking.tunnel',
    getStatus: (d) => {
      const s = String(d.tunnel_status ?? 'Unknown');
      return { active: s.includes('Connected') && !s.includes('Not'), status: s };
    },
  },
  {
    label: 'Explicit Proxy',
    stateKey: 'Agent.Explicit Proxy.ep',
    getStatus: (d) => {
      const fqdn = String(d.global_explicit_proxy_fqdn ?? '');
      const port = String(d.global_explicit_proxy_port ?? '');
      if (!fqdn) return { active: false, status: 'Not Configured' };
      return { active: true, status: 'Configured', details: `${fqdn}:${port}` };
    },
  },
  {
    label: 'ADNS Resolver',
    stateKey: 'Agent.ADNS Resolver.adns',
    getStatus: (d) => {
      const s = String(d.state ?? 'Unknown');
      return { active: !s.toLowerCase().includes('disabled'), status: s };
    },
  },
  {
    label: 'ADEM',
    stateKey: 'Agent.ADEM.adem_status',
    getStatus: (d) => {
      const s = String(d.state ?? 'Unknown');
      const version = d.version ? `v${d.version}` : '';
      const tenant = d.tenant ? `Tenant: ${d.tenant}` : '';
      const details = [version, tenant].filter(Boolean).join(' | ');
      return { active: s === 'Enabled', status: s, details };
    },
  },
  {
    label: 'Endpoint DLP',
    stateKey: 'Agent.DLP.dlp_status',
    getStatus: (d) => {
      const s = String(d.dlp_status ?? 'Unknown');
      const enforcer = d.enforcer_status ? `Enforcer: ${d.enforcer_status}` : '';
      return { active: !s.toLowerCase().includes('disabled'), status: s, details: enforcer };
    },
  },
];

export function FeaturesPanel({ stateData, loading }: Props) {
  if (loading) {
    return (
      <div style={{ display: 'flex', justifyContent: 'center', padding: 48 }}>
        <Spin />
      </div>
    );
  }

  return (
    <div>
      <div style={{ fontSize: 13, fontWeight: 600, color: 'var(--text)', marginBottom: 12 }}>
        Modules
      </div>
      <div style={{ display: 'flex', gap: 12, flexWrap: 'wrap' }}>
        {FEATURES.map((feat) => {
          const entry = stateData?.[feat.stateKey];
          const { active, status, details } = entry
            ? feat.getStatus(entry.data)
            : { active: false, status: 'No Data', details: undefined };

          return (
            <Card
              key={feat.label}
              size="small"
              style={{
                flex: '1 1 180px',
                maxWidth: 240,
                background: 'var(--surface)',
                borderColor: 'var(--border)',
              }}
              styles={{ body: { padding: '12px 16px' } }}
            >
              <div style={{ display: 'flex', alignItems: 'center', gap: 8, marginBottom: 4 }}>
                <Badge status={active ? 'success' : 'error'} />
                <span style={{ fontSize: 12, fontWeight: 600, color: 'var(--text)' }}>{feat.label}</span>
              </div>
              <div style={{ fontSize: 12, color: 'var(--text2)', fontFamily: '"JetBrains Mono", monospace' }}>
                {status}
              </div>
              {details && (
                <div style={{ fontSize: 11, color: 'var(--text3)', fontFamily: '"JetBrains Mono", monospace', marginTop: 2 }}>
                  {details}
                </div>
              )}
            </Card>
          );
        })}
      </div>
    </div>
  );
}
