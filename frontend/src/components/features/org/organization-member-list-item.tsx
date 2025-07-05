import React from "react";
import { ChevronDown } from "lucide-react";
import { OrganizationMember, OrganizationUserRole } from "#/types/org";

interface OrganizationMemberListItemProps {
  email: OrganizationMember["email"];
  role: OrganizationMember["role"];
  hasPermissionToChangeRole: boolean;

  onRoleChange: (role: OrganizationUserRole) => void;
}

export function OrganizationMemberListItem({
  email,
  role,
  hasPermissionToChangeRole,
  onRoleChange,
}: OrganizationMemberListItemProps) {
  const [roleSelectionOpen, setRoleSelectionOpen] = React.useState(false);

  const handleRoleSelectionClick = (newRole: OrganizationUserRole) => {
    onRoleChange(newRole);
    setRoleSelectionOpen(false);
  };

  return (
    <div className="flex items-center justify-between py-4">
      <span className="text-sm font-semibold">{email}</span>
      <span
        onClick={() => setRoleSelectionOpen(true)}
        className="text-xs text-gray-400 uppercase flex items-center gap-1 cursor-pointer"
      >
        {role}
        {hasPermissionToChangeRole && <ChevronDown size={14} />}
      </span>

      {hasPermissionToChangeRole && roleSelectionOpen && (
        <ul data-testid="role-dropdown">
          <li>
            <span onClick={() => handleRoleSelectionClick("admin")}>admin</span>
          </li>
          <li>
            <span onClick={() => handleRoleSelectionClick("user")}>user</span>
          </li>
        </ul>
      )}
    </div>
  );
}
