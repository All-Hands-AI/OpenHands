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

type UserRoleChangePermissionKey = "change_user_role";
type InviteUserToOrganizationKey = "invite_user_to_organization";

type ChangeUserRolePermission =
  `${UserRoleChangePermissionKey}:${OrganizationUserRole}`;

type UserPermission = InviteUserToOrganizationKey | ChangeUserRolePermission;

const superadminPerms: UserPermission[] = [
  "invite_user_to_organization",
  "change_user_role:superadmin",
  "change_user_role:admin",
  "change_user_role:user",
];
const adminPerms: UserPermission[] = [
  "invite_user_to_organization",
  "change_user_role:admin",
  "change_user_role:user",
];
const userPerms: UserPermission[] = [];

const rolePermissions: Record<OrganizationUserRole, UserPermission[]> = {
  superadmin: superadminPerms,
  admin: adminPerms,
  user: userPerms,
};

function ManageTeam() {
  const { data: organizationMembers } = useOrganizationMembers();
  const { data: user } = useMe();
  const { mutate: updateMemberRole } = useUpdateMemberRole();

  const [inviteModalOpen, setInviteModalOpen] = React.useState(false);

  const currentUserRole = user?.role || "user";
  const hasPermissionToInvite = rolePermissions[currentUserRole].includes(
    "invite_user_to_organization",
  );

  const handleRoleSelectionClick = (id: string, role: OrganizationUserRole) => {
    updateMemberRole({ userId: id, role });
  };

  const checkIfUserHasPermissionToChangeRole = (
    memberRole: OrganizationUserRole,
  ) => {
    if (!user) return false;

    const userPermissions = rolePermissions[user.role];
    return userPermissions.includes(`change_user_role:${memberRole}`);
  };

  return (
    <div data-testid="manage-team-settings" className="p-4 flex flex-col gap-2">
      {hasPermissionToInvite && (
        <BrandButton
          type="button"
          variant="secondary"
          onClick={() => setInviteModalOpen(true)}
          className="flex items-center gap-1"
        >
          <Plus size={14} />
          Invite Team
        </BrandButton>
      )}

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
