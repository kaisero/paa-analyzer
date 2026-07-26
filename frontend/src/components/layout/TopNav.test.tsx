import { describe, it, expect } from 'vitest';
import { screen } from '@testing-library/react';
import { renderWithProviders } from '../../test/wrapper';
import { TopNav } from './TopNav';

describe('TopNav', () => {
  it('orders tabs Overview, HIP, Log Viewer', () => {
    renderWithProviders(<TopNav sessionId="s1" />);
    const labels = screen.getAllByRole('tab').map((t) => t.textContent);
    expect(labels).toEqual(['Overview', 'HIP', 'Log Viewer']);
  });
});
