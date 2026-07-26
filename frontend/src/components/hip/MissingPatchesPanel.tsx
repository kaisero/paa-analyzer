import { useState } from 'react';
import { Spin } from 'antd';
import { useHipRaw } from '../../api/hooks';
import type { HipCycle, MissingPatch } from '../../api/types';
import { HipCard } from './HipCard';
import { MissingPatchesTable } from './MissingPatchesTable';
import { ModuleToggle } from './ModuleToggle';
import type { HipViewMode } from './ModuleToggle';
import { RawBlock } from './RawBlock';

interface Props {
  cycle: HipCycle;
  sessionId: string | undefined;
}

export function MissingPatchesPanel({ cycle, sessionId }: Props) {
  const [view, setView] = useState<HipViewMode>('Grid');

  // ComplianceChecklist (Task 7) makes the identical call for the same
  // (sessionId, cycle.index) pair — TanStack Query dedupes on queryKey, so
  // this is still one request even when both modules want XML at once.
  const { data: rawData, isLoading: rawLoading } = useHipRaw(
    sessionId,
    String(cycle.index),
    view === 'XML',
  );
  const rawPatchesXml = rawData?.data.raw_patches_xml;

  const categories = cycle.report?.categories ?? [];
  // Build patches and their owning category names in one pass so the two arrays
  // stay index-aligned — MissingPatch carries no HIP category of its own
  // (its `category` field is the patch's own kind, e.g. "update").
  const owned = categories.flatMap((c) =>
    (c.missing_patches ?? []).map((patch) => ({ patch, category: c.name })),
  );
  const patches: MissingPatch[] = owned.map((o) => o.patch);
  const categoryNames = owned.map((o) => o.category);
  const source = categories.find((c) => c.patches_source)?.patches_source ?? null;

  // The panel title stays "Missing Patches" in every view mode, matching
  // ComplianceChecklist (Task 7) — the count is a note beside the toggle
  // instead of baked into the title, so the header doesn't change shape
  // when the view mode changes.
  const countNote = (
    <span style={{ fontFamily: 'var(--sans)', fontWeight: 400, fontSize: 11, color: 'var(--text-dim)' }}>
      {patches.length} patch{patches.length === 1 ? '' : 'es'}
    </span>
  );
  const extra = (
    <div style={{ display: 'flex', gap: 12, alignItems: 'center' }}>
      {countNote}
      <ModuleToggle modes={['Grid', 'XML', 'JSON']} value={view} onChange={setView} />
    </div>
  );

  return (
    <HipCard title="Missing Patches" extra={extra}>
      {view === 'Grid' && (
        patches.length > 0
          ? <MissingPatchesTable patches={patches} source={source} categoryNames={categoryNames} />
          : <div style={{ color: 'var(--text-dim)', fontSize: 12 }}>
              No missing patches were reported for this cycle.
            </div>
      )}
      {view === 'XML' && (
        rawLoading
          ? <div style={{ display: 'flex', justifyContent: 'center', padding: 32 }}><Spin /></div>
          : <RawBlock
              label="missing-patches — PAComplianceMp"
              text={rawPatchesXml ?? undefined}
              emptyNote="No missing-patches document was captured for this cycle."
            />
      )}
      {view === 'JSON' && (
        <RawBlock
          label="missing patches — parsed model"
          text={JSON.stringify(patches, null, 2)}
          emptyNote="No missing patches."
        />
      )}
    </HipCard>
  );
}
