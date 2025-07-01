import React from "react";
import ReactDOM from "react-dom";
import { InviteOrganizationMemberModal } from "#/components/features/org/invite-organization-member-modal";
import { useOrganizationMembers } from "#/hooks/query/use-organization-members";

export function ManageTeam() {
  const { data: organizationMembers } = useOrganizationMembers();
  const [inviteModalOpen, setInviteModalOpen] = React.useState(false);

  return (
    <div>
      <button type="button" onClick={() => setInviteModalOpen(true)}>
        Invite Team
      </button>

      {inviteModalOpen &&
        ReactDOM.createPortal(
          <InviteOrganizationMemberModal
            onClose={() => setInviteModalOpen(false)}
          />,
          document.getElementById("portal-root") || document.body,
        )}

      {organizationMembers && (
        <ul>
          {organizationMembers.map((member) => (
            <li key={member.id} data-testid="member-item">
              <span>{member.email}</span>
              <span>{member.role}</span>
            </li>
          ))}
        </ul>
      )}
    </div>
  );
}
