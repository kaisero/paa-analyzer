import { BrowserRouter, Routes, Route, Navigate } from 'react-router-dom';
import { QueryClient, QueryClientProvider } from '@tanstack/react-query';
import { AppShell } from './components/layout/AppShell';
import { UploadPage } from './components/upload/UploadPage';
import { LogViewer } from './components/log-viewer/LogViewer';
import { DashboardPage } from './pages/DashboardPage';
import { AgentStatusPage } from './pages/AgentStatusPage';
import { AntdProto } from './pages/AntdProto';

const queryClient = new QueryClient({
  defaultOptions: {
    queries: { staleTime: 30_000, retry: 1 },
  },
});

export default function App() {
  return (
    <QueryClientProvider client={queryClient}>
      <BrowserRouter>
        <Routes>
          <Route path="/" element={<UploadPage />} />
          <Route path="/s/:sessionId" element={<AppShell />}>
            <Route index element={<LogViewer />} />
            <Route path="dashboard" element={<DashboardPage />} />
            <Route path="agent-status" element={<AgentStatusPage />} />
          </Route>
          <Route path="/proto" element={<AntdProto />} />
          <Route path="*" element={<Navigate to="/" replace />} />
        </Routes>
      </BrowserRouter>
    </QueryClientProvider>
  );
}
