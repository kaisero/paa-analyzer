import { useNavigate, useLocation } from 'react-router-dom';
import { Tabs, Button } from 'antd';
import { useTheme } from '../../contexts/ThemeContext';

interface Props {
  sessionId: string;
}

const tabItems = [
  { key: 'agent-status', label: 'Overview' },
  { key: 'logs', label: 'Log Viewer' },
];

export function TopNav({ sessionId }: Props) {
  const navigate = useNavigate();
  const location = useLocation();
  const { isDark, toggle } = useTheme();

  // Determine active tab from current path
  const path = location.pathname;
  let activeKey = 'agent-status';
  if (path.endsWith('/logs')) activeKey = 'logs';

  const handleTabChange = (key: string) => {
    navigate(`/s/${sessionId}/${key}`);
  };

  return (
    <header
      style={{
        display: 'flex',
        flexDirection: 'row',
        alignItems: 'stretch',
        height: 52,
        background: 'var(--surface)',
        borderBottom: '1px solid var(--border)',
        flexShrink: 0,
      }}
    >
      {/* Brand */}
      <div
        onClick={() => navigate('/')}
        style={{
          display: 'flex',
          alignItems: 'center',
          gap: 10,
          padding: '0 20px 0 17px',
          borderRight: '1px solid var(--border)',
          cursor: 'pointer',
          width: 'var(--sidebar-width, 260px)',
          flexShrink: 0,
          boxSizing: 'border-box',
        }}
      >
        <div
          style={{
            width: 26,
            height: 26,
            background: 'var(--accent)',
            color: 'var(--surface)',
            display: 'flex',
            alignItems: 'center',
            justifyContent: 'center',
            fontFamily: 'var(--mono)',
            fontWeight: 700,
            fontSize: 11,
          }}
        >
          PA
        </div>
        <div>
          <div style={{ fontSize: 13, fontWeight: 700, letterSpacing: '0.06em' }}>
            PAA <span style={{ color: 'var(--accent)' }}>ANALYZER</span>
          </div>
          <div
            style={{
              fontSize: 9,
              color: 'var(--text-dim)',
              letterSpacing: '0.14em',
              textTransform: 'uppercase',
            }}
          >
            Agent Diagnostics
          </div>
        </div>
      </div>

      {/* Tabs */}
      <Tabs
        activeKey={activeKey}
        onChange={handleTabChange}
        items={tabItems}
        type="line"
        style={{ flex: 1, marginBottom: 0 }}
        tabBarStyle={{ margin: 0, border: 'none', height: 52, background: 'transparent' }}
      />

      {/* Right controls */}
      <div style={{ display: 'flex', alignItems: 'center', gap: 12, paddingRight: 16 }}>
        <span
          onClick={() => navigate('/')}
          title="Switch session"
          style={{
            fontFamily: 'var(--mono)',
            fontSize: 11,
            color: 'var(--text-sec)',
            border: '1px solid var(--border)',
            background: 'var(--elevated)',
            padding: '4px 10px',
            cursor: 'pointer',
          }}
        >
          SESSION: <b style={{ color: 'var(--text)' }}>{sessionId}</b>
        </span>
        <Button size="small" onClick={toggle}>
          {isDark ? 'Light Mode' : 'Dark Mode'}
        </Button>
      </div>
    </header>
  );
}
