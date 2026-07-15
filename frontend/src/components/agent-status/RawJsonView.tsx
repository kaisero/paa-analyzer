import { useMemo } from 'react';
import type { StateEntry } from '../../api/types';

interface Props {
  entry: StateEntry | undefined;
  viewMode: 'Raw' | 'JSON';
}

const preStyle = {
  margin: 0,
  padding: 16,
  whiteSpace: 'pre-wrap' as const,
  color: 'var(--text2)',
  fontFamily: '"JetBrains Mono", monospace',
  fontSize: 12,
  background: 'var(--bg)',
  border: '1px solid var(--border)',
  borderRadius: 8,
  maxHeight: 500,
  overflowY: 'auto' as const,
};

export function RawJsonView({ entry, viewMode }: Props) {
  const jsonStr = useMemo(() => {
    if (!entry || viewMode !== 'JSON') return '';
    try {
      return JSON.stringify(entry.data, null, 2);
    } catch {
      return '// Error serializing data';
    }
  }, [entry, viewMode]);

  if (!entry) {
    return <div style={{ color: 'var(--text3)', fontSize: 12, padding: 16 }}>No data available.</div>;
  }

  if (viewMode === 'Raw') {
    if (entry.raw_text) {
      return <pre style={preStyle}>{entry.raw_text}</pre>;
    }
    return (
      <div style={{ color: 'var(--text3)', fontSize: 11, fontStyle: 'italic', padding: 16 }}>
        Raw text not available — re-upload bundle to enable
      </div>
    );
  }

  return <pre style={preStyle}>{jsonStr}</pre>;
}
