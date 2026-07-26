import type { HipCategory, HipCustomChecks, HipProduct } from '../../api/types';

/**
 * Turn a product's passthrough attributes into a short human phrase.
 *
 * Attributes are a passthrough bag (Decision 4) — the key set differs per
 * category and grows whenever Palo Alto adds a field. Rather than a per-category
 * map, prefer the first yes/no attribute, which is the defining state for every
 * category observed so far, and fall back to the first scalar.
 */
function attrPhrase(attrs: Record<string, unknown> | null | undefined): string | null {
  if (!attrs) return null;
  const entries = Object.entries(attrs);

  const boolEntry = entries.find(
    ([, v]) => typeof v === 'string' && /^(yes|no)$/i.test(v),
  );
  if (boolEntry) {
    const [key, raw] = boolEntry;
    const on = String(raw).toLowerCase() === 'yes';
    const label =
      key.replace(/^is-/, '').replace(/-protection$/, '').replace(/-/g, ' ').trim() || 'status';
    if (label === 'enabled') return on ? 'enabled' : 'disabled';
    return `${label} ${on ? 'on' : 'off'}`;
  }

  const other = entries.find(
    ([k, v]) => v != null && typeof v !== 'object' && k !== 'drives',
  );
  if (other) return `${other[0].replace(/-/g, ' ')} ${String(other[1])}`;
  return null;
}

/** One product's contribution to its category's folded verdict line. */
export function productClause(p: HipProduct): string {
  // An unknown product's value could not be queried, so never state it as fact.
  if (p.status === 'unknown') return `${p.name} unverifiable`;

  if (p.drives && p.drives.length > 0) {
    const total = p.drives.length;
    const good = p.drives.filter((d) => d.enc_state === 'encrypted').length;
    return `${p.name} ${good}/${total} drives encrypted`;
  }

  const phrase = attrPhrase(p.attributes);
  return phrase ? `${p.name} ${phrase}` : `${p.name} ${p.status}`;
}

/** The one-line summary a folded checklist row has to carry on its own. */
export function categoryVerdict(c: HipCategory): string {
  if (c.products.length > 0) return c.products.map(productClause).join('  ·  ');
  return c.status_reason ?? 'No data.';
}

export function customChecksVerdict(cc: HipCustomChecks | null): string {
  if (!cc) return 'No custom checks collected for this platform.';
  const n = cc.entries?.length ?? 0;
  if (n === 0) return `No ${cc.kind} checks configured.`;
  return `${n} ${cc.kind} check${n === 1 ? '' : 's'} configured.`;
}

/**
 * "patch-management" → "Patch Management" — matches the checklist row labels,
 * so the aggregated missing-patches table's Category column (Task 8) reads
 * the same way the checklist does.
 */
export function titleCase(name: string | null): string {
  if (!name) return '—';
  return name.split('-').map((w) => w.charAt(0).toUpperCase() + w.slice(1)).join(' ');
}
