import { Card, Descriptions, Tag, Spin, Tooltip } from 'antd';
import type { StateBatchResponse } from '../../api/types';

interface Props {
  stateData: StateBatchResponse | undefined;
  loading: boolean;
}

// eslint-disable-next-line react-refresh/only-export-components
export function getField(data: StateBatchResponse | undefined, key: string, field: string): string {
  const entry = data?.[key];
  if (!entry) return 'N/A';
  const val = entry.data[field];
  return val != null ? String(val) : 'N/A';
}

/** Try macOS key first, fall back to Windows key. */
function getFieldMulti(data: StateBatchResponse | undefined, attempts: Array<[string, string]>): string {
  for (const [key, field] of attempts) {
    const val = getField(data, key, field);
    if (val !== 'N/A') return val;
  }
  return 'N/A';
}

function StateTag({ value, greenWhen }: { value: string; greenWhen: string[] }) {
  const isGreen = greenWhen.some((g) => value.toLowerCase().includes(g.toLowerCase()));
  return (
    <Tag color={isGreen ? 'green' : 'red'} style={{ margin: 0 }}>
      {value}
    </Tag>
  );
}

export function OverviewCards({ stateData, loading }: Props) {
  if (loading) {
    return (
      <div style={{ display: 'flex', justifyContent: 'center', padding: 48 }}>
        <Spin />
      </div>
    );
  }

  // OS: try macOS sw_vers, fall back to Windows systeminfo
  const os = getFieldMulti(stateData, [
    ['Agent.Core.sw_vers', 'productname'],
  ]) !== 'N/A'
    ? [getField(stateData, 'Agent.Core.sw_vers', 'productname'), getField(stateData, 'Agent.Core.sw_vers', 'productversion')].filter((v) => v !== 'N/A').join(' ')
    : getFieldMulti(stateData, [['System.Core.systeminfo', 'os_name']]);

  // Architecture: macOS uname or Windows systeminfo
  const architecture = getFieldMulti(stateData, [
    ['System.Core.uname', 'architecture'],
    ['System.Core.systeminfo', 'system_type'],
  ]);

  // Kernel: macOS Darwin or Windows OS version
  const kernel = getFieldMulti(stateData, [
    ['System.Core.uname', 'kernel'],
    ['System.Core.systeminfo', 'os_version'],
  ]);
  const kernelShort = kernel !== 'N/A'
    ? kernel.replace(/Darwin Kernel Version /, '').split(';')[0].trim()
    : 'N/A';

  return (
    <div style={{ display: 'flex', gap: 16, flexWrap: 'wrap' }}>
      <Card
        title="System"
        size="small"
        style={{ flex: 1, minWidth: 340, background: 'var(--surface)', borderColor: 'var(--border)' }}
        styles={{ header: { borderBottom: '1px solid var(--border)', color: 'var(--text)' }, body: { padding: '8px 16px' } }}
      >
        <Descriptions column={1} size="small" colon={false}
          labelStyle={{ color: 'var(--text3)', width: 120, fontSize: 12 }}
          contentStyle={{ color: 'var(--text)', fontFamily: '"JetBrains Mono", monospace', fontSize: 12 }}
        >
          <Descriptions.Item label="OS">{os || 'N/A'}</Descriptions.Item>
          <Descriptions.Item label="Architecture">{architecture}</Descriptions.Item>
          <Descriptions.Item label="Kernel">{kernelShort}</Descriptions.Item>
          <Descriptions.Item label="Hostname">{getField(stateData, 'Agent.Core.status', 'local_hostname')}</Descriptions.Item>
          <Descriptions.Item label="External IP">{getField(stateData, 'System.Networking.external_ip', 'external_ip')}</Descriptions.Item>
          <Descriptions.Item label="Bundle Time">{getField(stateData, 'Agent.Core.status', 'current_time')}</Descriptions.Item>
        </Descriptions>
      </Card>

      <Card
        title="Agent"
        size="small"
        style={{ flex: 1, minWidth: 340, background: 'var(--surface)', borderColor: 'var(--border)' }}
        styles={{ header: { borderBottom: '1px solid var(--border)', color: 'var(--text)' }, body: { padding: '8px 16px' } }}
      >
        <Descriptions column={1} size="small" colon={false}
          labelStyle={{ color: 'var(--text3)', width: 120, fontSize: 12 }}
          contentStyle={{ color: 'var(--text)', fontFamily: '"JetBrains Mono", monospace', fontSize: 12 }}
        >
          <Descriptions.Item label="Version">{getField(stateData, 'Agent.Core.version', 'version')}</Descriptions.Item>
          <Descriptions.Item label="State">
            <StateTag value={getField(stateData, 'Agent.Core.status', 'state')} greenWhen={['Enabled']} />
          </Descriptions.Item>
          <Descriptions.Item label="Mode">{getField(stateData, 'Agent.Core.status', 'mode')}</Descriptions.Item>
          <Descriptions.Item label="EPM Status">
            <Tooltip title={getField(stateData, 'Agent.Core.epm_status', 'epm_address')}>
              <span><StateTag value={getField(stateData, 'Agent.Core.status', 'epm_status')} greenWhen={['Up']} /></span>
            </Tooltip>
          </Descriptions.Item>
          <Descriptions.Item label="Last Config">{getField(stateData, 'Agent.Core.status', 'last_successful_configuration')}</Descriptions.Item>
          <Descriptions.Item label="GlobalProtect">{getField(stateData, 'Agent.Core.status', 'globalprotect_status')}</Descriptions.Item>
          <Descriptions.Item label="Username">{getField(stateData, 'Agent.Core.status', 'username')}</Descriptions.Item>
        </Descriptions>
      </Card>
    </div>
  );
}
