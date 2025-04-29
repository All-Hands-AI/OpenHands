const MINIMUM_AMOUNT = 10;
const MAXIMUM_AMOUNT = 25_000;

export const amountIsValid = (amount: string) => {
  const value = parseInt(amount, 10);
  if (Number.isNaN(value)) return false;
  if (value < 0) return false;
  if (value < MINIMUM_AMOUNT) return false;
  if (value > MAXIMUM_AMOUNT) return false;
  if (value !== parseFloat(amount)) return false; // Ensure it's an integer

  return true;
};
