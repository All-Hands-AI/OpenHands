import { useCreateStripeCheckoutSession } from "#/hooks/mutation/stripe/use-create-stripe-checkout-session";
import { useBalance } from "#/hooks/query/use-balance";

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
      className="flex flex-col gap-6"
    >
      <h2 className="text-[28px] leading-8 tracking-[-0.02em] font-bold">
        Manage Credits
      </h2>

      <p data-testid="user-balance">{balance}</p>
      <input data-testid="top-up-input" name="top-up-input" type="text" />
      <button type="submit">Add credit</button>
    </form>
  );
}
