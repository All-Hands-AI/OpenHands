import React from "react";
import { UserAvatar } from "./user-avatar";
import { AccountSettingsContextMenu } from "../context-menu/account-settings-context-menu";
import { useIsAuthed } from "#/hooks/query/use-is-authed";

interface UserActionsProps {
  onLogout: () => void;
  user?: { avatar_url: string };
  isLoading?: boolean;
}

export function UserActions({ onLogout, user, isLoading }: UserActionsProps) {
  const { data: isAuthed, isLoading: isAuthLoading } = useIsAuthed();
  const [accountContextMenuIsVisible, setAccountContextMenuIsVisible] =
    React.useState(false);

  const toggleAccountMenu = () => {
    setAccountContextMenuIsVisible((prev) => !prev);
  };

  const closeAccountMenu = () => {
    setAccountContextMenuIsVisible(false);
  };

  const handleLogout = () => {
    onLogout();
    closeAccountMenu();
  };

  // For debugging - log authentication status
  React.useEffect(() => {
    console.log("Authentication status:", isAuthed);
    console.log("Auth loading:", isAuthLoading);
    console.log("User data:", user);
    console.log("Menu visible:", accountContextMenuIsVisible);
  }, [isAuthed, isAuthLoading, user, accountContextMenuIsVisible]);

  // Always show the menu for authenticated users, even without user data
  const showMenu = accountContextMenuIsVisible && isAuthed === true;

  return (
    <div data-testid="user-actions" className="w-8 h-8 relative cursor-pointer">
      <UserAvatar
        avatarUrl={user?.avatar_url}
        onClick={toggleAccountMenu}
        isLoading={isLoading}
      />

      {showMenu && (
        <AccountSettingsContextMenu
          onLogout={handleLogout}
          onClose={closeAccountMenu}
        />
      )}
    </div>
  );
}
