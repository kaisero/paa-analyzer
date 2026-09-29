import { useCallback, useEffect, useState } from 'react';
import { useNavigate } from 'react-router-dom';
import { Upload, Progress, Card, Button, Typography, Tag, Alert } from 'antd';
import { InboxOutlined } from '@ant-design/icons';
import { useUploadWithProgress } from '../../hooks/useUploadWithProgress';
import { APP_NAME } from '../../constants';
import { useSessions } from '../../api/hooks';

const { Dragger } = Upload;

export function UploadPage() {
  const navigate = useNavigate();
  const { status, stage, progress, detail, session, error, upload, reset } = useUploadWithProgress();
  const { data: sessionsResp } = useSessions();
  const sessions = sessionsResp?.data ?? [];
  const [elapsed, setElapsed] = useState(0);

  // Elapsed timer during upload
  useEffect(() => {
    if (status !== 'uploading') return;
    const start = Date.now();
    const timer = setInterval(() => setElapsed(Math.floor((Date.now() - start) / 1000)), 1000);
    return () => clearInterval(timer);
  }, [status]);

  // Auto-navigate on complete
  useEffect(() => {
    if (status === 'complete' && session) {
      const t = setTimeout(() => navigate(`/s/${session.id}`), 500);
      return () => clearTimeout(t);
    }
  }, [status, session, navigate]);

  const handleFile = useCallback((file: File) => {
    if (!file.name.endsWith('.zip')) return;
    upload(file);
  }, [upload]);

  const isUploading = status === 'uploading';
  const isComplete = status === 'complete';
  const isError = status === 'error';
  const isIdle = status === 'idle';

  return (
    <div style={{
      display: 'flex',
      alignItems: 'center',
      justifyContent: 'center',
      height: '100vh',
      background: 'var(--bg)',
    }}>
      <div style={{ width: '100%', maxWidth: 520, padding: '0 24px' }} className="animate-fade-in">

        {/* Branding */}
        <div style={{ textAlign: 'center', marginBottom: 40 }}>
          <div style={{
            fontSize: 28, color: 'var(--accent)', marginBottom: 12,
          }}>
            {'\u25C6'}
          </div>
          <h1 style={{
            fontSize: 24, fontWeight: 700, color: 'var(--text)',
            letterSpacing: '-0.02em', marginBottom: 6,
          }}>
            {APP_NAME}
          </h1>
          <p style={{ fontSize: 13, color: 'var(--text-dim)' }}>
            Prisma Access Agent Diagnostics
          </p>
        </div>

        {/* Upload zone (antd Dragger) */}
        {isIdle && (
          <Dragger
            accept=".zip"
            showUploadList={false}
            beforeUpload={(file) => {
              handleFile(file);
              return false; // prevent default upload
            }}
            style={{
              borderRadius: 0,
              border: '1px solid var(--border)',
              background: 'var(--surface)',
              padding: '48px 32px',
            }}
          >
            <p className="ant-upload-drag-icon">
              <InboxOutlined style={{ color: 'var(--accent)', fontSize: 48 }} />
            </p>
            <p style={{ fontSize: 14, fontWeight: 500, color: 'var(--text-sec)', marginBottom: 6 }}>
              Drop a troubleshooting bundle here
            </p>
            <p style={{ fontSize: 12, color: 'var(--text-dim)' }}>
              or click to browse &middot; .zip up to 500 MB
            </p>
          </Dragger>
        )}

        {/* Progress state */}
        {(isUploading || isComplete) && (
          <div style={{
            borderRadius: 0,
            border: '1px solid var(--border)',
            background: 'var(--surface)',
            padding: '40px 32px',
            textAlign: 'center',
          }} className="animate-fade-in">
            <div style={{
              fontSize: 13, fontWeight: 500, color: 'var(--text)',
              marginBottom: 4,
            }}>
              {isComplete ? 'Parsing complete' : stageLabel(stage)}
            </div>
            <div style={{
              fontSize: 11, color: 'var(--text-dim)',
              fontFamily: "'JetBrains Mono', monospace",
              marginBottom: 20,
              overflow: 'hidden', textOverflow: 'ellipsis', whiteSpace: 'nowrap',
            }}>
              {detail}
            </div>

            <Progress
              percent={progress}
              showInfo={false}
              strokeColor={isComplete ? 'var(--ok)' : 'var(--accent)'}
              trailColor="var(--elevated)"
              style={{ marginBottom: 16 }}
            />

            <div style={{ display: 'flex', justifyContent: 'space-between', fontSize: 11, color: 'var(--text-dim)' }}>
              <span>{progress}%</span>
              <span>{elapsed}s</span>
            </div>
          </div>
        )}

        {/* Error state */}
        {isError && (
          <Alert
            type="error"
            message="Upload failed"
            description={error}
            showIcon
            action={<Button onClick={reset} size="small">Try again</Button>}
            style={{ marginTop: 16 }}
            className="animate-fade-in"
          />
        )}

        {/* Recent sessions */}
        {sessions.length > 0 && isIdle && (
          <div style={{ marginTop: 40 }}>
            <Typography.Text
              type="secondary"
              style={{
                fontSize: 10, fontWeight: 600, textTransform: 'uppercase',
                letterSpacing: '0.08em', display: 'block', marginBottom: 10,
              }}
            >
              Recent sessions
            </Typography.Text>
            {sessions.map((s) => (
              <Card
                key={s.id}
                hoverable
                size="small"
                onClick={() => navigate(`/s/${s.id}`)}
                style={{
                  marginBottom: 6,
                  background: 'var(--surface)',
                  borderColor: 'var(--border)',
                  cursor: 'pointer',
                }}
                styles={{ body: { padding: '10px 14px' } }}
              >
                <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between' }}>
                  <div>
                    <div style={{ fontSize: 13, fontWeight: 500, color: 'var(--text)' }}>{s.filename}</div>
                    <div style={{ fontSize: 11, color: 'var(--text-dim)', marginTop: 2 }}>
                      {s.total_log_sources} sources &middot; {s.total_log_entries.toLocaleString()} entries
                      {s.parse_duration_ms ? ` \u00b7 ${(s.parse_duration_ms / 1000).toFixed(1)}s` : ''}
                    </div>
                  </div>
                  <Tag
                    color={s.parse_status === 'complete' ? 'success' : 'error'}
                    style={{ margin: 0, fontSize: 10 }}
                  >
                    {s.parse_status}
                  </Tag>
                </div>
              </Card>
            ))}
          </div>
        )}
      </div>
    </div>
  );
}

function stageLabel(stage: string): string {
  switch (stage) {
    case 'extracting': return 'Extracting files...';
    case 'parsing': return 'Parsing logs...';
    case 'sorting': return 'Sorting entries...';
    case 'storing': return 'Building session...';
    default: return 'Processing...';
  }
}
