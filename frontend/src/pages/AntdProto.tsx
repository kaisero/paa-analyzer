import { useState } from 'react';
import {
  ConfigProvider,
  theme as antdTheme,
  Layout,
  Menu,
  Table,
  Tag,
  Input,
  Radio,
  DatePicker,
  Button,
  Card,
  Descriptions,
  Tabs,
} from 'antd';
import type { MenuProps, TableColumnsType, TabsProps, ThemeConfig } from 'antd';

// ─── Accent ───────────────────────────────────────────────────────────────────

const ACCENT = '#FA582D';

// ─── Theme configs ────────────────────────────────────────────────────────────

const darkTokens: ThemeConfig = {
  algorithm: antdTheme.darkAlgorithm,
  token: {
    colorPrimary: ACCENT,
    colorBgBase: '#0C0F14',
    colorBgContainer: '#131920',
    colorBgElevated: '#1C2535',
    colorBorder: '#283040',
    colorBorderSecondary: '#1E2632',
    colorText: '#E8EEF4',
    colorTextSecondary: '#8FA4BC',
    colorTextTertiary: '#5C6E84',
    colorTextQuaternary: '#5C6E84',
    colorError: '#F0564A',
    colorWarning: '#E8A33D',
    colorSuccess: '#3DBE7B',
    colorInfo: '#4D9FDC',
    borderRadius: 0,
    borderRadiusLG: 0,
    borderRadiusSM: 0,
    borderRadiusXS: 0,
    fontFamily: "'Inter', -apple-system, 'Segoe UI', sans-serif",
    fontFamilyCode: "'JetBrains Mono', 'SF Mono', Consolas, monospace",
    fontSize: 13,
    fontSizeSM: 11,
  },
  components: {
    Layout: {
      headerBg: '#131920',
      bodyBg: '#0C0F14',
      siderBg: '#131920',
    },
    Menu: {
      darkItemBg: '#131920',
      darkSubMenuItemBg: '#131920',
      darkItemSelectedBg: 'rgba(250,88,45,0.12)',
      darkItemSelectedColor: '#E8EEF4',
      darkItemHoverBg: 'rgba(250,88,45,0.06)',
      darkItemHoverColor: '#E8EEF4',
      itemHeight: 30,
      itemMarginBlock: 0,
      itemMarginInline: 0,
      itemPaddingInline: 12,
      groupTitleFontSize: 10,
      groupTitleColor: '#5C6E84',
      activeBarBorderWidth: 3,
    },
    Table: {
      headerBg: '#1C2535',
      rowHoverBg: 'rgba(250,88,45,0.06)',
      borderColor: '#1E2632',
      headerColor: '#8FA4BC',
      headerSortActiveBg: '#1C2535',
      headerSortHoverBg: '#1C2535',
      fontSize: 12,
    },
    Tabs: {
      inkBarColor: ACCENT,
      itemActiveColor: '#E8EEF4',
      itemHoverColor: '#E8EEF4',
      itemSelectedColor: '#E8EEF4',
      titleFontSize: 12,
      horizontalItemPadding: '14px 18px',
    },
    Input: {
      activeBorderColor: 'rgba(250,88,45,0.6)',
      hoverBorderColor: 'rgba(250,88,45,0.4)',
      activeShadow: '0 0 0 2px rgba(250,88,45,0.2)',
      fontFamily: "'JetBrains Mono', monospace",
      fontSize: 12,
    },
    Button: {
      fontWeight: 600,
      fontSize: 11,
    },
    Tag: {
      fontSizeSM: 10,
    },
    Card: {
      headerBg: '#1C2535',
    },
  },
};

const lightTokens: ThemeConfig = {
  algorithm: antdTheme.defaultAlgorithm,
  token: {
    colorPrimary: ACCENT,
    colorBgBase: '#F0F4F8',
    colorBgContainer: '#FFFFFF',
    colorBgElevated: '#E8EEF4',
    colorBorder: '#CBD5E1',
    colorBorderSecondary: '#DAE2EC',
    colorText: '#0F172A',
    colorTextSecondary: '#526071',
    colorTextTertiary: '#7C8A9C',
    colorError: '#C4372C',
    colorWarning: '#A66E12',
    colorSuccess: '#1F8A55',
    colorInfo: '#1D6FAE',
    borderRadius: 0,
    borderRadiusLG: 0,
    borderRadiusSM: 0,
    borderRadiusXS: 0,
    fontFamily: "'Inter', -apple-system, 'Segoe UI', sans-serif",
    fontFamilyCode: "'JetBrains Mono', 'SF Mono', Consolas, monospace",
    fontSize: 13,
    fontSizeSM: 11,
  },
  components: {
    Layout: { headerBg: '#FFFFFF', bodyBg: '#F0F4F8', siderBg: '#FFFFFF' },
    Menu: {
      itemBg: '#FFFFFF',
      subMenuItemBg: '#FFFFFF',
      itemSelectedBg: 'rgba(250,88,45,0.08)',
      itemSelectedColor: '#0F172A',
      itemHoverBg: 'rgba(250,88,45,0.05)',
      itemHeight: 30,
      itemMarginBlock: 0,
      itemMarginInline: 0,
      itemPaddingInline: 12,
      groupTitleFontSize: 10,
      activeBarBorderWidth: 3,
    },
    Table: {
      headerBg: '#E8EEF4',
      rowHoverBg: 'rgba(250,88,45,0.05)',
      borderColor: '#DAE2EC',
      headerColor: '#526071',
      fontSize: 12,
    },
    Tabs: {
      inkBarColor: ACCENT,
      itemActiveColor: '#0F172A',
      itemHoverColor: '#0F172A',
      itemSelectedColor: '#0F172A',
      titleFontSize: 12,
      horizontalItemPadding: '14px 18px',
    },
    Input: {
      activeBorderColor: 'rgba(250,88,45,0.6)',
      hoverBorderColor: 'rgba(250,88,45,0.4)',
      fontFamily: "'JetBrains Mono', monospace",
      fontSize: 12,
    },
    Button: { fontWeight: 600, fontSize: 11 },
    Card: { headerBg: '#E8EEF4' },
    Tag: { fontSizeSM: 10 },
  },
};

// ─── Static CSS overrides ─────────────────────────────────────────────────────

const CSS_OVERRIDES = `
  .proto-shell .ant-menu-item-selected::after { display: none !important; }
  .proto-shell .ant-menu-inline .ant-menu-item-selected { border-left: 3px solid ${ACCENT} !important; }
  .proto-shell .ant-table-bordered .ant-table-cell { border-inline-end: 1px solid #1E2632 !important; }
  .proto-shell .ant-tag { border-radius: 0 !important; font-weight: 600; letter-spacing: 0.06em; text-transform: uppercase; }
  .proto-shell .ant-tabs { display: flex; flex-direction: column; overflow: hidden; }
  .proto-shell .ant-tabs-content-holder { flex: 1; overflow: hidden; }
  .proto-shell .ant-tabs-content { height: 100%; }
  .proto-shell .ant-tabs-tabpane { height: 100%; overflow: hidden; }
  .proto-shell .ant-tabs-nav { margin: 0 !important; flex-shrink: 0; }
  .proto-shell .ant-tabs-extra-content { align-self: stretch; }
  .proto-shell .ant-descriptions-item-label { vertical-align: middle !important; }
  .proto-shell .ant-descriptions-item-content { vertical-align: middle !important; }
  .proto-shell .ant-table-expand-icon-col { width: 0 !important; padding: 0 !important; }
  .proto-shell .ant-table-row-expand-icon-cell { width: 0 !important; padding: 0 !important; display: none !important; }
  .proto-tb-label {
    font-size: 10px; font-weight: 700; letter-spacing: 0.12em;
    text-transform: uppercase; color: #5C6E84; flex-shrink: 0;
  }
  .proto-section-title {
    font-size: 11px; font-weight: 700; letter-spacing: 0.14em; text-transform: uppercase;
    border-left: 3px solid ${ACCENT}; padding-left: 10px; margin: 24px 0 12px;
  }
  .proto-report-header {
    border-width: 1px; border-style: solid; border-left-width: 3px;
    border-left-color: ${ACCENT}; padding: 18px 22px; margin-bottom: 24px;
  }
`;

// ─── Mock data ────────────────────────────────────────────────────────────────

interface LogRow { key: number; ts: string; src: string; level: string; msg: string; }

const LOGS: LogRow[] = [
  { key: 1,  ts: '2026-07-23 14:40:34.382', src: 'Agent.Core.PABrowser',             level: 'debug',   msg: '[media_stream_manager.cc(1532)] MSPL::OnSpeedLimitChange({this=0x415400112300}, {new_limit=28})' },
  { key: 2,  ts: '2026-07-23 14:40:15.000', src: 'Agent.Core.agent',                 level: 'error',   msg: 'Connector: certificate-pin preflight WinHttpSendRequest failed. --> Win32 error: The operation timed out. (win32 code 0X2EE2 12002).' },
  { key: 3,  ts: '2026-07-23 14:40:10.000', src: 'Agent.Core.agent',                 level: 'error',   msg: 'Encountered an exception in main loop: HTTP response timed out.' },
  { key: 4,  ts: '2026-07-23 14:38:44.000', src: 'Agent.Core.PAS',                   level: 'info',    msg: 'IOWorker: connector socket read data available' },
  { key: 5,  ts: '2026-07-23 14:38:30.000', src: 'Agent.Core.PAS',                   level: 'warning', msg: 'Tunnel reconnect attempt 3/5 — gateway unreachable' },
  { key: 6,  ts: '2026-07-23 14:37:22.000', src: 'Agent.Core.PAS',                   level: 'error',   msg: 'SSL handshake failed for gateway gw1.prismaaccess.com: certificate verify failed' },
  { key: 7,  ts: '2026-07-23 14:36:50.000', src: 'Agent.Proxy.Proxy',                level: 'error',   msg: 'HTTP CONNECT tunnel failed: 407 Proxy Authentication Required' },
  { key: 8,  ts: '2026-07-23 14:36:44.000', src: 'Agent.Proxy.Proxy',                level: 'error',   msg: 'Upstream proxy rejected CONNECT to internal.corp.com:443' },
  { key: 9,  ts: '2026-07-23 14:35:59.000', src: 'Agent.Core.agent',                 level: 'error',   msg: 'Connector: certificate-pin preflight WinHttpSendRequest failed. The operation timed out.' },
  { key: 10, ts: '2026-07-23 14:34:12.000', src: 'Agent.ADEM.agent',                 level: 'info',    msg: 'ADEM probe completed: latency=45ms jitter=2ms loss=0%' },
  { key: 11, ts: '2026-07-23 14:33:58.000', src: 'Agent.ADEM.agent',                 level: 'warning', msg: 'ADEM threshold exceeded: latency=245ms (threshold=200ms)' },
  { key: 12, ts: '2026-07-23 14:32:44.000', src: 'System.Networking.NetworkManager', level: 'debug',   msg: 'Device state changed: eth0 from ACTIVATED to DEACTIVATED' },
  { key: 13, ts: '2026-07-23 14:31:16.000', src: 'Agent.ADEM.service',               level: 'info',    msg: 'Service heartbeat OK' },
  { key: 14, ts: '2026-07-23 14:30:00.000', src: 'Agent.Core.PAS',                   level: 'info',    msg: 'Configuration refresh successful — policies loaded' },
  { key: 15, ts: '2026-07-23 14:29:43.000', src: 'Agent.Compliance.PACompliance',    level: 'debug',   msg: 'Host compliance check started' },
  { key: 16, ts: '2026-07-23 14:28:55.000', src: 'Agent.Compliance.PACompliance',    level: 'error',   msg: 'Host compliance failed: antivirus definitions outdated (last update: 2026-07-20)' },
  { key: 17, ts: '2026-07-23 14:28:43.000', src: 'System.Networking.NetworkManager', level: 'debug',   msg: 'wlan0: DHCP lease renewed, IP=192.168.1.105' },
  { key: 18, ts: '2026-07-23 14:27:10.000', src: 'Agent.Core.PAS',                   level: 'warning', msg: 'MTU mismatch detected: tunnel MTU=1400, interface MTU=1500' },
];

interface ModuleRow { key: number; module: string; status: string; statusOk: boolean; detail: string; }

const MODULES: ModuleRow[] = [
  { key: 1, module: 'Tunnel',          status: 'Connected',  statusOk: true,  detail: '—' },
  { key: 2, module: 'Explicit Proxy',  status: 'Configured', statusOk: true,  detail: 'proxy.corp.internal:8080' },
  { key: 3, module: 'ADNS Resolver',   status: 'Enabled',    statusOk: true,  detail: '—' },
  { key: 4, module: 'ADEM',            status: 'Enabled',    statusOk: true,  detail: 'v3.2.1 · Tenant: pa-corp-prod' },
  { key: 5, module: 'Endpoint DLP',    status: 'Disabled',   statusOk: false, detail: '—' },
];

interface RouteRow { key: number; destination: string; gateway: string; iface: string; metric: number; }

const ROUTES: RouteRow[] = [
  { key: 1, destination: '0.0.0.0/0',      gateway: '192.168.1.1', iface: 'en0',   metric: 0 },
  { key: 2, destination: '10.0.0.0/8',     gateway: '10.255.0.1',  iface: 'utun4', metric: 1 },
  { key: 3, destination: '192.168.1.0/24', gateway: 'link#6',      iface: 'en0',   metric: 0 },
];

interface FwRuleRow { key: number; name: string; direction: string; action: string; protocol: string; }

const FW_RULES: FwRuleRow[] = [
  { key: 1, name: 'allow-tunnel-out', direction: 'Outbound', action: 'Allow', protocol: 'UDP/443' },
  { key: 2, name: 'allow-dns',        direction: 'Outbound', action: 'Allow', protocol: 'UDP/53' },
  { key: 3, name: 'block-inbound',    direction: 'Inbound',  action: 'Block', protocol: 'Any' },
];

interface FwdProfileRow { key: number; priority: number; name: string; enabled: boolean; type: string; action: string; hitcount: number; }

const FWD_PROFILE: FwdProfileRow[] = [
  { key: 1, priority: 1, name: 'corp-internal',   enabled: true,  type: 'FQDN',   action: 'Tunnel', hitcount: 12842 },
  { key: 2, priority: 2, name: 'saas-direct',     enabled: true,  type: 'Domain', action: 'Direct', hitcount: 4310 },
  { key: 3, priority: 3, name: 'legacy-exclude',  enabled: false, type: 'CIDR',   action: 'Exclude', hitcount: 0 },
];

// ─── Helpers ──────────────────────────────────────────────────────────────────

function LevelTag({ level }: { level: string }) {
  if (level === 'error')   return <Tag color="error">{level}</Tag>;
  if (level === 'warning') return <Tag color="warning">{level}</Tag>;
  if (level === 'info')    return <Tag style={{ background: 'rgba(77,159,220,0.13)', color: '#4D9FDC', borderColor: 'rgba(77,159,220,0.38)' }}>{level}</Tag>;
  return <Tag style={{ background: 'rgba(143,164,188,0.10)', color: '#8FA4BC', borderColor: 'rgba(143,164,188,0.32)' }}>{level}</Tag>;
}

function srcLabel(name: string, errs = 0, warns = 0) {
  return (
    <span style={{ display: 'flex', alignItems: 'center', fontFamily: "'JetBrains Mono', monospace", fontSize: 11.5 }}>
      {name}
      {errs  > 0 && <Tag color="error"   style={{ fontSize: 9, padding: '0 3px', marginLeft: 4,  lineHeight: '16px' }}>{errs}</Tag>}
      {warns > 0 && <Tag color="warning" style={{ fontSize: 9, padding: '0 3px', marginLeft: 2,  lineHeight: '16px' }}>{warns}</Tag>}
    </span>
  );
}

const MENU_ITEMS: MenuProps['items'] = [
  { key: '__all__', label: <span style={{ fontWeight: 600 }}>All Logs</span> },
  {
    key: 'g-adem', label: 'Agent / ADEM',
    children: [
      { key: 'Agent.ADEM.agent',   label: srcLabel('agent',   349, 5064) },
      { key: 'Agent.ADEM.dembios', label: srcLabel('dembios') },
      { key: 'Agent.ADEM.service', label: srcLabel('service') },
    ],
  },
  {
    key: 'g-compliance', label: 'Agent / Compliance',
    children: [
      { key: 'Agent.Compliance.PACompliance',   label: srcLabel('PACompliance',   8)  },
      { key: 'Agent.Compliance.PAComplianceMp', label: srcLabel('PAComplianceMp', 12) },
    ],
  },
  {
    key: 'g-core', label: 'Agent / Core',
    children: [
      { key: 'Agent.Core.PABrowser',         label: srcLabel('PABrowser',         2,  4)   },
      { key: 'Agent.Core.PAS',               label: srcLabel('PAS',               5058, 514) },
      { key: 'Agent.Core.TunneledPacket',    label: srcLabel('TunneledPacket',    36)  },
      { key: 'Agent.Core.connection_history',label: srcLabel('connection_history', 0, 1)  },
      { key: 'Agent.Core.event',             label: srcLabel('event') },
      { key: 'Agent.Core.pachecker',         label: srcLabel('pachecker') },
      { key: 'Agent.Core.remote-shell',      label: srcLabel('remote-shell',      2)   },
      { key: 'Agent.Core.traffic_log_json',  label: srcLabel('traffic_log_json') },
    ],
  },
  {
    key: 'g-proxy', label: 'Agent / Proxy',
    children: [
      { key: 'Agent.Proxy.Proxy', label: srcLabel('Proxy', 1233) },
    ],
  },
  {
    key: 'g-networking', label: 'System / Networking',
    children: [
      { key: 'System.Networking.NetworkManager', label: srcLabel('NetworkManager') },
    ],
  },
];

// ─── Component ────────────────────────────────────────────────────────────────

export function AntdProto() {
  const [isDark, setIsDark]           = useState(true);
  const [activeLevel, setActiveLevel] = useState('all');
  const [expandedKeys, setExpandedKeys] = useState<Set<number>>(new Set());
  const [searchText, setSearchText]   = useState('');
  const [selectedSource, setSelectedSource] = useState('__all__');

  const surface  = isDark ? '#131920' : '#FFFFFF';
  const bg       = isDark ? '#0C0F14' : '#F0F4F8';
  const border   = isDark ? '#283040' : '#CBD5E1';
  const textSec  = isDark ? '#8FA4BC' : '#526071';
  const textDim  = isDark ? '#5C6E84' : '#7C8A9C';
  const elevated = isDark ? '#1C2535' : '#E8EEF4';

  const filteredLogs = LOGS.filter(row => {
    if (activeLevel !== 'all' && row.level !== activeLevel) return false;
    if (selectedSource !== '__all__' && row.src !== selectedSource) return false;
    if (searchText && !row.msg.toLowerCase().includes(searchText.toLowerCase())) return false;
    return true;
  });

  const toggleExpand = (key: number) => {
    setExpandedKeys(prev => {
      const next = new Set(prev);
      if (next.has(key)) next.delete(key); else next.add(key);
      return next;
    });
  };

  // ── Log table columns ──────────────────────────────────────────────────────

  const logColumns: TableColumnsType<LogRow> = [
    {
      title: 'Timestamp', dataIndex: 'ts', key: 'ts', width: 190,
      render: (val: string) => (
        <span style={{ fontFamily: "'JetBrains Mono', monospace", fontSize: 11, color: textSec, whiteSpace: 'nowrap' }}>{val}</span>
      ),
    },
    {
      title: 'Source', dataIndex: 'src', key: 'src', width: 220, ellipsis: true,
      render: (val: string) => (
        <span title={val} style={{ fontFamily: "'JetBrains Mono', monospace", fontSize: 11, color: textSec }}>{val}</span>
      ),
    },
    {
      title: 'Level', dataIndex: 'level', key: 'level', width: 88,
      render: (val: string) => <LevelTag level={val} />,
    },
    {
      title: 'Message', dataIndex: 'msg', key: 'msg',
      render: (val: string, record: LogRow) => {
        const isExpanded = expandedKeys.has(record.key);
        return (
          <span style={{
            fontFamily: "'JetBrains Mono', monospace", fontSize: 11.5,
            display: '-webkit-box',
            WebkitLineClamp: isExpanded ? undefined : 2,
            WebkitBoxOrient: 'vertical' as const,
            overflow: isExpanded ? 'visible' : 'hidden',
            whiteSpace: 'pre-wrap', wordBreak: 'break-word',
          }}>
            {val}
          </span>
        );
      },
    },
  ];

  // ── Module table columns ───────────────────────────────────────────────────

  const moduleColumns: TableColumnsType<ModuleRow> = [
    {
      title: 'Module', dataIndex: 'module', key: 'module', width: 180,
      render: (v: string) => <strong>{v}</strong>,
    },
    {
      title: 'Status', dataIndex: 'status', key: 'status', width: 140,
      render: (v: string, r: ModuleRow) => (
        <Tag color={r.statusOk ? 'success' : 'error'}>{v}</Tag>
      ),
    },
    {
      title: 'Details', dataIndex: 'detail', key: 'detail',
      render: (v: string) => (
        <span style={{ fontFamily: "'JetBrains Mono', monospace", fontSize: 11, color: textSec }}>{v}</span>
      ),
    },
  ];

  // ── Log Viewer pane ────────────────────────────────────────────────────────

  const logViewerPane = (
    <Layout style={{ height: 'calc(100vh - 52px)', overflow: 'hidden' }}>
      <Layout.Sider
        width={264}
        theme={isDark ? 'dark' : 'light'}
        style={{ overflow: 'auto', borderRight: `1px solid ${border}`, flexShrink: 0 }}
      >
        <div style={{ padding: '12px 16px 6px', fontSize: 10, fontWeight: 700, letterSpacing: '0.16em', textTransform: 'uppercase', color: textDim }}>Log Sources</div>
        <Menu
          mode="inline"
          theme={isDark ? 'dark' : 'light'}
          items={MENU_ITEMS}
          selectedKeys={[selectedSource]}
          defaultOpenKeys={['g-adem', 'g-core', 'g-proxy', 'g-compliance', 'g-networking']}
          onClick={({ key }) => setSelectedSource(key)}
          style={{ background: 'transparent', borderInlineEnd: 'none', fontFamily: "'JetBrains Mono', monospace", fontSize: 12 }}
        />
      </Layout.Sider>

      <Layout.Content style={{ display: 'flex', flexDirection: 'column', overflow: 'hidden', background: bg }}>
        {/* Toolbar */}
        <div style={{
          display: 'flex', alignItems: 'center', gap: 18, flexWrap: 'wrap',
          padding: '8px 14px', background: surface, borderBottom: `1px solid ${border}`, flexShrink: 0,
        }}>
          <div style={{ display: 'flex', alignItems: 'center', gap: 8 }}>
            <span className="proto-tb-label">SEARCH:</span>
            <Input.Search
              value={searchText}
              onChange={e => setSearchText(e.target.value)}
              placeholder="Filter messages..."
              allowClear
              size="small"
              style={{ width: 240 }}
            />
          </div>

          <div style={{ display: 'flex', alignItems: 'center', gap: 8 }}>
            <span className="proto-tb-label">LEVEL:</span>
            <Radio.Group
              value={activeLevel}
              onChange={e => setActiveLevel(e.target.value as string)}
              optionType="button"
              buttonStyle="solid"
              size="small"
            >
              {(['all', 'error', 'warning', 'info', 'debug'] as const).map(l => (
                <Radio.Button
                  key={l} value={l}
                  style={{ fontSize: 10, fontWeight: 600, letterSpacing: '0.06em', textTransform: 'uppercase' }}
                >
                  {l === 'all' ? 'All' : l === 'warning' ? 'Warn' : l.charAt(0).toUpperCase() + l.slice(1)}
                </Radio.Button>
              ))}
            </Radio.Group>
          </div>

          <div style={{ display: 'flex', alignItems: 'center', gap: 8 }}>
            <span className="proto-tb-label">TIME RANGE:</span>
            <DatePicker.RangePicker size="small" showTime style={{ minWidth: 320 }} />
            <Button
              size="small"
              onClick={() => { setSearchText(''); setActiveLevel('all'); setSelectedSource('__all__'); }}
            >
              Clear
            </Button>
          </div>
        </div>

        {/* Table */}
        <div style={{ flex: 1, overflow: 'auto' }}>
          <Table<LogRow>
            dataSource={filteredLogs}
            columns={logColumns}
            rowKey="key"
            pagination={false}
            size="small"
            bordered
            expandable={{
              expandedRowKeys: [...expandedKeys],
              expandIcon: () => null,
              expandedRowRender: record => (
                <pre style={{
                  margin: 0, padding: '8px 16px',
                  fontFamily: "'JetBrains Mono', monospace", fontSize: 11,
                  whiteSpace: 'pre-wrap', wordBreak: 'break-word',
                  background: elevated, borderLeft: `3px solid ${ACCENT}`, color: textSec,
                }}>
                  {record.msg}
                </pre>
              ),
            }}
            onRow={record => ({
              onClick: () => toggleExpand(record.key),
              style: { cursor: 'pointer' },
            })}
            locale={{ emptyText: 'No entries match your filters' }}
          />
        </div>

        {/* Status bar */}
        <div style={{
          display: 'flex', alignItems: 'center', gap: 20,
          padding: '6px 14px', background: surface, borderTop: `1px solid ${border}`,
          fontFamily: "'JetBrains Mono', monospace", fontSize: 10.5, color: textDim, flexShrink: 0,
        }}>
          <span>
            Showing <strong style={{ color: textSec }}>{filteredLogs.length}</strong>{' '}
            of <strong style={{ color: textSec }}>145,938</strong> entries
          </span>
          <span style={{ marginLeft: 'auto' }}>6,700 errors · 5,583 warnings</span>
        </div>
      </Layout.Content>
    </Layout>
  );

  // ── Agent Status pane ──────────────────────────────────────────────────────

  const agentStatusPane = (
    <div style={{ height: 'calc(100vh - 52px)', overflowY: 'auto', padding: '24px 32px 48px', background: bg }}>
      <div
        className="proto-report-header"
        style={{ background: surface, borderColor: border }}
      >
        <h2 style={{ fontSize: 19, fontWeight: 700, margin: 0 }}>
          Prisma Access Agent —{' '}
          <span style={{ color: ACCENT }}>Diagnostic Report</span>
        </h2>
        <div style={{ marginTop: 8, fontFamily: "'JetBrains Mono', monospace", fontSize: 11, color: textSec }}>
          SESSION: ed95fed09bc7 &nbsp;|&nbsp; BUNDLE: paa-diag-20260723.zip &nbsp;|&nbsp; CAPTURED: 2026-07-23 14:41 UTC
        </div>
      </div>

      <div className="proto-section-title" style={{ color: textSec }}>SYSTEM OVERVIEW</div>

      <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: 20 }}>
        <Card title="SYSTEM" size="small" bordered>
          <Descriptions
            column={1} size="small" colon={false}
            labelStyle={{ color: textDim, width: 130, fontSize: 10.5, fontWeight: 600, letterSpacing: '0.08em', textTransform: 'uppercase' }}
            contentStyle={{ fontFamily: "'JetBrains Mono', monospace", fontSize: 11.5 }}
          >
            <Descriptions.Item label="OS">macOS Sequoia 15.5</Descriptions.Item>
            <Descriptions.Item label="Architecture">arm64</Descriptions.Item>
            <Descriptions.Item label="Kernel">Darwin 24.6.0</Descriptions.Item>
            <Descriptions.Item label="Hostname">corp-mbp-oliver.local</Descriptions.Item>
            <Descriptions.Item label="External IP">203.0.113.47</Descriptions.Item>
            <Descriptions.Item label="Bundle Time">2026-07-23 14:41 UTC</Descriptions.Item>
          </Descriptions>
        </Card>

        <Card title="AGENT" size="small" bordered>
          <Descriptions
            column={1} size="small" colon={false}
            labelStyle={{ color: textDim, width: 130, fontSize: 10.5, fontWeight: 600, letterSpacing: '0.08em', textTransform: 'uppercase' }}
            contentStyle={{ fontFamily: "'JetBrains Mono', monospace", fontSize: 11.5 }}
          >
            <Descriptions.Item label="Version">6.3.2-c47</Descriptions.Item>
            <Descriptions.Item label="State"><Tag color="success">Enabled</Tag></Descriptions.Item>
            <Descriptions.Item label="Mode">Managed</Descriptions.Item>
            <Descriptions.Item label="EPM Status"><Tag color="success">Up</Tag></Descriptions.Item>
            <Descriptions.Item label="Last Config">2026-07-23 14:30 UTC</Descriptions.Item>
            <Descriptions.Item label="Username">oliver.kaiser@paloaltonetworks.com</Descriptions.Item>
          </Descriptions>
        </Card>
      </div>

      <div className="proto-section-title" style={{ color: textSec }}>MODULES</div>

      <Table<ModuleRow>
        dataSource={MODULES}
        columns={moduleColumns}
        rowKey="key"
        pagination={false}
        size="small"
        bordered
      />

      <div className="proto-section-title" style={{ color: textSec }}>SYSTEM DETAILS</div>

      <Tabs
        type="card"
        size="small"
        items={[
          {
            key: 'routing',
            label: 'Routing Table',
            children: (
              <Table<RouteRow>
                dataSource={ROUTES}
                columns={[
                  { title: 'Destination', dataIndex: 'destination', key: 'destination', render: (v: string) => <span style={{ fontFamily: "'JetBrains Mono', monospace", fontSize: 11 }}>{v}</span> },
                  { title: 'Gateway', dataIndex: 'gateway', key: 'gateway', render: (v: string) => <span style={{ fontFamily: "'JetBrains Mono', monospace", fontSize: 11 }}>{v}</span> },
                  { title: 'Interface', dataIndex: 'iface', key: 'iface', render: (v: string) => <span style={{ fontFamily: "'JetBrains Mono', monospace", fontSize: 11 }}>{v}</span> },
                  { title: 'Metric', dataIndex: 'metric', key: 'metric', width: 90 },
                ]}
                rowKey="key"
                pagination={false}
                size="small"
                bordered
              />
            ),
          },
          {
            key: 'firewall',
            label: 'Firewall Rules',
            children: (
              <Table<FwRuleRow>
                dataSource={FW_RULES}
                columns={[
                  { title: 'Name', dataIndex: 'name', key: 'name', render: (v: string) => <span style={{ fontFamily: "'JetBrains Mono', monospace", fontSize: 11 }}>{v}</span> },
                  { title: 'Direction', dataIndex: 'direction', key: 'direction', width: 120 },
                  { title: 'Action', dataIndex: 'action', key: 'action', width: 100, render: (v: string) => <Tag color={v === 'Allow' ? 'success' : 'error'}>{v}</Tag> },
                  { title: 'Protocol', dataIndex: 'protocol', key: 'protocol', render: (v: string) => <span style={{ fontFamily: "'JetBrains Mono', monospace", fontSize: 11 }}>{v}</span> },
                ]}
                rowKey="key"
                pagination={false}
                size="small"
                bordered
              />
            ),
          },
        ]}
      />

      <div className="proto-section-title" style={{ color: textSec }}>FORWARDING PROFILE</div>

      <Table<FwdProfileRow>
        dataSource={FWD_PROFILE}
        columns={[
          { title: 'Priority', dataIndex: 'priority', key: 'priority', width: 90 },
          { title: 'Name', dataIndex: 'name', key: 'name', render: (v: string) => <span style={{ fontFamily: "'JetBrains Mono', monospace", fontSize: 11 }}>{v}</span> },
          { title: 'Enabled', dataIndex: 'enabled', key: 'enabled', width: 100, render: (v: boolean) => <Tag color={v ? 'success' : 'default'}>{v ? 'Yes' : 'No'}</Tag> },
          { title: 'Type', dataIndex: 'type', key: 'type', width: 110 },
          { title: 'Action', dataIndex: 'action', key: 'action', width: 110 },
          { title: 'Hitcount', dataIndex: 'hitcount', key: 'hitcount', width: 110, render: (v: number) => <span style={{ fontFamily: "'JetBrains Mono', monospace", fontSize: 11 }}>{v.toLocaleString()}</span> },
        ]}
        rowKey="key"
        pagination={false}
        size="small"
        bordered
      />

      <div className="proto-section-title" style={{ color: textSec }}>PACLI TERMINAL</div>

      <div style={{
        background: elevated,
        border: `1px solid ${border}`,
        fontFamily: "'JetBrains Mono', monospace",
        minHeight: 120,
        padding: '12px 16px',
        fontSize: 11.5,
      }}>
        <div>
          <span style={{ color: ACCENT }}>$</span> pacli help
        </div>
        <pre style={{ margin: '8px 0 0', fontFamily: 'inherit', fontSize: 'inherit', color: textSec, whiteSpace: 'pre-wrap' }}>
          Available commands: pacli status, pacli adem-status, pacli tunnel-info
        </pre>
      </div>
    </div>
  );

  // ── Tab items ──────────────────────────────────────────────────────────────

  const tabItems: TabsProps['items'] = [
    { key: 'logs',   label: 'Log Viewer',   children: logViewerPane },
    { key: 'status', label: 'Agent Status', children: agentStatusPane },
  ];

  // ── Brand (left extra content) ─────────────────────────────────────────────

  const brandSlot = (
    <div style={{
      display: 'flex', alignItems: 'center', gap: 10,
      paddingRight: 20, marginRight: 4, borderRight: `1px solid ${border}`,
      height: 52, flexShrink: 0,
    }}>
      <div style={{
        width: 26, height: 26, background: ACCENT,
        color: isDark ? '#0C0F14' : '#FFFFFF',
        display: 'flex', alignItems: 'center', justifyContent: 'center',
        fontFamily: 'monospace', fontWeight: 700, fontSize: 11,
      }}>PA</div>
      <div>
        <div style={{ fontSize: 13, fontWeight: 700, letterSpacing: '0.06em', lineHeight: 1.3 }}>
          PAA <span style={{ color: ACCENT }}>ANALYZER</span>
        </div>
        <div style={{ fontSize: 9, color: textDim, letterSpacing: '0.14em', textTransform: 'uppercase' }}>
          Prisma Access Agent Diagnostics
        </div>
      </div>
    </div>
  );

  // ── Right controls ─────────────────────────────────────────────────────────

  const rightSlot = (
    <div style={{ display: 'flex', alignItems: 'center', gap: 12, paddingLeft: 16, height: 52, flexShrink: 0 }}>
      <span style={{
        fontFamily: "'JetBrains Mono', monospace", fontSize: 11, color: textSec,
        border: `1px solid ${border}`, background: elevated, padding: '4px 10px',
      }}>
        SESSION: <strong style={{ color: isDark ? '#E8EEF4' : '#0F172A' }}>ed95fed09bc7</strong>
      </span>
      <Button size="small" onClick={() => setIsDark(d => !d)}>
        {isDark ? 'Light Mode' : 'Dark Mode'}
      </Button>
    </div>
  );

  // ── Render ─────────────────────────────────────────────────────────────────

  return (
    <ConfigProvider theme={isDark ? darkTokens : lightTokens}>
      <div style={{ borderLeft: `3px solid ${ACCENT}`, height: '100vh', display: 'flex', flexDirection: 'column', overflow: 'hidden' }}>
        <div
          className="proto-shell"
          style={{ height: '100vh', overflow: 'hidden', display: 'flex', flexDirection: 'column', background: bg }}
        >
          <style>{CSS_OVERRIDES}</style>
          <Tabs
            type="line"
            items={tabItems}
            tabBarExtraContent={{ left: brandSlot, right: rightSlot }}
            tabBarStyle={{
              height: 52,
              background: surface,
              borderBottom: `1px solid ${border}`,
              margin: 0,
              padding: 0,
              flexShrink: 0,
            }}
            style={{ flex: 1, overflow: 'hidden' }}
          />
        </div>
      </div>
    </ConfigProvider>
  );
}
