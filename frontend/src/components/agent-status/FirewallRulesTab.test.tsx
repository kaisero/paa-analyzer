import { describe, it, expect } from 'vitest';
import { cleanLabel } from './FirewallRulesTab';

describe('cleanLabel', () => {
  it('strips k prefix from direction labels', () => {
    expect(cleanLabel('kOut')).toBe('Out');
    expect(cleanLabel('kIn')).toBe('In');
  });

  it('strips k prefix from action labels', () => {
    expect(cleanLabel('kAllow')).toBe('Allow');
    expect(cleanLabel('kBlock')).toBe('Block');
  });

  it('passes through labels without k prefix', () => {
    expect(cleanLabel('Any')).toBe('Any');
    expect(cleanLabel('TCP')).toBe('TCP');
  });
});
