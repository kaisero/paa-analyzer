import { Pagination, Select, Typography, Flex } from 'antd';

const PAGE_SIZES = [100, 250, 500] as const;

/** Shared with the sidebar's footer bar so the two align. */
export const FOOTER_BAR_HEIGHT = 37;

interface LogPaginationProps {
  page: number;
  pageSize: number;
  total: number;
  hasNext: boolean;
  onPageChange: (page: number) => void;
  onPageSizeChange: (size: number) => void;
}

export function LogPagination({
  page,
  pageSize,
  total,
  onPageChange,
  onPageSizeChange,
}: LogPaginationProps) {
  if (total === 0) return null;

  const start = pageSize === 0 ? 1 : (page - 1) * pageSize + 1;
  const end = pageSize === 0 ? total : Math.min(page * pageSize, total);

  return (
    <Flex
      justify="space-between"
      align="center"
      style={{
        // Matched to the sidebar's footer bar so the two line up along the
        // bottom of the screen. Taken from the shorter of the two.
        height: FOOTER_BAR_HEIGHT,
        padding: '0 16px',
        background: 'var(--surface)',
        borderTop: '1px solid var(--border)',
        flexShrink: 0,
        fontSize: 12,
      }}
    >
      {/* Left: antd Pagination */}
      <Flex align="center" gap={12}>
        {pageSize > 0 ? (
          <Pagination
            current={page}
            total={total}
            pageSize={pageSize}
            onChange={onPageChange}
            showSizeChanger={false}
            size="small"
            simple
          />
        ) : (
          <Typography.Text type="secondary" style={{ fontSize: 12 }}>
            Showing all {total.toLocaleString()} entries
          </Typography.Text>
        )}
        <Typography.Text type="secondary" style={{ fontSize: 11 }}>
          {start.toLocaleString()}&ndash;{end.toLocaleString()} of {total.toLocaleString()}
        </Typography.Text>
      </Flex>

      {/* Right: page size selector */}
      <Flex align="center" gap={8}>
        <Typography.Text type="secondary" style={{ fontSize: 11 }}>
          Per page:
        </Typography.Text>
        <Select
          value={pageSize}
          onChange={onPageSizeChange}
          size="small"
          style={{ width: 80, fontSize: 11 }}
          options={[
            ...PAGE_SIZES.map((s) => ({ value: s, label: String(s) })),
            { value: 0, label: 'All' },
          ]}
        />
      </Flex>
    </Flex>
  );
}
