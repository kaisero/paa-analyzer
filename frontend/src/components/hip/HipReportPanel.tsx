import { useState } from 'react';
import { Spin } from 'antd';
import { useHipRaw } from '../../api/hooks';
import type { HipData } from '../../api/types';
import { CategoryGrid } from './CategoryGrid';
import { CycleHeader } from './CycleHeader';
import type { HipViewMode } from './CycleHeader';
import { RawBlock } from './RawBlock';

interface Props {
  hip: HipData;
  sessionId: string | undefined;
}

export function HipReportPanel({ hip, sessionId }: Props) {
  // Cycles arrive newest first (Decision 7): open on the latest.
  const [selectedIndex, setSelectedIndex] = useState(hip.cycles[0].index);
  const [viewMode, setViewMode] = useState<HipViewMode>('Grid');

  const cycle = hip.cycles.find((c) => c.index === selectedIndex) ?? hip.cycles[0];
  // Only XML mode needs the raw documents; JSON mode renders the structured
  // model the frontend actually consumes, for debugging that model.
  const wantsRaw = viewMode === 'XML';
  const { data: rawData, isLoading: rawLoading } = useHipRaw(
    sessionId,
    String(cycle.index),
    wantsRaw,
  );
  const raw = rawData?.data;

  return (
    <div>
      <CycleHeader
        cycles={hip.cycles}
        selectedIndex={cycle.index}
        onSelect={setSelectedIndex}
        viewMode={viewMode}
        onViewMode={setViewMode}
      />

      {viewMode === 'Grid' && <CategoryGrid cycle={cycle} />}

      {wantsRaw && rawLoading && (
        <div style={{ display: 'flex', justifyContent: 'center', padding: 48 }}>
          <Spin />
        </div>
      )}

      {viewMode === 'XML' && !rawLoading && (
        <div style={{ display: 'flex', flexDirection: 'column', gap: 16 }}>
          {/* Two separate documents: the report is logged by PACompliance, the
              patches by PAComplianceMp seconds later (Decision 3). */}
          <RawBlock
            label="hip-report — PACompliance"
            text={raw?.raw_xml}
            emptyNote="No hip-report document was captured for this cycle."
          />
          <RawBlock
            label="missing-patches — PAComplianceMp"
            text={raw?.raw_patches_xml}
            emptyNote="No missing-patches document was captured for this cycle."
          />
        </div>
      )}

      {viewMode === 'JSON' && (
        <RawBlock
          label={`cycle ${cycle.index} — parsed model`}
          text={JSON.stringify(cycle, null, 2)}
          emptyNote="No cycle data."
        />
      )}
    </div>
  );
}
