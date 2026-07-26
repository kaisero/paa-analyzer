import { useParams } from 'react-router-dom';
import { Spin, Empty } from 'antd';
import { useHip } from '../api/hooks';
import { HipReportPanel } from '../components/hip/HipReportPanel';

export function HipPage() {
  const { sessionId } = useParams<{ sessionId: string }>();
  const { data, isLoading } = useHip(sessionId);
  const hip = data?.data;

  if (isLoading && !hip) {
    return (
      <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'center', height: '100%' }}>
        <Spin size="large" />
      </div>
    );
  }

  // Keyed off cycles, never gateways: a bundle can carry HIP cycles with
  // zero gateway rows (e.g. a hip_status log that only holds an elevation
  // error), so gateways alone is not a reliable "nothing here" signal.
  if (!hip?.cycles?.length) {
    return (
      <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'center', height: '100%' }}>
        <Empty
          image={Empty.PRESENTED_IMAGE_SIMPLE}
          description={
            <div style={{ maxWidth: 420 }}>
              <div style={{ fontWeight: 600, color: 'var(--text)', marginBottom: 6 }}>
                No HIP Data Found
              </div>
              <div style={{ fontSize: 12, lineHeight: 1.6, color: 'var(--text-dim)' }}>
                This bundle contains no <code style={{ fontFamily: 'var(--mono)' }}>PACompliance.log</code> entries,
                so no Host Information Profile cycles could be extracted. HIP
                collection is most likely disabled by gateway policy for this
                endpoint.
              </div>
            </div>
          }
        />
      </div>
    );
  }

  const cycleCount = hip.cycles.length;

  return (
    <div style={{ height: '100%', overflowY: 'auto', padding: 24 }}>
      <div style={{ maxWidth: 1200, margin: '0 auto' }}>
        <div
          style={{
            borderWidth: 1,
            borderStyle: 'solid',
            borderColor: 'var(--border)',
            borderLeftWidth: 3,
            borderLeftColor: 'var(--accent)',
            background: 'var(--surface)',
            padding: '18px 22px',
            marginBottom: 28,
          }}
        >
          <h2 style={{ fontSize: 18, fontWeight: 700, margin: 0 }}>
            Host Information Profile
          </h2>
          <div style={{ marginTop: 8, fontFamily: 'var(--mono)', fontSize: 11, color: 'var(--text-sec)' }}>
            {hip.platform.toUpperCase()} &middot; {cycleCount} cycle{cycleCount === 1 ? '' : 's'} &middot; collection:{' '}
            {hip.collection ?? 'unknown'}
          </div>
        </div>
        <HipReportPanel hip={hip} sessionId={sessionId} />
      </div>
    </div>
  );
}
