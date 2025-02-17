import { useCreateStripeCheckoutSession } from "#/hooks/mutation/stripe/use-create-stripe-checkout-session";
import { useBalance } from "#/hooks/query/use-balance";
import { cn } from "#/utils/utils";
import MoneyIcon from "#/icons/money.svg?react";
import { SettingsInput } from "../settings/settings-input";
import { BrandButton } from "../settings/brand-button";
import { HelpLink } from "../settings/help-link";

export function PaymentForm() {
  const { data: balance } = useBalance();
  const { mutate: addBalance } = useCreateStripeCheckoutSession();

  const billingFormAction = async (formData: FormData) => {
    const amount = formData.get("top-up-input")?.toString();

    if (amount?.trim()) {
      const float = parseFloat(amount);
      if (Number.isNaN(float)) return;
      if (float < 0) return;
      if (float < 25) return;

      addBalance({ amount: Number(float.toFixed(2)) });
    }
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
          "flex justify-between w-[680px] bg-[#7F7445] rounded px-3 py-2",
          "text-[28px] leading-8 -tracking-[0.02em] font-bold",
        )}
      >
        <div className="flex items-center gap-2">
          <MoneyIcon width={22} height={14} />
          <span>Balance</span>
        </div>
        <span data-testid="user-balance">${Number(balance).toFixed(2)}</span>
      </div>

      <div className="flex flex-col gap-3">
        <SettingsInput
          testId="top-up-input"
          name="top-up-input"
          type="text"
          label="Top-up amount"
          placeholder="Enter amount"
          className="w-[680px]"
        />
        <BrandButton variant="primary" type="submit">
          Add credit
        </BrandButton>
      </div>

      <HelpLink
        testId="payment-methods-link"
        href="https://stripe.com/"
        text="Manage payment methods on"
        linkText="Stripe"
      />
    </form>
  );
}
