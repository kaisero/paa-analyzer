import { describe, it, expect, beforeEach, afterEach } from 'vitest';
import { render, screen } from '@testing-library/react';
import { MemoryRouter } from 'react-router-dom';
import { ThemeProvider } from '../../contexts/ThemeContext';
import { Sidebar } from './Sidebar';
import type { LogSource } from '../../api/types';
import { FOOTER_BAR_HEIGHT } from '../log-viewer/LogPagination';

const sources: LogSource[] = [
  {
    source: 'Agent.Core.PAS',
    module: 'Agent',
    component: 'Core',
    total_entries: 10,
    levels: { error: 2, warning: 1 },
    time_range: { from: null, to: null },
  },
];

function renderSidebar() {
  return render(
    <ThemeProvider>
      <MemoryRouter>
        <Sidebar
          sessionId="s1"
          logSources={sources}
          activeSource={null}
          setActiveSource={() => {}}
          customViewMode="off"
          setCustomViewMode={() => {}}
          selectedSources={new Set()}
          setSelectedSources={() => {}}
        />
      </MemoryRouter>
    </ThemeProvider>,
  );
}

describe('Sidebar', () => {
  afterEach(() => window.localStorage.clear());

  describe('menu theme', () => {
    // The menu used to be hardcoded `theme="dark"`, which painted white text on
    // the light sidebar in light mode — white on white, unreadable.
    beforeEach(() => window.localStorage.clear());

    it('uses the dark menu when the app is dark', () => {
      window.localStorage.setItem('theme', 'dark');
      const { container } = renderSidebar();
      const menu = container.querySelector('.ant-menu')!;
      expect(menu.className).toContain('ant-menu-dark');
    });

    it('uses the light menu when the app is light', () => {
      window.localStorage.setItem('theme', 'light');
      const { container } = renderSidebar();
      const menu = container.querySelector('.ant-menu')!;
      expect(menu.className).not.toContain('ant-menu-dark');
    });
  });

  it('lines its footer bar up with the log pagination bar', () => {
    // Both bars sit along the bottom of the log viewer, so they share a pinned
    // height; without it they differed by a few pixels and looked misaligned.
    window.localStorage.setItem('theme', 'dark');
    renderSidebar();
    const footer = screen.getByText(/errors ·/).closest('div') as HTMLElement;
    expect(footer.style.height).toBe(`${FOOTER_BAR_HEIGHT}px`);
    expect(footer.style.alignItems).toBe('center');
  });
});
