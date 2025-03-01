import React from "react";
import { useCreateStripeCheckoutSession } from "#/hooks/mutation/stripe/use-create-stripe-checkout-session";
import { useBalance } from "#/hooks/query/use-balance";
import { cn } from "#/utils/utils";
import MoneyIcon from "#/icons/money.svg?react";
import { SettingsInput } from "../settings/settings-input";
import { BrandButton } from "../settings/brand-button";
import { LoadingSpinner } from "#/components/shared/loading-spinner";
import { amountIsValid } from "#/utils/amount-is-valid";

export function PaymentForm() {
  const { data: balance, isLoading } = useBalance();
  const { mutate: addBalance, isPending } = useCreateStripeCheckoutSession();

  const [buttonIsDisabled, setButtonIsDisabled] = React.useState(true);

  const billingFormAction = async (formData: FormData) => {
    const amount = formData.get("top-up-input")?.toString();

    if (amount?.trim()) {
      if (!amountIsValid(amount)) return;

      const float = parseFloat(amount);
      addBalance({ amount: Number(float.toFixed(2)) });
    }

    setButtonIsDisabled(true);
  };

  const handleTopUpInputChange = (value: string) => {
    setButtonIsDisabled(!amountIsValid(value));
  };

  return (
    <form
      action={billingFormAction}
      data-testid="billing-settings"
      className="flex flex-col gap-6 px-11 py-9"
    >
      <h2 className="text-[28px] leading-8 tracking-[-0.02em] font-bold">
        Manage Credits
      </h2>

      <div
        className={cn(
          "flex items-center justify-between w-[680px] bg-[#7F7445] rounded px-3 py-2",
          "text-[28px] leading-8 -tracking-[0.02em] font-bold",
        )}
      >
        <div className="flex items-center gap-2">
          <MoneyIcon width={22} height={14} />
          <span>Balance</span>
        </div>
        {!isLoading && (
          <span data-testid="user-balance">${Number(balance).toFixed(2)}</span>
        )}
        {isLoading && <LoadingSpinner size="small" />}
      </div>

      <div className="flex flex-col gap-3">
        <SettingsInput
          testId="top-up-input"
          name="top-up-input"
          onChange={handleTopUpInputChange}
          type="text"
          label="Top-up amount"
          placeholder="Specify an amount to top up your credits"
          className="w-[680px]"
        />

        <div className="flex items-center w-[680px] gap-2">
          <BrandButton
            variant="primary"
            type="submit"
            isDisabled={isPending || buttonIsDisabled}
          >
            Add credit
          </BrandButton>
          {isPending && <LoadingSpinner size="small" />}
        </div>
      </div>
    </form>
  );
}
