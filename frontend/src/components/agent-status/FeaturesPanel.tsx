import { Table } from 'antd';
import type { TableColumnsType } from 'antd';
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

interface ModuleRow {
  key: string;
  label: string;
  active: boolean;
  status: string;
  details: string | undefined;
}

const columns: TableColumnsType<ModuleRow> = [
  {
    title: 'Module',
    dataIndex: 'label',
    key: 'label',
    width: 200,
    render: (v: string) => <strong style={{ fontSize: 12 }}>{v}</strong>,
  },
  {
    title: 'Status',
    dataIndex: 'status',
    key: 'status',
    width: 160,
    render: (v: string, r: ModuleRow) => (
      <span
        style={{
          display: 'inline-flex',
          alignItems: 'center',
          gap: 6,
          fontFamily: 'var(--mono)',
          fontSize: 11,
          fontWeight: 600,
        }}
      >
        <span
          style={{
            width: 8,
            height: 8,
            borderRadius: '50%',
            flexShrink: 0,
            background: r.active ? 'var(--ok)' : 'var(--err)',
            boxShadow: r.active ? '0 0 5px var(--ok)' : '0 0 5px var(--err)',
          }}
        />
        <span style={{ color: r.active ? 'var(--ok)' : 'var(--err)' }}>{v}</span>
      </span>
    ),
  },
  {
    title: 'Details',
    dataIndex: 'details',
    key: 'details',
    render: (v: string | undefined) => (
      <span style={{ fontFamily: 'var(--mono)', fontSize: 11, color: 'var(--text-sec)' }}>
        {v || '—'}
      </span>
    ),
  },
];

export function FeaturesPanel({ stateData, loading }: Props) {
  const rows: ModuleRow[] = FEATURES.map((feat) => {
    const entry = stateData?.[feat.stateKey];
    const { active, status, details } = entry
      ? feat.getStatus(entry.data)
      : { active: false, status: 'No Data', details: undefined };
    return { key: feat.label, label: feat.label, active, status, details };
  });

  return (
    <Table<ModuleRow>
      dataSource={rows}
      columns={columns}
      rowKey="key"
      size="small"
      bordered
      pagination={false}
      loading={loading}
    />
  );
}
