import { useMutation } from "@tanstack/react-query";
import OpenHands from "#/api/open-hands";
import { useBalance } from "#/hooks/query/use-balance";
import { StripeCheckoutForm } from "./stripe-checkout-form";

interface UserBalanceProps {
  user: string;
}

export function UserBalance({ user }: UserBalanceProps) {
  const { data: balance } = useBalance(user);
  const {
    data: clientSecret,
    mutate: getClientSecret,
    isPending: isGettingClientSecret,
  } = useMutation({
    mutationFn: OpenHands.createCheckoutSession,
  });

  return (
    <>
      {balance && (
        <div className="flex items-center justify-between">
          <div className="flex items-center gap-2">
            <span className="font-bold">Balance</span>
            {!isGettingClientSecret && (
              <button
                type="button"
                className="text-xs font-semibold border rounded-md px-2 py-0.5"
                onClick={() => getClientSecret()}
              >
                Top up
              </button>
            )}
            {isGettingClientSecret && (
              <span className="text-xs font-semibold">Loading...</span>
            )}
          </div>
          <span data-testid="current-balance">${balance.toFixed(2)}</span>
        </div>
      )}
      {clientSecret && <StripeCheckoutForm clientSecret={clientSecret} />}
    </>
  );
}
