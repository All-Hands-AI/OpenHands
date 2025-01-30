interface UserBalanceProps {
  balance: number;
  isLoading: boolean;
  onTopUp: () => void;
}

export function UserBalance({ balance, isLoading, onTopUp }: UserBalanceProps) {
  return (
    <div className="flex items-center justify-between">
      <div className="flex items-center gap-2">
        <span className="font-bold">Balance</span>
        {!isLoading && (
          <button
            type="button"
            className="text-xs font-semibold border rounded-md px-2 py-0.5"
            onClick={onTopUp}
          >
            Top up
          </button>
        )}
        {isLoading && <span className="text-xs font-semibold">Loading...</span>}
      </div>
      <span data-testid="current-balance">${balance.toFixed(2)}</span>
    </div>
  );
}
