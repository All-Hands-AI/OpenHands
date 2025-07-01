import { useInviteOrganizationMember } from "#/hooks/mutation/use-invite-organization-member";

interface InviteOrganizationMemberModalProps {
  onClose: () => void;
}

export function InviteOrganizationMemberModal({
  onClose,
}: InviteOrganizationMemberModalProps) {
  const { mutate: inviteMember } = useInviteOrganizationMember();

  const formAction = (formData: FormData) => {
    const email = formData.get("email-input")?.toString();
    if (email) inviteMember({ email });
  };

  return (
    <div data-testid="invite-modal">
      <form action={formAction}>
        <label>
          Email
          <input data-testid="email-input" name="email-input" type="text" />
        </label>
        <button type="button" onClick={onClose}>
          Close
        </button>
        <button type="submit">Submit</button>
      </form>
    </div>
  );
}
