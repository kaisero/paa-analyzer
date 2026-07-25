import { useState, useRef, useEffect, useCallback } from 'react';
import { AutoComplete, Segmented, Spin } from 'antd';
import { useParams } from 'react-router-dom';
import { useStateKeys, useStateEntry } from '../../api/hooks';

interface HistoryEntry {
  command: string;
  stateKey: string;
}

export function PacliTerminal() {
  const { sessionId } = useParams<{ sessionId: string }>();
  const { data: keysData } = useStateKeys(sessionId);

  const [input, setInput] = useState('');
  const [history, setHistory] = useState<HistoryEntry[]>([]);
  const [activeEntry, setActiveEntry] = useState<HistoryEntry | null>(null);
  const [viewMode, setViewMode] = useState<'Raw' | 'JSON'>('Raw');
  const outputRef = useRef<HTMLDivElement>(null);

  // Build autocomplete options from state keys that have a pacli_command
  const pacliCommands = (keysData?.data ?? [])
    .filter((k) => k.pacli_command)
    .map((k) => ({ command: k.pacli_command!, stateKey: k.key }));

  const autocompleteOptions = pacliCommands
    .filter((c) => {
      if (!input) return true;
      const needle = input.toLowerCase();
      return c.command.toLowerCase().includes(needle);
    })
    .map((c) => ({ value: c.command, label: c.command }));

  // Fetch state data for the active entry
  const { data: stateData, isLoading: stateLoading } = useStateEntry(
    sessionId,
    activeEntry?.stateKey,
  );

  // Scroll to bottom when new output appears
  useEffect(() => {
    if (outputRef.current) {
      outputRef.current.scrollTop = outputRef.current.scrollHeight;
    }
  }, [history, stateData]);

  const handleSelect = useCallback((value: string) => {
    const match = pacliCommands.find((c) => c.command === value);
    if (match) {
      const entry = { command: match.command, stateKey: match.stateKey };
      setHistory((prev) => [...prev, entry]);
      setActiveEntry(entry);
      setInput('');
    }
  }, [pacliCommands]);

  const handleKeyDown = useCallback((e: React.KeyboardEvent) => {
    if (e.key === 'Enter') {
      const trimmed = input.trim();
      if (!trimmed) return;
      // Try exact match first, then partial
      const match = pacliCommands.find((c) => c.command === trimmed)
        || pacliCommands.find((c) => c.command.includes(trimmed));
      if (match) {
        handleSelect(match.command);
      }
    }
  }, [input, pacliCommands, handleSelect]);

  const renderOutput = (isActive: boolean) => {
    if (isActive && stateLoading) {
      return <Spin size="small" style={{ marginLeft: 8 }} />;
    }

    const data = isActive ? stateData?.data : undefined;
    if (!data) return null;

    if (viewMode === 'Raw') {
      if (data.raw_text) {
        return (
          <pre style={{ margin: '4px 0 16px 0', whiteSpace: 'pre-wrap', color: 'var(--text-sec)', fontSize: 12 }}>
            {data.raw_text}
          </pre>
        );
      }
      return (
        <div style={{ margin: '4px 0 16px 0', color: 'var(--text-dim)', fontSize: 11, fontStyle: 'italic' }}>
          Raw text not available — re-upload bundle to enable
        </div>
      );
    }

    // JSON mode
    return (
      <pre style={{ margin: '4px 0 16px 0', whiteSpace: 'pre-wrap', color: 'var(--text-sec)', fontSize: 12 }}>
        {JSON.stringify(data.data, null, 2)}
      </pre>
    );
  };

  return (
    <div>
      <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', marginBottom: 12 }}>
        <div style={{ fontSize: 13, fontWeight: 600, color: 'var(--text)' }}>
          PACli Terminal
        </div>
        <Segmented
          size="small"
          options={['Raw', 'JSON']}
          value={viewMode}
          onChange={(v) => setViewMode(v as 'Raw' | 'JSON')}
        />
      </div>

      {/* Terminal output area */}
      <div
        ref={outputRef}
        style={{
          background: 'var(--bg)',
          border: '1px solid var(--border)',
          borderRadius: 0,
          padding: 16,
          fontFamily: '"JetBrains Mono", monospace',
          fontSize: 12,
          color: 'var(--text)',
          maxHeight: 600,
          overflowY: 'auto',
          minHeight: 'calc(20 * 1.5em + 32px)',
        }}
      >
        {/* Welcome message */}
        {history.length === 0 && (
          <div style={{ color: 'var(--text-dim)', marginBottom: 8 }}>
            Type a pacli command to view its output. Use autocomplete to browse available commands.
          </div>
        )}

        {/* Command history */}
        {history.map((entry, idx) => {
          const isActive = idx === history.length - 1 && entry.stateKey === activeEntry?.stateKey;
          return (
            <div key={idx}>
              <div style={{ color: 'var(--ok)' }}>
                <span style={{ color: 'var(--accent)', marginRight: 8 }}>$</span>
                {entry.command}
              </div>
              {renderOutput(isActive)}
            </div>
          );
        })}

        {/* Input line */}
        <div style={{ display: 'flex', alignItems: 'center', gap: 8 }}>
          <span style={{ color: 'var(--accent)', flexShrink: 0 }}>$</span>
          <AutoComplete
            value={input}
            onChange={setInput}
            onSelect={handleSelect}
            onKeyDown={handleKeyDown}
            options={autocompleteOptions}
            placeholder="pacli ..."
            variant="borderless"
            popupMatchSelectWidth={300}
            style={{ flex: 1 }}
            styles={{ input: {
              fontFamily: '"JetBrains Mono", monospace',
              fontSize: 12,
              color: 'var(--text)',
              padding: 0,
              background: 'transparent',
            }}}
          />
        </div>
      </div>
    </div>
  );
}
