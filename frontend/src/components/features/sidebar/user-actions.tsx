import React from "react";
import { UserAvatar } from "./user-avatar";
import { AccountSettingsContextMenu } from "../context-menu/account-settings-context-menu";

interface UserActionsProps {
  onClickAccountSettings: () => void;
  onLogout: () => void;
  user?: { avatar_url: string };
}

export function UserActions({
  onClickAccountSettings,
  onLogout,
  user,
}: UserActionsProps) {
  const [accountContextMenuIsVisible, setAccountContextMenuIsVisible] =
    React.useState(false);

  const toggleAccountMenu = () => {
    setAccountContextMenuIsVisible((prev) => !prev);
  };

  const closeAccountMenu = () => {
    setAccountContextMenuIsVisible(false);
  };

  const handleClickAccountSettings = () => {
    onClickAccountSettings();
    closeAccountMenu();
  };

  const handleLogout = () => {
    onLogout();
    closeAccountMenu();
  };

  return (
    <div data-testid="user-actions" className="w-8 h-8 relative">
      <UserAvatar avatarUrl={user?.avatar_url} onClick={toggleAccountMenu} />

      {accountContextMenuIsVisible && (
        <AccountSettingsContextMenu
          isLoggedIn={!!user}
          onClickAccountSettings={handleClickAccountSettings}
          onLogout={handleLogout}
          onClose={closeAccountMenu}
        />
      )}
    </div>
  );
}
