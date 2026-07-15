import { describe, it, expect } from 'vitest';
import { render, screen } from '@testing-library/react';
import { fmtTs, LogTable } from './LogTable';
import type { LogEntry } from '../../api/types';
import type { ColumnDef } from '../../hooks/useLogViewer';

describe('fmtTs — timestamp formatting', () => {
  it('formats valid ISO timestamp to local datetime with milliseconds', () => {
    const result = fmtTs('2026-04-03T07:24:40.123Z');
    // Should contain date, time, and milliseconds
    expect(result).toContain('2026');
    expect(result).toContain('.123');
  });

  it('returns original string for invalid timestamp', () => {
    expect(fmtTs('not-a-date')).toBe('not-a-date');
  });

  it('handles ISO timestamp with timezone offset', () => {
    const result = fmtTs('2026-04-03T09:24:40.000+02:00');
    expect(result).toContain('2026');
    // Should have milliseconds portion
    expect(result).toMatch(/\.\d{3}$/);
  });

  it('pads single-digit components with zeros', () => {
    // January 5, 2026 at 03:04:05.006 UTC
    const result = fmtTs('2026-01-05T03:04:05.006Z');
    expect(result).toContain('-01-05');
    expect(result).toContain('.006');
  });
});

describe('LogTable — rendering', () => {
  const defaultColumns: ColumnDef[] = [
    { id: 'timestamp', label: 'Timestamp', visible: true, width: 190, minWidth: 80 },
    { id: 'source', label: 'Source', visible: true, width: 140, minWidth: 60 },
    { id: 'level', label: 'Level', visible: true, width: 80, minWidth: 60 },
    { id: 'message', label: 'Message', visible: true, width: 0, minWidth: 100 },
  ];

  const sampleEntries: LogEntry[] = [
    { timestamp: '2026-04-03T07:24:40.100Z', level: 'info', source: 'PAS', message: 'Test message one' },
    { timestamp: '2026-04-03T07:24:41.200Z', level: 'error', source: 'PAS', message: 'Error occurred' },
  ];

  const noop = () => {};

  function renderTable(overrides: Partial<Parameters<typeof LogTable>[0]> = {}) {
    return render(
      <LogTable
        entries={sampleEntries}
        columns={defaultColumns}
        expandedRows={new Set()}
        onToggleExpand={noop}
        rawViewRows={new Set()}
        onToggleRawView={noop}
        beautifyRows={new Set()}
        onToggleBeautify={noop}
        pageOffset={0}
        sortDir="desc"
        onToggleSort={noop}
        toggleColumnVisible={noop}
        onResizeColumn={noop}
        {...overrides}
      />,
    );
  }

  it('renders entries with message text', () => {
    renderTable();
    expect(screen.getByText('Test message one')).toBeInTheDocument();
    expect(screen.getByText('Error occurred')).toBeInTheDocument();
  });

  it('renders level tags', () => {
    renderTable();
    expect(screen.getByText('info')).toBeInTheDocument();
    expect(screen.getByText('error')).toBeInTheDocument();
  });

  it('hides columns that have visible: false', () => {
    const cols = defaultColumns.map((c) =>
      c.id === 'source' ? { ...c, visible: false } : c,
    );
    renderTable({ columns: cols });
    // Source column header should not be present
    expect(screen.queryByText('Source')).not.toBeInTheDocument();
    // But other columns should be
    expect(screen.getByText('Message')).toBeInTheDocument();
  });

  it('shows raw JSON view when rawViewRows includes the row index', () => {
    renderTable({ rawViewRows: new Set([0]) });
    // Raw view renders JSON.stringify of the record — should contain the message
    const pre = document.querySelector('pre');
    expect(pre).not.toBeNull();
    expect(pre!.textContent).toContain('Test message one');
  });

  it('shows empty state when no entries', () => {
    renderTable({ entries: [] });
    expect(screen.getByText('No entries match your filters')).toBeInTheDocument();
  });
});
