import React from "react";
import { OrganizationMember, OrganizationUserRole } from "#/types/org";

interface OrganizationMemberListItemProps {
  email: OrganizationMember["email"];
  role: OrganizationMember["role"];

  onRoleChange: (role: OrganizationUserRole) => void;
}

export function OrganizationMemberListItem({
  email,
  role,
  onRoleChange,
}: OrganizationMemberListItemProps) {
  const [roleSelectionOpen, setRoleSelectionOpen] = React.useState(false);

  const handleRoleSelectionClick = (newRole: OrganizationUserRole) => {
    onRoleChange(newRole);
    setRoleSelectionOpen(false);
  };

  return (
    <div>
      <span>{email}</span>
      <span onClick={() => setRoleSelectionOpen(true)}>{role}</span>

      {roleSelectionOpen && (
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
