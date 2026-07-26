import { Tabs, Spin } from 'antd';
import { useParams } from 'react-router-dom';
import { useStateKeys, useStateBatch } from '../../api/hooks';
import type { StateEntry } from '../../api/types';
import type { ViewMode } from '../common/ViewToggle';
import { SystemExtensionsTab } from './SystemExtensionsTab';
import { RoutingTableTab } from './RoutingTableTab';
import { LaunchctlTab } from './LaunchctlTab';
import { InstalledAppsTab } from './InstalledAppsTab';
import { InstalledDriversTab } from './InstalledDriversTab';
import { FirewallRulesTab } from './FirewallRulesTab';
import { NetstatTab } from './NetstatTab';
import { IpconfigTab } from './IpconfigTab';

// Ordered list of tabs to show per OS — only keys listed here get a tab.
// Order determines tab order in the UI.
const TAB_CONFIG: Array<{
  key: string;
  label: string;
  view: (props: { entry: StateEntry | undefined; viewMode: ViewMode }) => React.ReactNode;
}> = [
  // macOS
  { key: 'System.Core.system_extension_list', label: 'System Extensions', view: (p) => <SystemExtensionsTab {...p} /> },
  { key: 'System.Core.launchctl_list', label: 'Autostart Programs', view: (p) => <LaunchctlTab {...p} /> },
  // Cross-platform
  { key: 'System.Networking.routing', label: 'Routing Table', view: (p) => <RoutingTableTab {...p} /> },
  { key: 'System.Networking.route', label: 'Routing Table', view: (p) => <RoutingTableTab {...p} /> },
  // Windows — curated order
  { key: 'System.Networking.ipconfig', label: 'Network Config', view: (p) => <IpconfigTab {...p} /> },
  { key: 'System.Security.WindowsFirewallrules', label: 'Firewall Rules', view: (p) => <FirewallRulesTab {...p} /> },
  { key: 'System.Networking.netstat', label: 'Network Connections', view: (p) => <NetstatTab {...p} /> },
  { key: 'System.Core.installed_applications', label: 'Installed Apps', view: (p) => <InstalledAppsTab {...p} /> },
  { key: 'System.Core.installed_drivers', label: 'Installed Drivers', view: (p) => <InstalledDriversTab {...p} /> },
];

interface Props {
  viewMode: ViewMode;
}

export function SystemDetails({ viewMode }: Props) {
  const { sessionId } = useParams<{ sessionId: string }>();
  const { data: keysData, isLoading: keysLoading } = useStateKeys(sessionId);

  // Get available System.* keys from the session
  const availableKeys = new Set(
    (keysData?.data ?? []).filter((k) => k.key.startsWith('System.')).map((k) => k.key),
  );

  // Only fetch and show tabs for keys that exist AND are in TAB_CONFIG
  const activeTabs = TAB_CONFIG.filter((t) => availableKeys.has(t.key));
  const batchKeys = activeTabs.map((t) => t.key);

  const { data, isLoading } = useStateBatch(sessionId, batchKeys);
  const stateData = data?.data;

  if ((keysLoading || isLoading) && !stateData) {
    return (
      <div style={{ display: 'flex', justifyContent: 'center', padding: 48 }}>
        <Spin />
      </div>
    );
  }

  if (activeTabs.length === 0) return null;

  const getEntry = (key: string): StateEntry | undefined =>
    stateData?.[key] as StateEntry | undefined;

  const tabItems = activeTabs.map(({ key, label, view: View }) => ({
    key,
    label,
    children: <View entry={getEntry(key)} viewMode={viewMode} />,
  }));

  return <Tabs type="card" items={tabItems} size="small" />;
}
