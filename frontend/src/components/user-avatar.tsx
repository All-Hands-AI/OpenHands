import { cn } from "@nextui-org/react";
import React from "react";
import { isGitHubErrorReponse } from "#/api/github";
import { AccountSettingsContextMenu } from "./account-settings-context-menu";
import { LoadingSpinner } from "./modals/LoadingProject";
import DefaultUserAvatar from "#/assets/default-user.svg?react";

interface UserAvatarProps {
  isLoading: boolean;
  user: GitHubUser | GitHubErrorReponse | null;
  onLogout: () => void;
  handleOpenAccountSettingsModal: () => void;
}

export function UserAvatar({
  isLoading,
  user,
  onLogout,
  handleOpenAccountSettingsModal,
}: UserAvatarProps) {
  const [accountContextMenuIsVisible, setAccountContextMenuIsVisible] =
    React.useState(false);

  const validUser = user && !isGitHubErrorReponse(user);

  return (
    <div className="w-8 h-8 relative">
      <button
        type="button"
        className={cn(
          "bg-white w-8 h-8 rounded-full flex items-center justify-center",
          isLoading && "bg-transparent",
        )}
        onClick={() => {
          if (!user) {
            // If the user is not logged in, opening the modal is the only option,
            // so we do that instead of toggling the context menu.
            handleOpenAccountSettingsModal();
            return;
          }
          setAccountContextMenuIsVisible((prev) => !prev);
        }}
      >
        {!validUser && !isLoading && (
          <DefaultUserAvatar width={20} height={20} />
        )}
        {!validUser && isLoading && <LoadingSpinner size="small" />}
        {validUser && (
          <img
            src={user.avatar_url}
            alt="User avatar"
            className="w-full h-full rounded-full"
          />
        )}
      </button>
      {accountContextMenuIsVisible && (
        <AccountSettingsContextMenu
          isLoggedIn={!!user}
          onClose={() => setAccountContextMenuIsVisible(false)}
          onClickAccountSettings={() => {
            setAccountContextMenuIsVisible(false);
            handleOpenAccountSettingsModal();
          }}
          onLogout={() => {
            onLogout();
            setAccountContextMenuIsVisible(false);
          }}
        />
      )}
    </div>
  );
}
