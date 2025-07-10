import React from "react";
import { useCreateStripeCheckoutSession } from "#/hooks/mutation/stripe/use-create-stripe-checkout-session";
import { useOrganization } from "#/hooks/query/use-organization";
import { useOrganizationPaymentInfo } from "#/hooks/query/use-organization-payment-info";

function ManageOrg() {
  const { data: organization } = useOrganization({ orgId: "1" });
  const { data: organizationPaymentInfo } = useOrganizationPaymentInfo({
    orgId: "1",
  });
  const { mutate: addBalance } = useCreateStripeCheckoutSession();

  const [addCreditsFormVisible, setAddCreditsFormVisible] =
    React.useState(false);

  const formAction = (formData: FormData) => {
    const amount = formData.get("amount")?.toString();

    if (amount?.trim()) {
      const intValue = parseInt(amount, 10);
      addBalance(
        { amount: intValue },
        { onSuccess: () => setAddCreditsFormVisible(false) },
      );
    }
  };

  return (
    <div>
      <div data-testid="available-credits">{organization?.balance}</div>
      <button type="button" onClick={() => setAddCreditsFormVisible(true)}>
        Add
      </button>
      {addCreditsFormVisible && (
        <form data-testid="add-credits-form" action={formAction}>
          <input name="amount" type="text" />
          <button type="submit">Next</button>
        </form>
      )}
      <div data-testid="org-name">{organization?.name}</div>
      <div data-testid="billing-info">
        {organizationPaymentInfo?.cardNumber}
      </div>
    </div>
  );
}

export default ManageOrg;
