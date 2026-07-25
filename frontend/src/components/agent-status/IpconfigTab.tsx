import { Card, Descriptions } from 'antd';
import type { StateEntry } from '../../api/types';
import { RawJsonView } from './RawJsonView';

interface Adapter {
  name: string;
  [key: string]: unknown;
}

interface Props {
  entry: StateEntry | undefined;
  viewMode: 'Table' | 'Raw' | 'JSON';
}

const FIELD_LABELS: Record<string, string> = {
  description: 'Description',
  physical_address: 'MAC Address',
  dhcp_enabled: 'DHCP',
  ipv4_address: 'IPv4 Address',
  ipv6_address: 'IPv6 Address',
  subnet_mask: 'Subnet Mask',
  default_gateway: 'Default Gateway',
  dhcp_server: 'DHCP Server',
  dns_servers: 'DNS Servers',
  connection_specific_dns_suffix: 'DNS Suffix',
  autoconfiguration_enabled: 'Autoconfiguration',
  link_local_ipv6_address: 'Link-Local IPv6',
};

// Fields to display, in order
const DISPLAY_FIELDS = [
  'description', 'physical_address', 'dhcp_enabled',
  'ipv4_address', 'subnet_mask', 'default_gateway',
  'dhcp_server', 'dns_servers', 'connection_specific_dns_suffix',
];

function formatValue(val: unknown): string {
  if (Array.isArray(val)) return val.join(', ');
  return val != null ? String(val) : '';
}

export function IpconfigTab({ entry, viewMode }: Props) {
  if (!entry) {
    return <div style={{ color: 'var(--text-dim)', fontSize: 12, padding: 16 }}>No network configuration available.</div>;
  }

  if (viewMode !== 'Table') {
    return <RawJsonView entry={entry} viewMode={viewMode} />;
  }

  const data = entry.data as { global?: Record<string, unknown>; adapters?: Adapter[] };
  const adapters = data.adapters ?? [];

  return (
    <div style={{ display: 'flex', flexDirection: 'column', gap: 12 }}>
      {/* Global config */}
      {data.global && Object.keys(data.global).length > 0 && (
        <Card
          title="Global Configuration"
          size="small"
          style={{ background: 'var(--surface)', borderColor: 'var(--border)' }}
          styles={{ header: { borderBottom: '1px solid var(--border)', color: 'var(--text)', fontSize: 12 }, body: { padding: '8px 16px' } }}
        >
          <Descriptions column={1} size="small" colon={false}
            labelStyle={{ color: 'var(--text-dim)', width: 160, fontSize: 12 }}
            contentStyle={{ color: 'var(--text)', fontFamily: '"JetBrains Mono", monospace', fontSize: 12 }}
          >
            {Object.entries(data.global).map(([key, val]) => (
              <Descriptions.Item key={key} label={FIELD_LABELS[key] || key.replace(/_/g, ' ')}>
                {formatValue(val)}
              </Descriptions.Item>
            ))}
          </Descriptions>
        </Card>
      )}

      {/* Adapter cards */}
      {adapters.map((adapter, idx) => (
        <Card
          key={idx}
          title={adapter.name}
          size="small"
          style={{ background: 'var(--surface)', borderColor: 'var(--border)' }}
          styles={{ header: { borderBottom: '1px solid var(--border)', color: 'var(--text)', fontSize: 12, fontFamily: '"JetBrains Mono", monospace' }, body: { padding: '8px 16px' } }}
        >
          <Descriptions column={1} size="small" colon={false}
            labelStyle={{ color: 'var(--text-dim)', width: 160, fontSize: 12 }}
            contentStyle={{ color: 'var(--text)', fontFamily: '"JetBrains Mono", monospace', fontSize: 12 }}
          >
            {DISPLAY_FIELDS.map((field) => {
              const val = adapter[field];
              if (val == null || val === '') return null;
              return (
                <Descriptions.Item key={field} label={FIELD_LABELS[field] || field}>
                  {formatValue(val)}
                </Descriptions.Item>
              );
            })}
            {/* Show any extra fields not in DISPLAY_FIELDS */}
            {Object.entries(adapter)
              .filter(([k, v]) => k !== 'name' && !DISPLAY_FIELDS.includes(k) && v != null && v !== '')
              .map(([key, val]) => (
                <Descriptions.Item key={key} label={FIELD_LABELS[key] || key.replace(/_/g, ' ')}>
                  {formatValue(val)}
                </Descriptions.Item>
              ))}
          </Descriptions>
        </Card>
      ))}
    </div>
  );
}
