import React from "react";
import ReactDOM from "react-dom";
import { Plus } from "lucide-react";
import { InviteOrganizationMemberModal } from "#/components/features/org/invite-organization-member-modal";
import { useOrganizationMembers } from "#/hooks/query/use-organization-members";
import { OrganizationUserRole } from "#/types/org";
import { OrganizationMemberListItem } from "#/components/features/org/organization-member-list-item";
import { useUpdateMemberRole } from "#/hooks/mutation/use-update-member-role";
import { useMe } from "#/hooks/query/use-me";
import { BrandButton } from "#/components/features/settings/brand-button";

const superadminPerms = ["superadmin", "admin", "user"];
const adminPerms = ["admin", "user"];
const userPerms: string[] = [];

const rolePermissions: Record<OrganizationUserRole, string[]> = {
  superadmin: superadminPerms,
  admin: adminPerms,
  user: userPerms,
};

function ManageTeam() {
  const { data: organizationMembers } = useOrganizationMembers();
  const { data: user } = useMe();
  const { mutate: updateMemberRole } = useUpdateMemberRole();

  const [inviteModalOpen, setInviteModalOpen] = React.useState(false);

  const handleRoleSelectionClick = (id: string, role: OrganizationUserRole) => {
    updateMemberRole({ userId: id, role });
  };

  const checkIfUserHasPermissionToChangeRole = (
    memberRole: OrganizationUserRole,
  ) => {
    if (!user) return false;

    const userRole = user.role;
    const userPermissions = rolePermissions[userRole] || [];

    return userPermissions.includes(memberRole);
  };

  return (
    <div className="p-4 flex flex-col gap-2">
      <BrandButton
        type="button"
        variant="secondary"
        onClick={() => setInviteModalOpen(true)}
        className="flex items-center gap-1"
      >
        <Plus size={14} />
        Invite Team
      </BrandButton>

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
            <li
              key={member.id}
              data-testid="member-item"
              className="border-b border-tertiary"
            >
              <OrganizationMemberListItem
                email={member.email}
                role={member.role}
                status={member.status}
                hasPermissionToChangeRole={checkIfUserHasPermissionToChangeRole(
                  member.role,
                )}
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

export default ManageTeam;
