import React from "react";
import { useCreateStripeCheckoutSession } from "#/hooks/mutation/stripe/use-create-stripe-checkout-session";
import { useOrganization } from "#/hooks/query/use-organization";
import { useOrganizationPaymentInfo } from "#/hooks/query/use-organization-payment-info";
import { ModalBackdrop } from "#/components/shared/modals/modal-backdrop";
import { cn } from "#/utils/utils";

function TempChip({
  children,
  ...props
}: React.PropsWithChildren<{ "data-testid": string }>) {
  return (
    <div
      // eslint-disable-next-line react/jsx-props-no-spreading
      {...props}
      style={{ minWidth: "100px" }}
      data-openhands-chip
      className="bg-[#FFE165] px-4 rounded-[100px] text-black text-lg text-center font-semibold"
    >
      {children}
    </div>
  );
}

interface TempInteractiveChipProps {
  onClick: () => void;
}

function TempInteractiveChip({
  children,
  onClick,
}: React.PropsWithChildren<TempInteractiveChipProps>) {
  return (
    <div
      onClick={onClick}
      className="bg-[#E4E4E4] px-2 rounded-[100px] text-black text-sm text-center font-semibold cursor-pointer"
    >
      {children}
    </div>
  );
}

function TempButton({
  children,
  onClick,
  type,
  variant = "primary",
}: React.PropsWithChildren<{
  onClick?: () => void;
  type: "button" | "submit";
  variant?: "primary" | "secondary";
}>) {
  return (
    <button
      className={cn(
        "flex-1 py-3 rounded text-sm text-center font-semibold cursor-pointer",
        variant === "primary" && "bg-[#F3CE49] text-black",
        variant === "secondary" && "bg-[#737373] text-white",
      )}
      type={type}
      onClick={onClick}
    >
      {children}
    </button>
  );
}

interface AddCreditsModalProps {
  onClose: () => void;
}

function AddCreditsModal({ onClose }: AddCreditsModalProps) {
  const { mutate: addBalance } = useCreateStripeCheckoutSession();

  const formAction = (formData: FormData) => {
    const amount = formData.get("amount")?.toString();

    if (amount?.trim()) {
      const intValue = parseInt(amount, 10);
      addBalance({ amount: intValue }, { onSuccess: onClose });
    }
  };

  return (
    <ModalBackdrop>
      <form
        data-testid="add-credits-form"
        action={formAction}
        className="w-sm rounded-xl bg-[#171717] flex flex-col p-6 gap-6"
      >
        <div className="flex flex-col gap-2">
          <h3 className="text-xl font-semibold">Add Credits</h3>
          <input
            data-testid="amount-input"
            name="amount"
            type="number"
            className="text-lg bg-[#27272A] p-2"
          />
        </div>

        <div className="flex gap-2">
          <TempButton type="submit">Next</TempButton>
          <TempButton type="button" onClick={onClose} variant="secondary">
            Cancel
          </TempButton>
        </div>
      </form>
    </ModalBackdrop>
  );
}

function ManageOrg() {
  const { data: organization } = useOrganization({ orgId: "1" });
  const { data: organizationPaymentInfo } = useOrganizationPaymentInfo({
    orgId: "1",
  });

  const [addCreditsFormVisible, setAddCreditsFormVisible] =
    React.useState(false);

  return (
    <div>
      <div className="flex items-center gap-2">
        <TempChip data-testid="available-credits">
          {organization?.balance}
        </TempChip>
        <TempInteractiveChip onClick={() => setAddCreditsFormVisible(true)}>
          + Add
        </TempInteractiveChip>
      </div>
      {addCreditsFormVisible && (
        <AddCreditsModal onClose={() => setAddCreditsFormVisible(false)} />
      )}
      <div data-testid="org-name">{organization?.name}</div>
      <div data-testid="billing-info">
        {organizationPaymentInfo?.cardNumber}
      </div>
    </div>
  );
}

export default ManageOrg;
