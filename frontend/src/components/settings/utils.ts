export const isDifferent = (
  a: Record<string, string>,
  b: Record<string, string>,
): boolean => JSON.stringify(a) !== JSON.stringify(b);
