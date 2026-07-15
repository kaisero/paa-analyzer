import { useCallback, useEffect, useMemo, useRef, useState } from 'react';
import { useParams } from 'react-router-dom';
import { useLogSources, useLogs } from '../../api/hooks';
import { useLogViewer } from '../../hooks/useLogViewer';
import { Sidebar } from '../layout/Sidebar';
import { LogToolbar } from './LogToolbar';
import { LogTable } from './LogTable';
import { LogPagination } from './LogPagination';

export function LogViewer() {
  const { sessionId } = useParams<{ sessionId: string }>();
  const {
    activeSource,
    setActiveSource,
    level,
    setLevel,
    search,
    setSearch,
    dateFrom,
    setDateFrom,
    dateTo,
    setDateTo,
    sortDir,
    toggleSort,
    page,
    setPage,
    pageSize,
    setPageSize,
    resetPage,
    expandedRows,
    toggleExpand,
    rawViewRows,
    toggleRawView,
    beautifyRows,
    toggleBeautify,
    columns,
    setColumnWidth,
    toggleColumnVisible,
    autoSizeColumns,
    customViewMode,
    setCustomViewMode,
    selectedSources,
    setSelectedSources,
    sourceParam,
    clearFilters,
  } = useLogViewer();

  // Debounced search
  const [debouncedSearch, setDebouncedSearch] = useState('');
  const searchTimerRef = useRef<ReturnType<typeof setTimeout>>(undefined);

  useEffect(() => {
    clearTimeout(searchTimerRef.current);
    searchTimerRef.current = setTimeout(() => {
      setDebouncedSearch(search);
      resetPage();
    }, 150);
    return () => clearTimeout(searchTimerRef.current);
  }, [search, resetPage]);

  // Fetch log sources
  const { data: sourcesData } = useLogSources(sessionId);
  const logSources = useMemo(() => sourcesData?.data ?? [], [sourcesData]);

  // Compute available date range from current source(s)
  const availableDateRange = useMemo(() => {
    const relevantSources = sourceParam
      ? logSources.filter((s) => sourceParam.split(',').includes(s.source))
      : logSources;
    let minDate: string | null = null;
    let maxDate: string | null = null;
    for (const s of relevantSources) {
      if (s.time_range.from && (!minDate || s.time_range.from < minDate)) minDate = s.time_range.from;
      if (s.time_range.to && (!maxDate || s.time_range.to > maxDate)) maxDate = s.time_range.to;
    }
    return { from: minDate, to: maxDate };
  }, [logSources, sourceParam]);

  // Fetch log entries
  const { data: logsData } = useLogs(sessionId, {
    source: sourceParam,
    level: level === 'all' ? undefined : level,
    search: debouncedSearch || undefined,
    date_from: dateFrom,
    date_to: dateTo,
    sort: sortDir,
    page,
    page_size: pageSize || undefined,
  });

  const entries = useMemo(() => logsData?.data ?? [], [logsData]);
  const meta = logsData?.meta ?? { total: 0, page: 1, page_size: 100, has_next: false };

  // Auto-size columns when source changes and data arrives
  const prevSourceRef = useRef(sourceParam);
  useEffect(() => {
    if (prevSourceRef.current !== sourceParam) {
      prevSourceRef.current = sourceParam;
      resetPage();
    }
  }, [sourceParam, resetPage]);

  useEffect(() => {
    if (entries.length > 0) {
      autoSizeColumns(entries);
    }
  }, [sourceParam, entries, autoSizeColumns]);


  // Page offset for expanded row tracking
  const pageOffset = pageSize === 0 ? 0 : (page - 1) * pageSize;

  // Handle page size change: reset page to 1
  const handlePageSizeChange = useCallback(
    (size: number) => {
      setPageSize(size);
      setPage(1);
    },
    [setPageSize, setPage],
  );

  // Handle source change from sidebar
  const handleSetActiveSource = useCallback(
    (source: string | null) => {
      if (customViewMode === 'applied') {
        setCustomViewMode('off');
      }
      setActiveSource(source);
      setPage(1);
    },
    [customViewMode, setCustomViewMode, setActiveSource, setPage],
  );

  // Handle level change: reset page
  const handleSetLevel = useCallback(
    (l: string) => {
      setLevel(l);
      setPage(1);
    },
    [setLevel, setPage],
  );

  if (!sessionId) return null;

  return (
    <div style={{ display: 'flex', height: '100%' }}>
      <Sidebar
        sessionId={sessionId}
        logSources={logSources}
        activeSource={activeSource}
        setActiveSource={handleSetActiveSource}
        customViewMode={customViewMode}
        setCustomViewMode={setCustomViewMode}
        selectedSources={selectedSources}
        setSelectedSources={setSelectedSources}
      />

      <div
        style={{
          flex: 1,
          display: 'flex',
          flexDirection: 'column',
          minWidth: 0,
        }}
      >
        <LogToolbar
          search={search}
          setSearch={setSearch}
          level={level}
          setLevel={handleSetLevel}
          dateFrom={dateFrom}
          setDateFrom={setDateFrom}
          dateTo={dateTo}
          setDateTo={setDateTo}
          onClear={clearFilters}
          availableDateRange={availableDateRange}
        />

        <LogTable
          entries={entries}
          columns={columns}
          expandedRows={expandedRows}
          onToggleExpand={toggleExpand}
          rawViewRows={rawViewRows}
          onToggleRawView={toggleRawView}
          beautifyRows={beautifyRows}
          onToggleBeautify={toggleBeautify}
          pageOffset={pageOffset}
          sortDir={sortDir}
          onToggleSort={toggleSort}
          toggleColumnVisible={toggleColumnVisible}
          onResizeColumn={setColumnWidth}
        />

        <LogPagination
          page={page}
          pageSize={pageSize}
          total={meta.total}
          hasNext={meta.has_next}
          onPageChange={setPage}
          onPageSizeChange={handlePageSizeChange}
        />
      </div>
    </div>
  );
}
