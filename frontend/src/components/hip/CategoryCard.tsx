import type { HipCategory } from '../../api/types';
import { StatusDot } from '../common/StatusDot';
import { HipCard } from './HipCard';
import { ProductRow } from './ProductRow';

interface Props {
  category: HipCategory;
  /** Seconds this category took to collect, if the cycle logged a timing. */
  timingS?: number;
}

export function CategoryCard({ category, timingS }: Props) {
  const count = category.products.length;

  return (
    <HipCard
      title={category.name ?? 'unnamed category'}
      bodyPadding={0}
      extra={
        <span
          style={{
            display: 'inline-flex',
            alignItems: 'center',
            gap: 8,
            fontFamily: 'var(--mono)',
            fontSize: 10,
            color: 'var(--text-dim)',
          }}
        >
          {timingS != null && timingS > 0 && <span>{timingS}s</span>}
          <span>
            {count} product{count === 1 ? '' : 's'}
          </span>
          <StatusDot status={category.status} reason={category.status_reason} />
        </span>
      }
    >
      {category.products.map((product, i) => (
        <ProductRow key={`${product.name ?? 'product'}-${i}`} product={product} divider={i > 0} />
      ))}
    </HipCard>
  );
}
