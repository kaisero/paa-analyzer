import { describe, it, expect } from 'vitest';
import hipFixture from '../../test/fixtures/hip.json';
import { categoryErrors, unattachedErrors } from './hipErrors';
import type { HipCategory, OpswatError } from '../../api/types';

const macCycle = hipFixture.macos.cycles[0];
const errors = macCycle.opswat_errors as unknown as OpswatError[];

describe('categoryErrors', () => {
  it('counts errors the flat list carries, not just those attached to products', () => {
    // Regression guard: summing product.errors gives 4, but the cycle has 6 —
    // the two GetMissingPatchesForThisProduct errors carry no signature and so
    // attach to no product.
    // The raw JSON import types `categories` as a union of seven differently
    // shaped literals, so `flatMap`/`reduce` can't resolve overloads directly
    // against it — cast once to the real type, same as `hipVerdict.test.ts`.
    const categories = macCycle.report!.categories as unknown as HipCategory[];
    const attached = categories
      .flatMap((c) => c.products)
      .reduce((n, p) => n + p.errors.length, 0);
    expect(attached).toBe(4);
    expect(errors).toHaveLength(6);
    expect(categoryErrors(errors, 'patch-management')).toHaveLength(2);
  });

  it('attributes errors to anti-malware and disk-backup', () => {
    expect(categoryErrors(errors, 'anti-malware')).toHaveLength(3);
    expect(categoryErrors(errors, 'disk-backup')).toHaveLength(1);
  });

  it('returns none for a category with no errors', () => {
    expect(categoryErrors(errors, 'firewall')).toHaveLength(0);
  });
});

describe('unattachedErrors', () => {
  it('returns only the errors that resolved to no product', () => {
    const un = unattachedErrors(errors, 'patch-management');
    expect(un).toHaveLength(2);
    expect(un.every((e) => e.product === null)).toBe(true);
  });

  it('returns none where every error attached to a product', () => {
    expect(unattachedErrors(errors, 'anti-malware')).toHaveLength(0);
  });
});
