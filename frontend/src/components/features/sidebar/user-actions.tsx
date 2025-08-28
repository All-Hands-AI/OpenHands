import React from "react";
import { UserAvatar } from "./user-avatar";
import { AccountSettingsContextMenu } from "../context-menu/account-settings-context-menu";
import { useShouldShowUserFeatures } from "#/hooks/use-should-show-user-features";

interface UserActionsProps {
  onLogout: () => void;
  user?: { avatar_url: string };
  isLoading?: boolean;
}

export function UserActions({ onLogout, user, isLoading }: UserActionsProps) {
  // Use the shared hook to determine if user actions should be shown
  const shouldShowUserActions = useShouldShowUserFeatures();

  const handleLogout = () => {
    onLogout();
  };

  return (
    <div
      data-testid="user-actions"
      className="w-8 h-8 relative cursor-pointer group"
    >
      <UserAvatar avatarUrl={user?.avatar_url} isLoading={isLoading} />

      {shouldShowUserActions && (
        <div className="opacity-0 group-hover:opacity-100 pointer-events-none group-hover:pointer-events-auto">
          <AccountSettingsContextMenu onLogout={handleLogout} />
        </div>
      )}
    </div>
  );
}
