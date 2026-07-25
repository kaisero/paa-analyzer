import { Outlet, useParams } from 'react-router-dom';
import { TopNav } from './TopNav';

export function AppShell() {
  const { sessionId } = useParams<{ sessionId: string }>();

  return (
    <div style={{ height: '100vh', overflow: 'hidden', display: 'flex', flexDirection: 'column' }}>
      {sessionId && <TopNav sessionId={sessionId} />}
      <div style={{ flex: 1, overflow: 'hidden' }}>
        <Outlet />
      </div>
    </div>
  );
}
