import { describe, it, expect } from 'vitest';
import { render, screen } from '@testing-library/react';
import { hipFixture } from '../../test/handlers';
import type { HipData } from '../../api/types';
import { MissingPatchesTable } from './MissingPatchesTable';

const macos = hipFixture.macos as unknown as HipData;
const patchMgmt = macos.cycles[0].report!.categories.find((c) => c.name === 'patch-management')!;

describe('MissingPatchesTable', () => {
  it('renders every patch with its severity, reference and reboot flag', () => {
    render(
      <MissingPatchesTable patches={patchMgmt.missing_patches} source={patchMgmt.patches_source} />,
    );

    expect(screen.getByText('missing patches (2)')).toBeInTheDocument();
    expect(screen.getByText('from PAComplianceMp')).toBeInTheDocument();

    for (const patch of patchMgmt.missing_patches) {
      expect(screen.getByText(patch.title!)).toBeInTheDocument();
      expect(screen.getByText(patch.kb_article_id!)).toBeInTheDocument();
    }
    expect(screen.getByText('important')).toBeInTheDocument();
    expect(screen.getByText('moderate')).toBeInTheDocument();
    // macOS Tahoe requires a restart, Safari does not.
    expect(screen.getByText('yes')).toBeInTheDocument();
    expect(screen.getByText('no')).toBeInTheDocument();
  });
});
