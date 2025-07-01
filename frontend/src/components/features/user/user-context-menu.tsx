import React from "react";
import ReactDOM from "react-dom";
import { useNavigate } from "react-router";
import { useLogout } from "#/hooks/mutation/use-logout";
import { CreateNewOrganizationModal } from "../org/create-new-organization-modal";

type UserRole = "user" | "admin" | "superadmin";

interface UserContextMenuProps {
  type: UserRole;
}

export function UserContextMenu({ type }: UserContextMenuProps) {
  const navigate = useNavigate();
  const { mutate: logout } = useLogout();

  const [orgModalIsOpen, setOrgModalIsOpen] = React.useState(false);

  const isUser = type === "user";
  const isSuperAdmin = type === "superadmin";

  return (
    <div>
      {orgModalIsOpen &&
        ReactDOM.createPortal(
          <CreateNewOrganizationModal
            onCancel={() => setOrgModalIsOpen(false)}
          />,
          document.getElementById("root-outlet") || document.body,
        )}

      <button type="button" onClick={() => logout()}>
        Logout
      </button>
      <button type="button" onClick={() => navigate("/settings")}>
        Settings
      </button>
      {!isUser && (
        <>
          <button type="button" onClick={() => navigate("/settings/team")}>
            Manage Team
          </button>
          <button type="button" onClick={() => navigate("/settings/org")}>
            Manage Account
          </button>
        </>
      )}
      {isSuperAdmin && (
        <button type="button" onClick={() => setOrgModalIsOpen(true)}>
          Create New Organization
        </button>
      )}
    </div>
  );
}
