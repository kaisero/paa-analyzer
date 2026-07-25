import { useState, useRef, useEffect, useCallback } from 'react';
import { AutoComplete, Segmented, Spin } from 'antd';
import { useParams } from 'react-router-dom';
import { useStateKeys, useStateEntry } from '../../api/hooks';

interface ActiveEntry {
  command: string;
  stateKey: string;
}

export function PacliTerminal() {
  const { sessionId } = useParams<{ sessionId: string }>();
  const { data: keysData } = useStateKeys(sessionId);

  const [input, setInput] = useState('');
  const [activeEntry, setActiveEntry] = useState<ActiveEntry | null>(null);
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

  // Scroll to top when a new command is run
  useEffect(() => {
    if (outputRef.current) {
      outputRef.current.scrollTop = 0;
    }
  }, [activeEntry]);

  const handleSelect = useCallback((value: string) => {
    const match = pacliCommands.find((c) => c.command === value);
    if (match) {
      setActiveEntry({ command: match.command, stateKey: match.stateKey });
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

  const renderOutput = () => {
    if (stateLoading) {
      return <Spin size="small" style={{ marginLeft: 8 }} />;
    }

    const data = stateData?.data;
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
        {!activeEntry && (
          <div style={{ color: 'var(--text-dim)', marginBottom: 8 }}>
            Type a pacli command to view its output. Use autocomplete to browse available commands.
          </div>
        )}

        {/* Current command + output */}
        {activeEntry && (
          <div>
            <div style={{ color: 'var(--ok)', marginBottom: 4 }}>
              <span style={{ color: 'var(--accent)', marginRight: 8 }}>$</span>
              {activeEntry.command}
            </div>
            {renderOutput()}
          </div>
        )}

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
