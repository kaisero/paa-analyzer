import { useCallback } from 'react';
import { Table, Tag, Empty, Popover, Checkbox } from 'antd';
import { SettingOutlined, CodeOutlined, FormatPainterOutlined } from '@ant-design/icons';
import type { ColumnsType, ColumnType } from 'antd/es/table';
import type { LogEntry } from '../../api/types';
import type { ColumnDef } from '../../hooks/useLogViewer';

interface LogTableProps {
  entries: LogEntry[];
  columns: ColumnDef[];
  expandedRows: Set<number>;
  onToggleExpand: (idx: number) => void;
  rawViewRows: Set<number>;
  onToggleRawView: (idx: number) => void;
  beautifyRows: Set<number>;
  onToggleBeautify: (idx: number) => void;
  pageOffset: number;
  sortDir: 'asc' | 'desc';
  onToggleSort: () => void;
  toggleColumnVisible: (id: string) => void;
  onResizeColumn: (id: string, width: number) => void;
}

// eslint-disable-next-line react-refresh/only-export-components
export function fmtTs(iso: string): string {
  const d = new Date(iso);
  if (isNaN(d.getTime())) return iso;
  const Y = d.getFullYear();
  const M = String(d.getMonth() + 1).padStart(2, '0');
  const D = String(d.getDate()).padStart(2, '0');
  const h = String(d.getHours()).padStart(2, '0');
  const m = String(d.getMinutes()).padStart(2, '0');
  const s = String(d.getSeconds()).padStart(2, '0');
  const ms = String(d.getMilliseconds()).padStart(3, '0');
  return `${Y}-${M}-${D} ${h}:${m}:${s}.${ms}`;
}

const LEVEL_TAG_COLORS: Record<string, string> = {
  error: 'red',
  warning: 'gold',
  info: 'cyan',
  debug: 'default',
};

// Resizable header cell
function ResizableHeaderCell({
  onResize,
  width,
  resizable,
  ...restProps
}: React.HTMLAttributes<HTMLTableCellElement> & {
  onResize?: (width: number) => void;
  width?: number;
  resizable?: boolean;
}) {
  if (!resizable || !width) {
    return <th {...restProps} />;
  }

  const handleMouseDown = (e: React.MouseEvent) => {
    e.preventDefault();
    e.stopPropagation();
    const startX = e.clientX;
    const startWidth = width;
    document.body.style.cursor = 'col-resize';
    document.body.style.userSelect = 'none';

    const onMouseMove = (ev: MouseEvent) => {
      onResize?.(Math.max(40, startWidth + ev.clientX - startX));
    };
    const onMouseUp = () => {
      document.body.style.cursor = '';
      document.body.style.userSelect = '';
      document.removeEventListener('mousemove', onMouseMove);
      document.removeEventListener('mouseup', onMouseUp);
    };
    document.addEventListener('mousemove', onMouseMove);
    document.addEventListener('mouseup', onMouseUp);
  };

  return (
    <th {...restProps} style={{ ...restProps.style, position: 'relative' }}>
      {restProps.children}
      <div
        onMouseDown={handleMouseDown}
        style={{ position: 'absolute', right: -4, top: 0, bottom: 0, width: 8, cursor: 'col-resize', zIndex: 2 }}
        onMouseEnter={(e) => { e.currentTarget.style.background = 'var(--focus)'; e.currentTarget.style.opacity = '0.3'; }}
        onMouseLeave={(e) => { e.currentTarget.style.background = ''; e.currentTarget.style.opacity = ''; }}
      />
    </th>
  );
}

export function LogTable({
  entries,
  columns,
  expandedRows,
  onToggleExpand,
  rawViewRows,
  onToggleRawView,
  beautifyRows,
  onToggleBeautify,
  pageOffset,
  sortDir,
  onToggleSort,
  toggleColumnVisible,
  onResizeColumn,
}: LogTableProps) {
  const colMap = new Map(columns.map((c) => [c.id, c]));

  const handleResize = useCallback(
    (colId: string) => (newWidth: number) => { onResizeColumn(colId, newWidth); },
    [onResizeColumn],
  );

  // Column visibility popover content
  const columnSettings = (
    <div style={{ display: 'flex', flexDirection: 'column', gap: 4, minWidth: 140 }}>
      {columns.map((col) => (
        <Checkbox
          key={col.id}
          checked={col.visible}
          onChange={() => toggleColumnVisible(col.id)}
          style={{ fontSize: 12 }}
        >
          {col.label}
        </Checkbox>
      ))}
    </div>
  );

  const antColumns: (ColumnType<LogEntry> & { resizable?: boolean; onResize?: (w: number) => void })[] = [];

  const tsCol = colMap.get('timestamp');
  if (tsCol?.visible) {
    antColumns.push({
      title: (
        <span onClick={onToggleSort} style={{ cursor: 'pointer', userSelect: 'none' }}>
          Timestamp {sortDir === 'desc' ? '\u2193' : '\u2191'}
        </span>
      ),
      dataIndex: 'timestamp', key: 'timestamp', width: tsCol.width,
      resizable: true, onResize: handleResize('timestamp'),
      render: (val: string) => (
        <span style={{ fontFamily: "'JetBrains Mono', monospace", fontSize: 11, color: 'var(--text-dim)', whiteSpace: 'nowrap' }}>
          {val ? fmtTs(val) : ''}
        </span>
      ),
    });
  }

  const srcCol = colMap.get('source');
  if (srcCol?.visible) {
    antColumns.push({
      title: 'Source', dataIndex: 'source', key: 'source', width: srcCol.width,
      resizable: true, onResize: handleResize('source'), ellipsis: true,
      render: (val: string) => (
        <span title={val || ''} style={{ fontFamily: "'JetBrains Mono', monospace", fontSize: 11, color: 'var(--info)', overflow: 'hidden', textOverflow: 'ellipsis', whiteSpace: 'nowrap', display: 'block' }}>
          {val || ''}
        </span>
      ),
    });
  }

  const lvlCol = colMap.get('level');
  if (lvlCol?.visible) {
    antColumns.push({
      title: 'Level', dataIndex: 'level', key: 'level', width: lvlCol.width,
      resizable: true, onResize: handleResize('level'),
      render: (val: string) => (
        <Tag color={LEVEL_TAG_COLORS[val] ?? 'default'} style={{ fontSize: 10, fontWeight: 600, textTransform: 'uppercase', padding: '0 4px', margin: 0, lineHeight: '18px', borderRadius: 3 }}>
          {val}
        </Tag>
      ),
    });
  }

  const msgCol = colMap.get('message');
  if (msgCol?.visible) {
    antColumns.push({
      title: (
        <span style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', width: '100%' }}>
          <span>Message</span>
          <Popover content={columnSettings} title="Columns" trigger="click" placement="bottomRight">
            <SettingOutlined
              onClick={(e) => e.stopPropagation()}
              style={{ fontSize: 12, color: 'var(--text-dim)', cursor: 'pointer' }}
            />
          </Popover>
        </span>
      ),
      dataIndex: 'message', key: 'message',
      render: (val: string, record: LogEntry, index: number) => {
        const gIdx = pageOffset + index;
        const expanded = expandedRows.has(gIdx);
        const showRaw = rawViewRows.has(gIdx);
        const showBeautified = beautifyRows.has(gIdx);
        const displayMsg = showBeautified && record.beautified ? record.beautified : (val || '');
        const multiline = displayMsg.split('\n').length > 3 || displayMsg.length > 300;
        return (
          <div style={{ position: 'relative' }}>
            {/* Action buttons */}
            <span className="row-action-btns" style={{ position: 'absolute', top: 0, right: 0, zIndex: 1, display: 'flex', gap: 4 }}>
              {record.beautified && (
                <FormatPainterOutlined
                  onClick={(e) => { e.stopPropagation(); onToggleBeautify(gIdx); }}
                  style={{ fontSize: 12, color: showBeautified ? 'var(--info)' : 'var(--text-dim)', cursor: 'pointer', padding: 2, opacity: showBeautified ? 1 : undefined }}
                />
              )}
              <CodeOutlined
                onClick={(e) => { e.stopPropagation(); onToggleRawView(gIdx); }}
                style={{ fontSize: 12, color: showRaw ? 'var(--info)' : 'var(--text-dim)', cursor: 'pointer', padding: 2, opacity: showRaw ? 1 : undefined }}
              />
            </span>
            {/* Message text */}
            <span style={{
              display: expanded || showBeautified ? 'block' : '-webkit-box',
              WebkitLineClamp: expanded || showBeautified ? undefined : 3,
              WebkitBoxOrient: expanded || showBeautified ? undefined : 'vertical',
              overflow: expanded || showBeautified ? 'visible' : 'hidden',
              whiteSpace: 'pre-wrap', wordBreak: 'break-word',
              color: 'var(--text-sec)', fontFamily: "'JetBrains Mono', monospace", fontSize: 12,
              paddingRight: 40,
            }}>
              {displayMsg}
              {!expanded && !showBeautified && multiline && (
                <span style={{ display: 'block', color: 'var(--text-dim)', fontSize: 10, letterSpacing: 2, lineHeight: 1, marginTop: 1 }}>
                  &middot;&middot;&middot;
                </span>
              )}
            </span>
            {/* Raw JSON view */}
            {showRaw && (
              <pre
                onClick={(e) => e.stopPropagation()}
                style={{
                  marginTop: 8,
                  padding: 8,
                  background: 'var(--elevated)',
                  border: '1px solid var(--border)',
                  borderLeft: '3px solid var(--accent)',
                  fontFamily: 'var(--mono)',
                  fontSize: 11,
                  color: 'var(--text-sec)',
                  whiteSpace: 'pre-wrap',
                  wordBreak: 'break-word',
                  overflow: 'auto',
                  maxHeight: 400,
                }}
              >
                {JSON.stringify(record, null, 2)}
              </pre>
            )}
          </div>
        );
      },
    });
  }

  return (
    <div style={{ flex: 1, overflow: 'auto', minHeight: 0 }}>
      <style>{`
        .ant-table-row .row-action-btns > * { opacity: 0; transition: opacity 0.15s; }
        .ant-table-row:hover .row-action-btns > * { opacity: 1; }
      `}</style>
      <Table<LogEntry>
        dataSource={entries}
        columns={antColumns as ColumnsType<LogEntry>}
        rowKey={(_record, index) => String(pageOffset + (index ?? 0))}
        pagination={false}
        size="small"
        showHeader
        onRow={(_record, index) => ({
          onClick: () => { if (index !== undefined) onToggleExpand(pageOffset + index); },
          style: { cursor: 'pointer' },
        })}
        components={{ header: { cell: ResizableHeaderCell } }}
        locale={{ emptyText: <Empty description="No entries match your filters" /> }}
      />
    </div>
  );
}
