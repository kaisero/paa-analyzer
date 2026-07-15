import { useMemo } from 'react';
import { Input, Radio, DatePicker, Button, Flex } from 'antd';
import { ClearOutlined } from '@ant-design/icons';
import dayjs, { type Dayjs } from 'dayjs';

const LEVELS = ['all', 'error', 'warning', 'info', 'debug'] as const;
const LEVEL_LABELS: Record<string, string> = {
  all: 'All',
  error: 'Error',
  warning: 'Warn',
  info: 'Info',
  debug: 'Debug',
};

interface LogToolbarProps {
  search: string;
  setSearch: (v: string) => void;
  level: string;
  setLevel: (v: string) => void;
  dateFrom: string | undefined;
  setDateFrom: (v: string | undefined) => void;
  dateTo: string | undefined;
  setDateTo: (v: string | undefined) => void;
  onClear: () => void;
  availableDateRange: { from: string | null; to: string | null };
}

export function LogToolbar({
  search,
  setSearch,
  level,
  setLevel,
  dateFrom,
  setDateFrom,
  dateTo,
  setDateTo,
  onClear,
  availableDateRange,
}: LogToolbarProps) {
  const rangeValue: [Dayjs | null, Dayjs | null] = [
    dateFrom ? dayjs(dateFrom) : null,
    dateTo ? dayjs(dateTo) : null,
  ];

  const minDate = useMemo(
    () => (availableDateRange.from ? dayjs(availableDateRange.from) : undefined),
    [availableDateRange.from],
  );
  const maxDate = useMemo(
    () => (availableDateRange.to ? dayjs(availableDateRange.to) : undefined),
    [availableDateRange.to],
  );

  const handleRangeChange = (values: [Dayjs | null, Dayjs | null] | null) => {
    if (!values) {
      setDateFrom(undefined);
      setDateTo(undefined);
      return;
    }
    setDateFrom(values[0] ? values[0].toISOString() : undefined);
    setDateTo(values[1] ? values[1].toISOString() : undefined);
  };

  const disabledDate = (current: Dayjs) => {
    if (minDate && current.isBefore(minDate, 'day')) return true;
    if (maxDate && current.isAfter(maxDate, 'day')) return true;
    return false;
  };

  return (
    <Flex
      gap={8}
      align="center"
      style={{
        padding: '8px 16px',
        borderBottom: '1px solid var(--border)',
        background: 'var(--surface)',
        flexShrink: 0,
      }}
    >
      {/* Search */}
      <Input.Search
        value={search}
        onChange={(e) => setSearch(e.target.value)}
        placeholder="Search..."
        allowClear
        size="small"
        style={{
          flex: 1,
          minWidth: 160,
          fontFamily: "'JetBrains Mono', monospace",
          fontSize: 12,
        }}
      />

      {/* Level filter */}
      <Radio.Group
        value={level}
        onChange={(e) => setLevel(e.target.value)}
        size="small"
        optionType="button"
        buttonStyle="solid"
      >
        {LEVELS.map((l) => (
          <Radio.Button key={l} value={l} style={{ fontSize: 11 }}>
            {LEVEL_LABELS[l]}
          </Radio.Button>
        ))}
      </Radio.Group>

      {/* Date range picker */}
      <DatePicker.RangePicker
        value={rangeValue[0] || rangeValue[1] ? rangeValue : null}
        onChange={handleRangeChange}
        showTime={{ format: 'HH:mm' }}
        format="YYYY-MM-DD HH:mm"
        disabledDate={disabledDate}
        size="small"
        style={{ minWidth: 360, fontFamily: "'JetBrains Mono', monospace", fontSize: 12 }}
        placeholder={['Start date', 'End date']}
      />

      {/* Clear */}
      <Button
        size="small"
        icon={<ClearOutlined />}
        onClick={onClear}
        style={{ fontSize: 11 }}
      >
        Clear
      </Button>
    </Flex>
  );
}
