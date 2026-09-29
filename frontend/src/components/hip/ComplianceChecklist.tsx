import { useState } from 'react';
import type { CSSProperties } from 'react';
import { Spin } from 'antd';
import { useHipRaw } from '../../api/hooks';
import type { HipCycle, OpswatError } from '../../api/types';
import { Panel } from '../common/Panel';
import { ViewToggle } from '../common/ViewToggle';
import type { ViewMode } from '../common/ViewToggle';
import { CustomChecksCard } from './CustomChecksCard';
import { MissingPatchesTable } from './MissingPatchesTable';
import { ProductRow } from './ProductRow';
import { RawBlock } from './RawBlock';
import { ChecklistRow } from './ChecklistRow';
import { categoryErrors, unattachedErrors } from './hipErrors';
import { categoryVerdict, customChecksVerdict, titleCase } from './hipVerdict';

const CUSTOM_CHECKS_KEY = '__custom-checks__';

const sectionHeading: CSSProperties = {
  fontSize: 10, fontWeight: 700, letterSpacing: '0.1em',
  textTransform: 'uppercase', color: 'var(--text-dim)', marginBottom: 6,
};

function ErrorLine({ error }: { error: OpswatError }) {
  return (
    <div style={{ fontFamily: 'var(--mono)', fontSize: 11, color: 'var(--text-sec)', marginTop: 4 }}>
      <span style={{ color: 'var(--err)', fontWeight: 600 }}>err {error.code}</span>
      {' — '}
      {error.method_name ?? `method ${error.method}`}
      {error.code_meaning ? `: ${error.code_meaning}` : ''}
    </div>
  );
}

interface Props {
  cycle: HipCycle;
  sessionId: string | undefined;
}

export function ComplianceChecklist({ cycle, sessionId }: Props) {
  const [view, setView] = useState<ViewMode>('View');
  const [open, setOpen] = useState<Set<string>>(new Set());

  // Only Raw needs the raw document; JSON renders the structured model.
  // MissingPatchesPanel (Task 8) makes the identical call for the same
  // (sessionId, cycle.index) pair — TanStack Query dedupes on queryKey, so
  // this is still one request even when both modules want Raw at once.
  const { data: rawData, isLoading: rawLoading } = useHipRaw(
    sessionId,
    String(cycle.index),
    view === 'Raw',
  );
  const rawXml = rawData?.data.raw_xml;

  const report = cycle.report;
  const toggleRow = (key: string) =>
    setOpen((prev) => {
      const next = new Set(prev);
      if (next.has(key)) next.delete(key); else next.add(key);
      return next;
    });

  const toggle = <ViewToggle modes={['View', 'Raw', 'JSON']} value={view} onChange={setView} />;

  // The panel title stays "Compliance Checklist" in every view mode — View
  // used to bake the category count into the title ("Categories · 7") while
  // Raw/JSON showed the plain title, so switching modes changed the header's
  // shape. The count is now a separate note next to the toggle instead. It
  // is only meaningful when a report exists, which Raw and JSON must handle
  // too (unlike View, they must not bail out on a missing report — a
  // truncated cycle is exactly when raw XML matters most).
  const countNote = report ? (
    <span style={{ fontFamily: 'var(--sans)', fontWeight: 400, fontSize: 11, color: 'var(--text-dim)' }}>
      {report.categories.length} {report.categories.length === 1 ? 'category' : 'categories'}
    </span>
  ) : null;

  if (view === 'Raw') {
    return (
      <Panel
        title="Compliance Checklist"
        extra={<div style={{ display: 'flex', gap: 12, alignItems: 'center' }}>{countNote}{toggle}</div>}
      >
        {rawLoading ? (
          <div style={{ display: 'flex', justifyContent: 'center', padding: 32 }}><Spin /></div>
        ) : (
          <RawBlock
            label="hip-report — PACompliance"
            text={rawXml ?? undefined}
            emptyNote="No hip-report document was captured for this cycle."
          />
        )}
      </Panel>
    );
  }

  if (view === 'JSON') {
    return (
      <Panel
        title="Compliance Checklist"
        extra={<div style={{ display: 'flex', gap: 12, alignItems: 'center' }}>{countNote}{toggle}</div>}
      >
        <div style={{ display: 'flex', flexDirection: 'column', gap: 16 }}>
          <RawBlock
            label={`cycle ${cycle.index} categories — parsed model`}
            text={report ? JSON.stringify(report.categories, null, 2) : undefined}
            emptyNote="No categories in this report."
          />
          {/* The checklist folds categories AND custom checks into one list,
              so its JSON view has to show both documents, not just
              categories. */}
          <RawBlock
            label={`cycle ${cycle.index} custom_checks — parsed model`}
            text={report ? JSON.stringify(report.custom_checks, null, 2) : undefined}
            emptyNote="No custom checks in this report."
          />
        </div>
      </Panel>
    );
  }

  // View needs a real report from here on — this guard sits after the
  // Raw/JSON returns so a truncated cycle can still be inspected as raw XML.
  if (!report) {
    return (
      <Panel title="Compliance Checklist" extra={<div style={{ display: 'flex', gap: 12, alignItems: 'center' }}>{countNote}{toggle}</div>}>
        <div style={{ color: 'var(--text-dim)', fontSize: 12 }}>
          This cycle carries no HIP report — the log was most likely truncated by
          rotation before the report was written.
        </div>
      </Panel>
    );
  }

  const allKeys = [...report.categories.map((c) => c.name ?? ''), CUSTOM_CHECKS_KEY];
  const controls = (
    <div style={{ display: 'flex', gap: 12, alignItems: 'center' }}>
      {countNote}
      <button type="button" onClick={() => setOpen(new Set(allKeys))} className="hip-ghost-btn">Expand All</button>
      <button type="button" onClick={() => setOpen(new Set())} className="hip-ghost-btn">Collapse All</button>
      {toggle}
    </div>
  );

  const cc = report.custom_checks;
  const ccEntries = cc?.entries?.length ?? 0;

  return (
    <Panel title="Compliance Checklist" extra={controls} bodyPadding="0">
      {report.categories.map((category) => {
        const key = category.name ?? '';
        const errs = categoryErrors(cycle.opswat_errors, category.name);
        const orphans = unattachedErrors(cycle.opswat_errors, category.name);
        const patches = category.missing_patches ?? [];
        const timing = cycle.category_timings?.[key];
        const expandable = category.products.length > 0 || patches.length > 0 || orphans.length > 0;

        return (
          <ChecklistRow
            key={key}
            status={category.status}
            name={titleCase(category.name)}
            verdict={categoryVerdict(category)}
            recede={category.status === 'not-detected'}
            expandable={expandable}
            open={open.has(key)}
            onToggle={() => toggleRow(key)}
            stats={
              <>
                <span>
                  {category.products.length} product{category.products.length === 1 ? '' : 's'}
                </span>
                <span style={errs.length ? { color: 'var(--err)' } : undefined}>
                  {errs.length} error{errs.length === 1 ? '' : 's'}
                </span>
                {patches.length > 0 && (
                  <span>{patches.length} missing patch{patches.length === 1 ? '' : 'es'}</span>
                )}
                <span>{timing != null ? `${timing}s` : '—'}</span>
              </>
            }
          >
            {category.products.map((p, i) => (
              <ProductRow key={p.name} product={p} divider={i > 0} />
            ))}
            {orphans.length > 0 && (
              <div style={{ marginTop: 12 }}>
                <div style={sectionHeading}>Other OPSWAT errors ({orphans.length})</div>
                {/* These carry no signature, so they attach to no product. */}
                {orphans.map((e, i) => <ErrorLine key={i} error={e} />)}
              </div>
            )}
            {patches.length > 0 && (
              <div style={{ marginTop: 12 }}>
                {/* MissingPatchesTable lost its own Panel title (Task 8), so
                    the in-row heading the prototype renders has to live here. */}
                <div style={sectionHeading}>Missing Patches ({patches.length})</div>
                <MissingPatchesTable patches={patches} source={category.patches_source} />
              </div>
            )}
          </ChecklistRow>
        );
      })}

      <ChecklistRow
        status="not-detected"
        name="Custom Checks"
        verdict={customChecksVerdict(cc)}
        recede={ccEntries === 0}
        expandable={ccEntries > 0}
        open={open.has(CUSTOM_CHECKS_KEY)}
        onToggle={() => toggleRow(CUSTOM_CHECKS_KEY)}
        stats={<span>{ccEntries} {ccEntries === 1 ? 'entry' : 'entries'}</span>}
      >
        {/* cc is HipCustomChecks | null; CustomChecksCard's prop is not
            nullable, so this must be guarded rather than passed through.
            (When cc is null, ccEntries is 0, so expandable is false and
            ChecklistRow never renders children anyway — this guard just
            keeps the expression itself well-typed.) */}
        {cc && <CustomChecksCard customChecks={cc} />}
      </ChecklistRow>
    </Panel>
  );
}
