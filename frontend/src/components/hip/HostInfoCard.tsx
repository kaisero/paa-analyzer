import { useState } from 'react';
import { Button } from 'antd';
import type { HipHostInfo } from '../../api/types';
import { HipCard } from './HipCard';

// The host-id field carries different things per platform; the parser already
// resolved which (Decision 10), so the UI only has to label it.
const HOST_ID_LABEL: Record<HipHostInfo['host_id_kind'], string> = {
  'mac-address': 'MAC address',
  'machine-guid': 'machine GUID',
  unknown: 'host ID',
};

function Field({ label, value }: { label: string; value: string }) {
  return (
    <>
      <div style={{ color: 'var(--text-dim)', fontSize: 11 }}>{label}</div>
      <div
        style={{
          color: 'var(--text)',
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
  hostInfo: HipHostInfo;
  /** HIP report schema version, shown as provenance in the card header. */
  reportVersion?: string | null;
  /** Full-width card (no custom checks beside it): pair up the fields. */
  wide?: boolean;
}

export function HostInfoCard({ hostInfo, reportVersion, wide = false }: Props) {
  const [showInterfaces, setShowInterfaces] = useState(false);
  const interfaces = hostInfo.interfaces ?? [];

  const fields: Array<[string, string | null]> = [
    ['os', hostInfo.os],
    ['host name', hostInfo.host_name],
    ['domain', hostInfo.domain],
    [HOST_ID_LABEL[hostInfo.host_id_kind] ?? 'host ID', hostInfo.host_id],
    ['client version', hostInfo.client_version],
  ];

  return (
    <HipCard
      title="host info"
      extra={
        reportVersion ? (
          <span style={{ fontFamily: 'var(--mono)', fontSize: 10, color: 'var(--text-dim)' }}>
            report v{reportVersion}
          </span>
        ) : undefined
      }
    >
      <div
        style={{
          display: 'grid',
          gridTemplateColumns: wide
            ? 'minmax(0, auto) minmax(0, 1fr) minmax(0, auto) minmax(0, 1fr)'
            : 'minmax(0, auto) minmax(0, 1fr)',
          columnGap: 12,
          rowGap: 3,
        }}
      >
        {fields
          .filter(([, value]) => value != null && value !== '')
          .map(([label, value]) => (
            <Field key={label} label={label} value={value as string} />
          ))}
      </div>

      {interfaces.length > 0 && (
        <div style={{ marginTop: 6 }}>
          <Button
            type="link"
            size="small"
            style={{ padding: 0, height: 'auto', fontSize: 11 }}
            onClick={() => setShowInterfaces((v) => !v)}
          >
            {showInterfaces ? 'hide' : 'show'} {interfaces.length} interface
            {interfaces.length === 1 ? '' : 's'}
          </Button>
          {showInterfaces && (
            <div
              style={{
                marginTop: 6,
                maxHeight: 260,
                overflowY: 'auto',
                border: '1px solid var(--border-soft)',
              }}
            >
              {interfaces.map((iface, i) => {
                const addresses = [...iface.ipv4, ...iface.ipv6].filter(Boolean).join(' · ');
                return (
                  <div
                    key={`${iface.name ?? 'iface'}-${i}`}
                    style={{
                      padding: '4px 8px',
                      borderTop: i > 0 ? '1px solid var(--border-soft)' : undefined,
                      fontFamily: 'var(--mono)',
                      fontSize: 11,
                    }}
                  >
                    <div style={{ display: 'flex', gap: 8, justifyContent: 'space-between' }}>
                      <span style={{ color: 'var(--text)' }}>{iface.name ?? '—'}</span>
                      <span style={{ color: 'var(--text-dim)' }}>{iface.mac ?? ''}</span>
                    </div>
                    {addresses && (
                      <div style={{ color: 'var(--text-sec)', wordBreak: 'break-all' }}>
                        {addresses}
                      </div>
                    )}
                  </div>
                );
              })}
            </div>
          )}
        </div>
      )}
    </HipCard>
  );
}
