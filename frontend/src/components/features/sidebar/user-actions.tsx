import React from "react";
import { UserAvatar } from "./user-avatar";
import { UserContextMenu } from "../user/user-context-menu";
import { useMe } from "#/hooks/query/use-me";

interface UserActionsProps {
  user?: { avatar_url: string };
  isLoading?: boolean;
}

export function UserActions({ user, isLoading }: UserActionsProps) {
  const { data: me } = useMe();
  const [accountContextMenuIsVisible, setAccountContextMenuIsVisible] =
    React.useState(false);

  const toggleAccountMenu = () => {
    setAccountContextMenuIsVisible((prev) => !prev);
  };

  const closeAccountMenu = () => {
    setAccountContextMenuIsVisible(false);
  };

  return (
    <div data-testid="user-actions" className="w-8 h-8 relative cursor-pointer">
      <UserAvatar
        avatarUrl={user?.avatar_url}
        onClick={toggleAccountMenu}
        isLoading={isLoading}
      />

      {accountContextMenuIsVisible && !!user && (
        <div className="w-sm absolute left-[calc(100%+12px)] bottom-0 z-10">
          <UserContextMenu
            type={me?.role || "user"}
            onClose={closeAccountMenu}
          />
        </div>
      )}
    </div>
  );
}
