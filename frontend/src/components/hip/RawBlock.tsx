interface Props {
  /** Which document this is — the two XML documents come from different logs. */
  label: string;
  text: string | null | undefined;
  /** Shown instead of the block when the document is absent. */
  emptyNote: string;
}

/**
 * A labelled raw-document block. `RawJsonView` is bound to the `StateEntry`
 * shape (`data` + `raw_text`) and cannot carry the two separate HIP documents,
 * so this mirrors its styling instead.
 */
export function RawBlock({ label, text, emptyNote }: Props) {
  return (
    <div>
      <div
        style={{
          fontFamily: 'var(--mono)',
          fontSize: 11,
          fontWeight: 600,
          letterSpacing: '0.08em',
          textTransform: 'uppercase',
          color: 'var(--text-sec)',
          marginBottom: 6,
        }}
      >
        {label}
      </div>
      {text ? (
        <pre
          style={{
            margin: 0,
            padding: 16,
            whiteSpace: 'pre-wrap',
            wordBreak: 'break-word',
            color: 'var(--text-sec)',
            fontFamily: 'var(--mono)',
            fontSize: 12,
            background: 'var(--bg)',
            border: '1px solid var(--border)',
            maxHeight: 500,
            overflowY: 'auto',
          }}
        >
          {text}
        </pre>
      ) : (
        <div style={{ color: 'var(--text-dim)', fontSize: 12, fontStyle: 'italic' }}>
          {emptyNote}
        </div>
      )}
    </div>
  );
}
