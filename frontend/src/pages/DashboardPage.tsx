import { Empty } from 'antd';

export function DashboardPage() {
  return (
    <div style={{
      display: 'flex',
      alignItems: 'center',
      justifyContent: 'center',
      height: '100%',
    }}>
      <Empty
        description={
          <span style={{ color: 'var(--text3)' }}>Dashboard coming soon</span>
        }
        image={Empty.PRESENTED_IMAGE_SIMPLE}
      />
    </div>
  );
}
