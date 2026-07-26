import type { ReactNode } from 'react';
import { Card } from 'antd';

interface Props {
  /** Card label — rendered uppercase, tracked, in the secondary text colour. */
  title: string;
  /** Optional node pinned to the right of the header (a view toggle, counts). */
  extra?: ReactNode;
  /** Body padding; bodies that hold their own full-bleed rows pass 0. */
  bodyPadding?: string | number;
  children: ReactNode;
}

/**
 * The card chrome for every panel in the app.
 *
 * Before this existed the header was styled inline at each call site and had
 * drifted into four different treatments — three of them inside agent-status
 * alone. Route new panels through here rather than restyling a `Card`.
 */
export function Panel({ title, extra, bodyPadding = '8px 16px', children }: Props) {
  return (
    <Card
      size="small"
      title={title}
      extra={extra}
      style={{ background: 'var(--surface)', borderColor: 'var(--border)' }}
      styles={{
        header: {
          color: 'var(--text-sec)',
          fontSize: 11,
          fontWeight: 700,
          letterSpacing: '0.12em',
          textTransform: 'uppercase',
        },
        body: { padding: bodyPadding },
      }}
    >
      {children}
    </Card>
  );
}
