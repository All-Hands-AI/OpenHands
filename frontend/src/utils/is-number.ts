export const isNumber = (value: string | number): boolean =>
  !Number.isNaN(Number(value));
