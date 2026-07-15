import { useCallback, useEffect, useRef, useState } from 'react';
import { Button, Checkbox, Menu } from 'antd';
import type { MenuProps } from 'antd';
import type { LogSource } from '../../api/types';

interface SidebarProps {
  sessionId: string;
  logSources: LogSource[];
  activeSource: string | null;
  setActiveSource: (source: string | null) => void;
  customViewMode: 'off' | 'selecting' | 'applied';
  setCustomViewMode: (mode: 'off' | 'selecting' | 'applied') => void;
  selectedSources: Set<string>;
  setSelectedSources: (sources: Set<string>) => void;
}

export function Sidebar({
  logSources,
  activeSource,
  setActiveSource,
  customViewMode,
  setCustomViewMode,
  selectedSources,
  setSelectedSources,
}: SidebarProps) {
  const [width, setWidth] = useState(260);
  const sidebarRef = useRef<HTMLDivElement>(null);
  const resizing = useRef(false);

  const onResizeStart = useCallback(
    (e: React.MouseEvent) => {
      e.preventDefault();
      resizing.current = true;
      const startX = e.clientX;
      const startW = width;
      const onMove = (ev: MouseEvent) => {
        setWidth(Math.min(500, Math.max(180, startW + ev.clientX - startX)));
      };
      const onUp = () => {
        resizing.current = false;
        document.body.style.cursor = '';
        document.body.style.userSelect = '';
        document.removeEventListener('mousemove', onMove);
        document.removeEventListener('mouseup', onUp);
      };
      document.body.style.cursor = 'col-resize';
      document.body.style.userSelect = 'none';
      document.addEventListener('mousemove', onMove);
      document.addEventListener('mouseup', onUp);
    },
    [width],
  );

  // Group sources by module / component
  const groups = new Map<string, (LogSource & { key: string; displayName: string })[]>();
  for (const src of logSources) {
    const groupKey = `${src.module} / ${src.component}`;
    if (!groups.has(groupKey)) groups.set(groupKey, []);
    const prefix = `${src.module}.${src.component}.`;
    const displayName = src.source.startsWith(prefix)
      ? src.source.slice(prefix.length)
      : src.source;
    groups.get(groupKey)!.push({ ...src, key: src.source, displayName });
  }
  const sortedGroupKeys = Array.from(groups.keys()).sort();

  const totalErrors = logSources.reduce((sum, s) => sum + (s.levels['error'] ?? 0), 0);
  const allSourceKeys = logSources.map((s) => s.source);

  // Custom View actions
  const handleCustomViewClick = () => {
    if (customViewMode === 'off') {
      setCustomViewMode('selecting');
      setSelectedSources(new Set(allSourceKeys));
    } else if (customViewMode === 'selecting') {
      if (selectedSources.size === 0) return;
      setCustomViewMode('applied');
    } else {
      setCustomViewMode('off');
      setActiveSource(null);
    }
  };

  const toggleSource = (key: string) => {
    const next = new Set(selectedSources);
    if (next.has(key)) next.delete(key);
    else next.add(key);
    setSelectedSources(next);
  };

  const toggleSelectAll = () => {
    const allChecked = allSourceKeys.every((k) => selectedSources.has(k));
    setSelectedSources(allChecked ? new Set() : new Set(allSourceKeys));
  };

  const toggleGroup = (groupKey: string) => {
    const groupFiles = groups.get(groupKey);
    if (!groupFiles) return;
    const groupKeys = groupFiles.map((f) => f.key);
    const allChecked = groupKeys.every((k) => selectedSources.has(k));
    const next = new Set(selectedSources);
    for (const k of groupKeys) {
      if (allChecked) next.delete(k);
      else next.add(k);
    }
    setSelectedSources(next);
  };

  // ESC to cancel selection
  useEffect(() => {
    if (customViewMode !== 'selecting') return;
    const onKey = (e: KeyboardEvent) => {
      if (e.key === 'Escape') setCustomViewMode('off');
    };
    document.addEventListener('keydown', onKey);
    return () => document.removeEventListener('keydown', onKey);
  }, [customViewMode, setCustomViewMode]);

  const selecting = customViewMode === 'selecting';
  const isCustomApplied = customViewMode === 'applied';

  // Button label/style
  let btnLabel = 'Custom View';
  let btnType: 'default' | 'primary' = 'default';
  let btnDanger = false;
  if (selecting) {
    btnLabel = `Apply (${selectedSources.size} selected)`;
    btnType = 'primary';
  } else if (isCustomApplied) {
    btnLabel = 'Reset';
    btnDanger = true;
  }

  // Build Menu items for normal mode
  const buildMenuItems = (): MenuProps['items'] => {
    const items: MenuProps['items'] = [];

    // All Logs item
    items.push({
      key: '__all__',
      label: (
        <span style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', width: '100%' }}>
          <span>All Logs</span>
          <span style={{ display: 'flex', gap: 4, flexShrink: 0, marginLeft: 6, alignItems: 'center' }}>
            {totalErrors > 0 && (
              <span title={`${totalErrors.toLocaleString()} errors`} style={{ width: 7, height: 7, borderRadius: '50%', background: 'var(--red)', flexShrink: 0 }} />
            )}
          </span>
        </span>
      ),
    });

    // Custom View applied label
    if (isCustomApplied) {
      items.push({
        key: '__custom_view__',
        disabled: true,
        label: (
          <span
            style={{
              fontSize: 12,
              fontFamily: "'JetBrains Mono', monospace",
              color: 'var(--green)',
            }}
          >
            Custom View ({selectedSources.size})
          </span>
        ),
      });
    }

    // Groups
    for (const groupKey of sortedGroupKeys) {
      const files = groups.get(groupKey)!;
      const sorted = [...files].sort((a, b) => a.displayName.localeCompare(b.displayName));

      items.push({
        key: `group_${groupKey}`,
        type: 'group',
        label: groupKey,
        children: sorted.map((f) => {
          const errors = f.levels['error'] ?? 0;
          const warnings = f.levels['warning'] ?? 0;
          return {
            key: f.key,
            label: (
              <span
                title={f.key}
                style={{
                  display: 'flex',
                  alignItems: 'center',
                  justifyContent: 'space-between',
                  width: '100%',
                  fontFamily: "'JetBrains Mono', monospace",
                  fontSize: 12,
                }}
              >
                <span style={{ overflow: 'hidden', textOverflow: 'ellipsis', whiteSpace: 'nowrap', flex: 1 }}>
                  {f.displayName}
                </span>
                <span style={{ display: 'flex', gap: 4, flexShrink: 0, marginLeft: 6, alignItems: 'center' }}>
                  {errors > 0 && (
                    <span title={`${errors.toLocaleString()} errors`} style={{ width: 7, height: 7, borderRadius: '50%', background: 'var(--red)', flexShrink: 0 }} />
                  )}
                  {warnings > 0 && (
                    <span title={`${warnings.toLocaleString()} warnings`} style={{ width: 7, height: 7, borderRadius: '50%', background: 'var(--yellow)', flexShrink: 0 }} />
                  )}
                </span>
              </span>
            ),
          };
        }),
      });
    }

    return items;
  };

  const handleMenuClick: MenuProps['onClick'] = (info) => {
    if (info.key === '__all__') {
      setActiveSource(null);
    } else if (info.key === '__custom_view__') {
      // disabled item, no action
    } else {
      setActiveSource(info.key);
    }
  };

  // Determine selected key
  const selectedKeys: string[] = [];
  if (isCustomApplied) {
    selectedKeys.push('__custom_view__');
  } else if (activeSource === null) {
    selectedKeys.push('__all__');
  } else {
    selectedKeys.push(activeSource);
  }

  return (
    <div
      ref={sidebarRef}
      style={{
        width, minWidth: 180, maxWidth: 500,
        background: 'var(--surface)',
        borderRight: '1px solid var(--border)',
        display: 'flex', flexDirection: 'column', flexShrink: 0,
        position: 'relative',
      }}
    >
      {/* Resize handle */}
      <div
        onMouseDown={onResizeStart}
        style={{ position: 'absolute', top: 0, right: -4, bottom: 0, width: 8, cursor: 'col-resize', zIndex: 10 }}
        onMouseEnter={(e) => { (e.currentTarget as HTMLDivElement).style.background = 'var(--focus)'; (e.currentTarget as HTMLDivElement).style.opacity = '0.3'; }}
        onMouseLeave={(e) => { if (!resizing.current) { (e.currentTarget as HTMLDivElement).style.background = ''; (e.currentTarget as HTMLDivElement).style.opacity = ''; } }}
      />

      {/* Scrollable body */}
      <div style={{ flex: 1, overflowY: 'auto', padding: selecting ? 8 : 0 }}>
        {selecting ? (
          /* Selection mode with checkboxes */
          <>
            {/* Select All */}
            <SelectionRow onClick={toggleSelectAll} paddingLeft={8}>
              <Checkbox
                checked={allSourceKeys.every((k) => selectedSources.has(k))}
                indeterminate={
                  allSourceKeys.some((k) => selectedSources.has(k)) &&
                  !allSourceKeys.every((k) => selectedSources.has(k))
                }
              />
              <span style={{ fontSize: 11, color: 'var(--text3)' }}>
                {allSourceKeys.every((k) => selectedSources.has(k)) ? 'Deselect all' : 'Select all'}
              </span>
            </SelectionRow>

            {/* Groups */}
            {sortedGroupKeys.map((groupKey) => {
              const files = groups.get(groupKey)!;
              const sorted = [...files].sort((a, b) => a.displayName.localeCompare(b.displayName));
              const groupAllChecked = files.every((f) => selectedSources.has(f.key));
              const groupSomeChecked = !groupAllChecked && files.some((f) => selectedSources.has(f.key));

              return (
                <div key={groupKey} style={{ marginTop: 12 }}>
                  <SelectionRow onClick={() => toggleGroup(groupKey)} paddingLeft={8}>
                    <Checkbox
                      checked={groupAllChecked}
                      indeterminate={groupSomeChecked}
                    />
                    <span style={{
                      fontSize: 10, fontWeight: 600, textTransform: 'uppercase',
                      letterSpacing: '0.08em', color: 'var(--text3)',
                    }}>
                      {groupKey}
                    </span>
                  </SelectionRow>

                  {sorted.map((f) => {
                    const checked = selectedSources.has(f.key);
                    return (
                      <SelectionRow key={f.key} onClick={() => toggleSource(f.key)} paddingLeft={28}>
                        <Checkbox checked={checked} />
                        <span title={f.key} style={{
                          overflow: 'hidden', textOverflow: 'ellipsis', whiteSpace: 'nowrap',
                          flex: 1, fontSize: 12, fontFamily: "'JetBrains Mono', monospace",
                          color: 'var(--text2)',
                        }}>
                          {f.displayName}
                        </span>
                      </SelectionRow>
                    );
                  })}
                </div>
              );
            })}
          </>
        ) : (
          /* Normal mode with antd Menu */
          <Menu
            mode="inline"
            theme="dark"
            selectedKeys={selectedKeys}
            onClick={handleMenuClick}
            items={buildMenuItems()}
            style={{
              background: 'transparent',
              borderInlineEnd: 'none',
              fontFamily: "'JetBrains Mono', monospace",
              fontSize: 12,
            }}
          />
        )}
      </div>

      {/* Bottom button */}
      {logSources.length > 0 && (
        <div style={{ padding: '0 8px 8px' }}>
          <Button
            block
            type={btnType}
            danger={btnDanger}
            onClick={handleCustomViewClick}
            size="small"
            style={{ fontSize: 12 }}
          >
            {btnLabel}
          </Button>
        </div>
      )}
    </div>
  );
}

// -- Sub-component for selection mode rows --

function SelectionRow({ children, onClick, paddingLeft }: {
  children: React.ReactNode;
  onClick: () => void;
  paddingLeft: number;
}) {
  return (
    <div
      onClick={onClick}
      style={{
        display: 'flex', alignItems: 'center', gap: 8,
        padding: `5px 8px 5px ${paddingLeft}px`,
        borderRadius: 6, cursor: 'pointer', transition: 'background 0.1s',
      }}
      onMouseEnter={(e) => { e.currentTarget.style.background = 'var(--hover)'; }}
      onMouseLeave={(e) => { e.currentTarget.style.background = ''; }}
    >
      {children}
    </div>
  );
}
