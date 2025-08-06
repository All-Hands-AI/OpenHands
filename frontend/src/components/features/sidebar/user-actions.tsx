import React from "react";
import { UserAvatar } from "./user-avatar";
import { AccountSettingsContextMenu } from "../context-menu/account-settings-context-menu";
import { useIsAuthed } from "#/hooks/query/use-is-authed";
import { useConfig } from "#/hooks/query/use-config";
import { useUserProviders } from "#/hooks/use-user-providers";

interface UserActionsProps {
  onLogout: () => void;
  user?: { avatar_url: string };
  isLoading?: boolean;
}

export function UserActions({ onLogout, user, isLoading }: UserActionsProps) {
  const { data: config } = useConfig();
  const { data: isAuthed } = useIsAuthed();
  const { providers } = useUserProviders();
  const [accountContextMenuIsVisible, setAccountContextMenuIsVisible] =
    React.useState(false);

  // Check if user should have access based on auth and provider configuration
  const shouldShowUserActions = React.useMemo(() => {
    if (!config?.APP_MODE || !isAuthed) return false;

    // In OSS mode, only show user actions if Git providers are configured
    if (config.APP_MODE === "oss") {
      return providers.length > 0;
    }

    // In non-OSS modes (saas), always show user actions when authenticated
    return true;
  }, [config?.APP_MODE, isAuthed, providers.length]);

  const toggleAccountMenu = () => {
    // Always toggle the menu, even if user is undefined
    setAccountContextMenuIsVisible((prev) => !prev);
  };

  const closeAccountMenu = () => {
    setAccountContextMenuIsVisible(false);
  };

  const handleLogout = () => {
    onLogout();
    closeAccountMenu();
  };

  // Show the menu based on the new logic
  const showMenu = accountContextMenuIsVisible && shouldShowUserActions;

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
