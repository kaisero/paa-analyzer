import { useNavigate, useLocation } from 'react-router-dom';
import { Layout, Tabs, Typography } from 'antd';
import { APP_NAME, APP_VERSION } from '../../constants';

interface Props {
  sessionId: string;
}

const tabItems = [
  { key: 'dashboard', label: 'Dashboard' },
  { key: 'agent-status', label: 'Agent Status' },
  { key: 'logs', label: 'Log Viewer' },
];

export function TopNav({ sessionId }: Props) {
  const navigate = useNavigate();
  const location = useLocation();

  // Determine active tab from current path
  const path = location.pathname;
  let activeKey = 'logs';
  if (path.endsWith('/dashboard')) activeKey = 'dashboard';
  else if (path.endsWith('/agent-status')) activeKey = 'agent-status';

  const handleTabChange = (key: string) => {
    if (key === 'logs') navigate(`/s/${sessionId}`);
    else navigate(`/s/${sessionId}/${key}`);
  };

  return (
    <Layout.Header
      style={{
        display: 'flex',
        alignItems: 'center',
        gap: 0,
        padding: '0 16px',
        height: 44,
        background: 'var(--surface)',
        borderBottom: '1px solid var(--border)',
        flexShrink: 0,
        lineHeight: '44px',
      }}
    >
      {/* Brand */}
      <div
        onClick={() => navigate('/')}
        style={{
          fontSize: 13,
          fontWeight: 700,
          color: 'var(--text)',
          marginRight: 24,
          cursor: 'pointer',
          letterSpacing: '-0.01em',
          display: 'flex',
          alignItems: 'center',
          gap: 8,
        }}
      >
        <span style={{ color: 'var(--orange)', fontSize: 16 }}>{'\u25C6'}</span>
        {APP_NAME}
        <span style={{ fontSize: 10, fontWeight: 400, color: 'var(--text3)', marginLeft: 4 }}>v{APP_VERSION}</span>
      </div>

      {/* Tabs */}
      <Tabs
        activeKey={activeKey}
        onChange={handleTabChange}
        items={tabItems}
        size="small"
        style={{ marginBottom: 0, flex: 1 }}
        tabBarStyle={{
          margin: 0,
          height: 44,
          borderBottom: 'none',
        }}
      />

      {/* Session info */}
      <Typography.Text
        onClick={() => navigate('/')}
        style={{
          fontSize: 11,
          color: 'var(--text3)',
          cursor: 'pointer',
          padding: '4px 8px',
          borderRadius: 4,
          flexShrink: 0,
        }}
        title="Switch session"
      >
        Session {sessionId}
      </Typography.Text>
    </Layout.Header>
  );
}
