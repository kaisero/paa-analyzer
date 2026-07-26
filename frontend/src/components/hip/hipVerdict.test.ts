import { describe, it, expect } from 'vitest';
import hipFixture from '../../test/fixtures/hip.json';
import { productClause, categoryVerdict, customChecksVerdict, titleCase } from './hipVerdict';
import type { HipCategory, HipProduct } from '../../api/types';

const macCycle = hipFixture.macos.cycles[0];
const cat = (name: string) =>
  macCycle.report!.categories.find((c) => c.name === name) as unknown as HipCategory;
const prod = (catName: string, prodName: string) =>
  cat(catName).products.find((p) => p.name === prodName) as HipProduct;

describe('productClause', () => {
  it('reports a boolean attribute as on/off', () => {
    expect(productClause(prod('anti-malware', 'Cortex XDR'))).toBe('Cortex XDR real time on');
    expect(productClause(prod('anti-malware', 'Xprotect'))).toBe('Xprotect real time off');
  });

  it('reports enabled/disabled for is-enabled', () => {
    expect(productClause(prod('patch-management', 'Jamf Pro'))).toBe('Jamf Pro enabled');
    expect(productClause(prod('patch-management', 'Microsoft AutoUpdate')))
      .toBe('Microsoft AutoUpdate disabled');
  });

  it('calls an unknown product unverifiable regardless of its value', () => {
    // Gatekeeper reports real-time-protection "yes" but OPSWAT could not
    // confirm it, so the value must not be presented as fact.
    expect(productClause(prod('anti-malware', 'Gatekeeper'))).toBe('Gatekeeper unverifiable');
  });

  it('summarises drives for disk encryption', () => {
    expect(productClause(prod('disk-encryption', 'FileVault')))
      .toBe('FileVault 3/3 drives encrypted');
  });
});

describe('categoryVerdict', () => {
  it('joins product clauses', () => {
    expect(categoryVerdict(cat('anti-malware')))
      .toBe('Cortex XDR real time on  ·  Xprotect real time off  ·  Gatekeeper unverifiable');
  });

  it('falls back to status_reason when a category has no products', () => {
    expect(categoryVerdict(cat('certificate'))).toBe(cat('certificate').status_reason);
  });
});

describe('customChecksVerdict', () => {
  it('counts configured checks', () => {
    expect(customChecksVerdict(macCycle.report!.custom_checks as never))
      .toBe('1 plist check configured.');
  });

  it('handles a platform with no custom checks at all', () => {
    expect(customChecksVerdict(null)).toBe('No custom checks collected for this platform.');
  });
});

describe('titleCase', () => {
  it('title-cases a hyphenated category name, matching the checklist row labels', () => {
    expect(titleCase('patch-management')).toBe('Patch Management');
    expect(titleCase('anti-malware')).toBe('Anti Malware');
  });

  it('renders an em dash for a null category', () => {
    expect(titleCase(null)).toBe('—');
  });
});
