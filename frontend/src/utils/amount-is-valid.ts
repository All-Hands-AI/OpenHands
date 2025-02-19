const MINIMUM_AMOUNT = 25;

export const amountIsValid = (amount: string) => {
  const float = parseFloat(amount);
  if (Number.isNaN(float)) return false;
  if (float < 0) return false;
  if (float < MINIMUM_AMOUNT) return false;

  return true;
};
