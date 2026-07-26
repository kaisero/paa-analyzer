import type { ReactNode } from 'react';
import { Card } from 'antd';

interface Props {
  /** Card label — rendered uppercase in mono, like a schematic block. */
  title: string;
  /** Optional node pinned to the right of the header (status, counts). */
  extra?: ReactNode;
  /** Body padding; card bodies that hold their own rows pass 0. */
  bodyPadding?: string | number;
  children: ReactNode;
}

/** Shared chrome for every block in the HIP grid. */
export function HipCard({ title, extra, bodyPadding = '8px 12px', children }: Props) {
  return (
    <Card
      size="small"
      title={title}
      extra={extra}
      style={{ background: 'var(--surface)', borderColor: 'var(--border)' }}
      styles={{
        header: {
          borderBottom: '1px solid var(--border)',
          color: 'var(--text)',
          fontFamily: 'var(--mono)',
          fontSize: 11,
          fontWeight: 600,
          letterSpacing: '0.08em',
          textTransform: 'uppercase',
          minHeight: 34,
          padding: '0 12px',
        },
        body: { padding: bodyPadding },
      }}
    >
      {children}
    </Card>
  );
}
