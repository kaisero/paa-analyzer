import type { OpswatError } from '../../api/types';

/**
 * Every OPSWAT error belonging to a category.
 *
 * Derived from the cycle's flat `opswat_errors` list, NOT by summing each
 * product's `errors`. The GetMissingPatchesForThisProduct log line carries no
 * Signature field, so those errors resolve to no product: on the macOS fixture
 * the flat list holds 6 while the products between them hold only 4. Summing
 * product errors makes patch-management look error-free when it is not.
 */
export function categoryErrors(
  errors: OpswatError[],
  categoryName: string | null,
): OpswatError[] {
  return errors.filter((e) => e.category === categoryName);
}

/** Category errors that resolved to no product, so no ProductRow can show them. */
export function unattachedErrors(
  errors: OpswatError[],
  categoryName: string | null,
): OpswatError[] {
  return categoryErrors(errors, categoryName).filter((e) => e.product === null);
}
