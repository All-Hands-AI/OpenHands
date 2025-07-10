import { ModalBackdrop } from "#/components/shared/modals/modal-backdrop";
import { useInviteOrganizationMember } from "#/hooks/mutation/use-invite-organization-member";
import { BrandButton } from "../settings/brand-button";
import { SettingsInput } from "../settings/settings-input";

interface InviteOrganizationMemberModalProps {
  onClose: (event?: React.MouseEvent<HTMLButtonElement>) => void;
}

export function InviteOrganizationMemberModal({
  onClose,
}: InviteOrganizationMemberModalProps) {
  const { mutate: inviteMember } = useInviteOrganizationMember();

  const formAction = (formData: FormData) => {
    const email = formData.get("email-input")?.toString();
    if (email) {
      inviteMember({ email });
      onClose();
    }
  };

  return (
    <ModalBackdrop onClose={onClose}>
      <div
        data-testid="invite-modal"
        className="bg-base rounded-xl p-4 border w-sm border-tertiary items-start"
        onClick={(e) => e.stopPropagation()}
      >
        <form action={formAction} className="w-full flex flex-col gap-6">
          <div className="flex flex-col gap-2">
            <h3 className="text-lg font-semibold">Invite Users</h3>
            <p className="text-xs text-gray-400">
              Invite colleaguess using their email address
            </p>
            <SettingsInput
              testId="email-input"
              name="email-input"
              label="Email"
              type="email"
              placeholder="Type email and press enter"
              className="w-full"
              required
            />
          </div>

          <div className="flex gap-2">
            <BrandButton type="submit" variant="primary" className="flex-1">
              Next
            </BrandButton>
            <BrandButton
              type="button"
              variant="secondary"
              onClick={onClose}
              className="flex-1"
            >
              Skip
            </BrandButton>
          </div>
        </form>
      </div>
    </ModalBackdrop>
  );
}
