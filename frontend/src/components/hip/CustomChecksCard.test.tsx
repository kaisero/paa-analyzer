import { describe, it, expect } from 'vitest';
import { render, screen } from '@testing-library/react';
import hipFixture from '../../test/fixtures/hip.json';
import type { HipData } from '../../api/types';
import { CustomChecksCard } from './CustomChecksCard';

const macos = hipFixture.macos as unknown as HipData;
const windows = hipFixture.windows as unknown as HipData;
const checks = macos.cycles[0].report!.custom_checks!;

describe('CustomChecksCard', () => {
  it('renders the plist entry and its nested preference value', () => {
    render(<CustomChecksCard customChecks={checks} />);

    expect(screen.getByText('com.jamfsoftware.jamf')).toBeInTheDocument();
    expect(screen.getByText('jss_url')).toBeInTheDocument();
    expect(screen.getByText('https://jss.example.com:8443/')).toBeInTheDocument();
    expect(screen.getAllByText('exist yes').length).toBe(2);
  });

  it('is not rendered at all for the Windows fixture, which has no custom checks', () => {
    // Guard for the checklist row's `report.custom_checks &&` branch: the
    // Windows bundle emits no custom-check subtree.
    expect(windows.cycles[0].report!.custom_checks).toBeNull();
  });
});
