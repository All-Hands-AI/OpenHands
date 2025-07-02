import React from "react";
import ReactDOM from "react-dom";
import { InviteOrganizationMemberModal } from "#/components/features/org/invite-organization-member-modal";
import { useOrganizationMembers } from "#/hooks/query/use-organization-members";
import { OrganizationUserRole } from "#/types/org";
import { OrganizationMemberListItem } from "#/components/features/org/organization-member-list-item";
import { useUpdateMemberRole } from "#/hooks/mutation/use-update-member-role";
import { useMe } from "#/hooks/query/use-me";

export function ManageTeam() {
  const { data: organizationMembers } = useOrganizationMembers();
  const { data: user } = useMe();
  const { mutate: updateMemberRole } = useUpdateMemberRole();

  const [inviteModalOpen, setInviteModalOpen] = React.useState(false);

  const handleRoleSelectionClick = (id: string, role: OrganizationUserRole) => {
    updateMemberRole({ userId: id, role });
  };

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
              <OrganizationMemberListItem
                email={member.email}
                role={member.role}
                hasPermissionToChangeRole={user?.role !== "user"}
                onRoleChange={(role) =>
                  handleRoleSelectionClick(member.id, role)
                }
              />
            </li>
          ))}
        </ul>
      )}
    </div>
  );
}
