import type { CSSProperties, ReactNode } from 'react';
import type { HipCycle } from '../../api/types';
import { CategoryCard } from './CategoryCard';
import { CustomChecksCard } from './CustomChecksCard';
import { HostInfoCard } from './HostInfoCard';
import { MissingPatchesTable } from './MissingPatchesTable';
import { NotDetectedStrip } from './NotDetectedStrip';

/**
 * Preferred order and span hints for the 4-column grid (Decision 11).
 *
 * The spans are chosen so the known categories tile without holes on both
 * platforms: `2 + 1 + 1` fills one row, `2 + 2` the next. Categories the
 * report carries but this list does not know are appended at span 1.
 */
// eslint-disable-next-line react-refresh/only-export-components
export const CATEGORY_LAYOUT: Array<{ name: string; span: number }> = [
  { name: 'anti-malware', span: 2 },
  { name: 'firewall', span: 1 },
  { name: 'disk-encryption', span: 1 },
  { name: 'disk-backup', span: 2 },
  { name: 'patch-management', span: 2 },
];

const GRID_COLUMNS = 4;

function GridItem({ span, children }: { span: number; children: ReactNode }) {
  const style = {
    '--hip-span': span,
    // Narrow viewports drop to 2 columns; anything wider than half stays full.
    '--hip-span-sm': span === 1 ? 1 : 2,
  } as CSSProperties;
  return <div style={style}>{children}</div>;
}

interface Props {
  cycle: HipCycle;
}

export function CategoryGrid({ cycle }: Props) {
  const report = cycle.report;

  if (!report) {
    return (
      <div style={{ color: 'var(--text-dim)', fontSize: 12, padding: 16 }}>
        This cycle carries no HIP report — the log was most likely truncated by
        rotation before the report was written.
      </div>
    );
  }

  const categories = report.categories ?? [];
  const populated = categories.filter((c) => c.products.length > 0);
  const notDetected = categories.filter((c) => c.products.length === 0);

  const ordered = [
    ...CATEGORY_LAYOUT.flatMap(({ name, span }) => {
      const category = populated.find((c) => c.name === name);
      return category ? [{ category, span }] : [];
    }),
    // Anything the report carried that the layout config does not name.
    ...populated
      .filter((c) => !CATEGORY_LAYOUT.some((l) => l.name === c.name))
      .map((category) => ({ category, span: 1 })),
  ];

  return (
    <div style={{ display: 'flex', flexDirection: 'column', gap: 12 }}>
      <div className="hip-grid">
        {report.host_info && (
          <GridItem span={report.custom_checks ? 2 : GRID_COLUMNS}>
            <HostInfoCard
              hostInfo={report.host_info}
              reportVersion={report.version}
              wide={!report.custom_checks}
            />
          </GridItem>
        )}
        {report.custom_checks && (
          <GridItem span={2}>
            <CustomChecksCard customChecks={report.custom_checks} />
          </GridItem>
        )}
        {ordered.map(({ category, span }, i) => (
          <GridItem key={category.name ?? `category-${i}`} span={span}>
            <CategoryCard
              category={category}
              timingS={category.name ? cycle.category_timings[category.name] : undefined}
            />
          </GridItem>
        ))}
        {ordered
          .filter(({ category }) => category.missing_patches.length > 0)
          .map(({ category }, i) => (
            <GridItem key={`${category.name ?? i}-patches`} span={GRID_COLUMNS}>
              <MissingPatchesTable
                patches={category.missing_patches}
                source={category.patches_source}
              />
            </GridItem>
          ))}
      </div>
      <NotDetectedStrip categories={notDetected} />
    </div>
  );
}
