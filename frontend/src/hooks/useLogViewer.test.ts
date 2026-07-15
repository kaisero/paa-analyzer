import { describe, it, expect } from 'vitest';
import { renderHook, act } from '@testing-library/react';
import { useLogViewer } from './useLogViewer';
import { TestWrapper } from '../test/wrapper';

function renderLogViewer() {
  return renderHook(() => useLogViewer(), { wrapper: TestWrapper });
}

describe('useLogViewer — sort and filter state', () => {
  it('starts with desc sort direction', () => {
    const { result } = renderLogViewer();
    expect(result.current.sortDir).toBe('desc');
  });

  it('toggleSort flips direction and resets page', () => {
    const { result } = renderLogViewer();
    act(() => result.current.setPage(5));
    act(() => result.current.toggleSort());
    expect(result.current.sortDir).toBe('asc');
    expect(result.current.page).toBe(1);
  });

  it('toggleSort flips back to desc', () => {
    const { result } = renderLogViewer();
    act(() => result.current.toggleSort());
    act(() => result.current.toggleSort());
    expect(result.current.sortDir).toBe('desc');
  });

  it('clearFilters resets level, search, dates, and page', () => {
    const { result } = renderLogViewer();
    act(() => {
      result.current.setLevel('error');
      result.current.setSearch('tunnel');
      result.current.setDateFrom('2026-01-01');
      result.current.setDateTo('2026-12-31');
      result.current.setPage(3);
    });
    act(() => result.current.clearFilters());
    expect(result.current.level).toBe('all');
    expect(result.current.search).toBe('');
    expect(result.current.dateFrom).toBeUndefined();
    expect(result.current.dateTo).toBeUndefined();
    expect(result.current.page).toBe(1);
  });
});

describe('useLogViewer — raw/beautify mutual exclusion', () => {
  it('toggleRawView activates raw and deactivates beautify for same index', () => {
    const { result } = renderLogViewer();
    // First activate beautify
    act(() => result.current.toggleBeautify(5));
    expect(result.current.beautifyRows.has(5)).toBe(true);
    // Now toggle raw — should deactivate beautify
    act(() => result.current.toggleRawView(5));
    expect(result.current.rawViewRows.has(5)).toBe(true);
    expect(result.current.beautifyRows.has(5)).toBe(false);
  });

  it('toggleBeautify activates beautify and deactivates raw for same index', () => {
    const { result } = renderLogViewer();
    act(() => result.current.toggleRawView(3));
    expect(result.current.rawViewRows.has(3)).toBe(true);
    act(() => result.current.toggleBeautify(3));
    expect(result.current.beautifyRows.has(3)).toBe(true);
    expect(result.current.rawViewRows.has(3)).toBe(false);
  });

  it('toggling raw twice deactivates it', () => {
    const { result } = renderLogViewer();
    act(() => result.current.toggleRawView(1));
    act(() => result.current.toggleRawView(1));
    expect(result.current.rawViewRows.has(1)).toBe(false);
  });

  it('toggling beautify twice deactivates it', () => {
    const { result } = renderLogViewer();
    act(() => result.current.toggleBeautify(1));
    act(() => result.current.toggleBeautify(1));
    expect(result.current.beautifyRows.has(1)).toBe(false);
  });
});

describe('useLogViewer — column management', () => {
  it('setColumnWidth enforces minWidth floor', () => {
    const { result } = renderLogViewer();
    // timestamp has minWidth: 80
    act(() => result.current.setColumnWidth('timestamp', 10));
    const tsCol = result.current.columns.find((c) => c.id === 'timestamp')!;
    expect(tsCol.width).toBe(tsCol.minWidth);
  });

  it('toggleColumnVisible hides a visible column', () => {
    const { result } = renderLogViewer();
    act(() => result.current.toggleColumnVisible('source'));
    const srcCol = result.current.columns.find((c) => c.id === 'source')!;
    expect(srcCol.visible).toBe(false);
  });

  it('cannot hide the last visible column', () => {
    const { result } = renderLogViewer();
    // Hide all but one
    const ids = result.current.columns.map((c) => c.id);
    act(() => {
      for (const id of ids.slice(1)) {
        result.current.toggleColumnVisible(id);
      }
    });
    // Only first column visible — try to hide it
    const visibleBefore = result.current.columns.filter((c) => c.visible).length;
    expect(visibleBefore).toBe(1);
    act(() => result.current.toggleColumnVisible(ids[0]));
    const visibleAfter = result.current.columns.filter((c) => c.visible).length;
    expect(visibleAfter).toBe(1); // guard prevents hiding last
  });
});

describe('useLogViewer — custom view sourceParam', () => {
  it('returns activeSource when customViewMode is off', () => {
    const { result } = renderLogViewer();
    act(() => result.current.setActiveSource('Agent.Core.PAS'));
    expect(result.current.sourceParam).toBe('Agent.Core.PAS');
  });

  it('returns undefined when no source selected and mode is off', () => {
    const { result } = renderLogViewer();
    expect(result.current.sourceParam).toBeUndefined();
  });

  it('returns comma-joined selectedSources when mode is applied', () => {
    const { result } = renderLogViewer();
    act(() => {
      result.current.setSelectedSources(new Set(['Agent.Core.PAS', 'Agent.Core.traffic_log_json']));
      result.current.setCustomViewMode('applied');
    });
    expect(result.current.sourceParam).toContain('Agent.Core.PAS');
    expect(result.current.sourceParam).toContain('Agent.Core.traffic_log_json');
    expect(result.current.sourceParam!.split(',').length).toBe(2);
  });
});
