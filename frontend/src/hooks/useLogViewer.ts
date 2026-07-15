import { useState, useCallback } from 'react';
import { useSearchParams } from 'react-router-dom';

export interface ColumnDef {
  id: string;
  label: string;
  visible: boolean;
  width: number;
  minWidth: number;
}

const DEFAULT_COLUMNS: ColumnDef[] = [
  { id: 'timestamp', label: 'Timestamp', visible: true, width: 190, minWidth: 80 },
  { id: 'source', label: 'Source', visible: true, width: 140, minWidth: 60 },
  { id: 'level', label: 'Level', visible: true, width: 80, minWidth: 60 },
  { id: 'message', label: 'Message', visible: true, width: 0, minWidth: 100 }, // flex
];

export function useLogViewer() {
  const [searchParams] = useSearchParams();
  const [activeSource, setActiveSource] = useState<string | null>(searchParams.get('source'));
  const [level, setLevel] = useState('all');
  const [search, setSearch] = useState(searchParams.get('search') || '');
  const [dateFrom, setDateFrom] = useState<string | undefined>();
  const [dateTo, setDateTo] = useState<string | undefined>();
  const [sortDir, setSortDir] = useState<'asc' | 'desc'>('desc');
  const [page, setPage] = useState(1);
  const [pageSize, setPageSize] = useState(100);
  const [expandedRows, setExpandedRows] = useState<Set<number>>(new Set());
  const [rawViewRows, setRawViewRows] = useState<Set<number>>(new Set());
  const [beautifyRows, setBeautifyRows] = useState<Set<number>>(new Set());
  const [columns, setColumns] = useState<ColumnDef[]>(DEFAULT_COLUMNS);

  // Custom view
  const [customViewMode, setCustomViewMode] = useState<'off' | 'selecting' | 'applied'>('off');
  const [selectedSources, setSelectedSources] = useState<Set<string>>(new Set());

  const resetPage = useCallback(() => setPage(1), []);

  const toggleSort = useCallback(() => {
    setSortDir((d) => (d === 'desc' ? 'asc' : 'desc'));
    setPage(1);
  }, []);

  const toggleExpand = useCallback((idx: number) => {
    setExpandedRows((prev) => {
      const next = new Set(prev);
      if (next.has(idx)) next.delete(idx);
      else next.add(idx);
      return next;
    });
  }, []);

  const toggleRawView = useCallback((idx: number) => {
    setRawViewRows((prev) => {
      const next = new Set(prev);
      if (next.has(idx)) next.delete(idx);
      else next.add(idx);
      return next;
    });
    // Deactivate beautify when raw is toggled on
    setBeautifyRows((prev) => {
      const next = new Set(prev);
      next.delete(idx);
      return next;
    });
  }, []);

  const toggleBeautify = useCallback((idx: number) => {
    setBeautifyRows((prev) => {
      const next = new Set(prev);
      if (next.has(idx)) next.delete(idx);
      else next.add(idx);
      return next;
    });
    // Deactivate raw view when beautify is toggled on
    setRawViewRows((prev) => {
      const next = new Set(prev);
      next.delete(idx);
      return next;
    });
  }, []);

  const setColumnWidth = useCallback((id: string, width: number) => {
    setColumns((cols) => cols.map((c) => (c.id === id ? { ...c, width: Math.max(c.minWidth, width) } : c)));
  }, []);

  const toggleColumnVisible = useCallback((id: string) => {
    setColumns((cols) => {
      const visibleCount = cols.filter((c) => c.visible).length;
      return cols.map((c) => {
        if (c.id !== id) return c;
        if (c.visible && visibleCount <= 1) return c; // keep at least 1
        return { ...c, visible: !c.visible };
      });
    });
  }, []);

  const autoSizeColumns = useCallback((entries: Array<Record<string, unknown>>) => {
    if (entries.length === 0) return;
    const canvas = document.createElement('canvas').getContext('2d');
    if (!canvas) return;

    // Measure content text widths (monospace 11px for data)
    canvas.font = '11px "JetBrains Mono", monospace';
    const tsContentWidth = canvas.measureText('2026-04-02 00:37:28.033').width;
    let maxSrc = 0;
    const seenSrc = new Set<string>();
    for (const e of entries.slice(0, 200)) {
      const s = String(e.source || '');
      if (!seenSrc.has(s)) {
        seenSrc.add(s);
        maxSrc = Math.max(maxSrc, canvas.measureText(s).width);
      }
    }
    const levels = new Set(entries.slice(0, 200).map((e) => String(e.level || '')).filter(Boolean));
    let maxLvl = 0;
    for (const l of levels) maxLvl = Math.max(maxLvl, canvas.measureText(l.toUpperCase()).width);

    // Measure header text widths (Inter 14px for headers) — must fit header label too
    canvas.font = '14px "Inter", system-ui, sans-serif';
    const tsHeaderWidth = canvas.measureText('Timestamp \u2193').width;
    const srcHeaderWidth = canvas.measureText('Source').width;
    const lvlHeaderWidth = canvas.measureText('Level').width;

    // Column width = max(content, header) + cell padding (24px for antd small table)
    const pad = 24;
    setColumns((cols) => cols.map((c) => {
      if (c.id === 'timestamp') return { ...c, width: Math.round(Math.max(tsContentWidth, tsHeaderWidth) + pad) };
      if (c.id === 'source') return { ...c, width: Math.round(Math.max(60, Math.min(250, Math.max(maxSrc, srcHeaderWidth) + pad))) };
      if (c.id === 'level') return { ...c, width: Math.round(Math.max(50, Math.min(100, Math.max(maxLvl, lvlHeaderWidth) + pad))) };
      return c;
    }));
  }, []);

  // Build the source query param for the API
  const sourceParam = (() => {
    if (customViewMode === 'applied' && selectedSources.size > 0) {
      return Array.from(selectedSources).join(',');
    }
    return activeSource ?? undefined;
  })();

  const clearFilters = useCallback(() => {
    setLevel('all');
    setSearch('');
    setDateFrom(undefined);
    setDateTo(undefined);
    setPage(1);
  }, []);

  return {
    activeSource, setActiveSource,
    level, setLevel,
    search, setSearch,
    dateFrom, setDateFrom, dateTo, setDateTo,
    sortDir, toggleSort,
    page, setPage, pageSize, setPageSize, resetPage,
    expandedRows, toggleExpand,
    rawViewRows, toggleRawView,
    beautifyRows, toggleBeautify,
    columns, setColumnWidth, toggleColumnVisible, autoSizeColumns,
    customViewMode, setCustomViewMode, selectedSources, setSelectedSources,
    sourceParam,
    clearFilters,
  };
}
