import { Segmented } from 'antd';

export type ViewMode = 'View' | 'Raw' | 'JSON';

interface Props {
  modes: ViewMode[];
  value: ViewMode;
  onChange: (mode: ViewMode) => void;
}

/**
 * The view-mode control. `View` is the structured rendering — a table, a
 * key-value list or a checklist depending on the panel — and `Raw` is the
 * original document the parser read.
 */
export function ViewToggle({ modes, value, onChange }: Props) {
  return (
    <Segmented
      size="small"
      options={modes}
      value={value}
      onChange={(v) => onChange(v as ViewMode)}
    />
  );
}
