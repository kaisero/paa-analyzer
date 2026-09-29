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
      // height:100% so panels sitting side by side in a grid or flex row match
      // each other — the shorter one stretches rather than leaving a ragged
      // bottom edge. In a column (the full-width HIP panels) the percentage
      // resolves against an indefinite height, i.e. to auto, so it is inert.
      style={{ background: 'var(--surface)', borderColor: 'var(--border)', height: '100%' }}
      styles={{
        // The type treatment belongs on the title, not the header: `header`
        // also wraps the `extra` slot, so putting uppercase and letter-spacing
        // there deformed every control passed into it.
        title: {
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
