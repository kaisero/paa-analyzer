import { Segmented } from 'antd';

export type HipViewMode = 'Grid' | 'XML' | 'JSON';

interface Props {
  modes: HipViewMode[];
  value: HipViewMode;
  onChange: (mode: HipViewMode) => void;
}

/**
 * View mode is a property of a module, not of the page: the hip-report XML
 * belongs to the checklist and the missing-patches XML to the patches table,
 * because they are separate documents logged by different processes.
 */
export function ModuleToggle({ modes, value, onChange }: Props) {
  return (
    <Segmented
      size="small"
      options={modes}
      value={value}
      onChange={(v) => onChange(v as HipViewMode)}
    />
  );
}
