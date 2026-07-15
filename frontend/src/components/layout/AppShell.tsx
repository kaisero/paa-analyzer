import { Outlet, useParams } from 'react-router-dom';
import { Layout } from 'antd';
import { TopNav } from './TopNav';

export function AppShell() {
  const { sessionId } = useParams<{ sessionId: string }>();

  return (
    <Layout style={{ height: '100vh', overflow: 'hidden' }}>
      {sessionId && <TopNav sessionId={sessionId} />}
      <Layout.Content style={{ flex: 1, overflow: 'hidden' }}>
        <Outlet />
      </Layout.Content>
    </Layout>
  );
}
