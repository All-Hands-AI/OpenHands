import React from "react";
import { useLocation } from "react-router";
import { useAuth } from "#/context/auth-context";
import { useSettings } from "#/context/settings-context";
import { useGitHubUser } from "#/hooks/query/use-github-user";
import { UserActions } from "./user-actions";
import { AllHandsLogoButton } from "#/components/shared/buttons/all-hands-logo-button";
import { DocsButton } from "#/components/shared/buttons/docs-button";
import { ExitProjectButton } from "#/components/shared/buttons/exit-project-button";
import { SettingsButton } from "#/components/shared/buttons/settings-button";
import { LoadingSpinner } from "#/components/shared/loading-spinner";
import { AccountSettingsModal } from "#/components/shared/modals/account-settings/account-settings-modal";
import { ExitProjectConfirmationModal } from "#/components/shared/modals/exit-project-confirmation-modal";
import { SettingsModal } from "#/components/shared/modals/settings/settings-modal";

export function Sidebar() {
  const location = useLocation();

  const user = useGitHubUser();
  const { logout } = useAuth();
  const { settingsAreUpToDate, settings } = useSettings();

  const [accountSettingsModalOpen, setAccountSettingsModalOpen] =
    React.useState(false);

  const [settingsModalIsOpen, setSettingsModalIsOpen] = React.useState(false);
  const [startNewProjectModalIsOpen, setStartNewProjectModalIsOpen] =
    React.useState(false);

  React.useEffect(() => {
    // If the github token is invalid, open the account settings modal again
    if (user.isError) {
      setAccountSettingsModalOpen(true);
    }
  }, [user.isError]);

  React.useEffect(() => {
    if (!settings || !settingsAreUpToDate) {
      setSettingsModalIsOpen(true);
    }
  }, [settings, settingsAreUpToDate]);

  const handleAccountSettingsModalClose = () => {
    // If the user closes the modal without connecting to GitHub,
    // we need to log them out to clear the invalid token from the
    // local storage
    if (user.isError) logout();
    setAccountSettingsModalOpen(false);
  };

  const handleClickLogo = () => {
    if (location.pathname.startsWith("/conversations/"))
      setStartNewProjectModalIsOpen(true);
  };

  return (
    <>
      <aside className="h-[40px] md:h-auto px-1 flex flex-row md:flex-col gap-1">
        <nav className="flex flex-row md:flex-col items-center gap-[18px]">
          <div className="w-[34px] h-[34px] flex items-center justify-center">
            <AllHandsLogoButton onClick={handleClickLogo} />
          </div>
          {user.isLoading && <LoadingSpinner size="small" />}
          {!user.isLoading && (
            <UserActions
              user={
                user.data ? { avatar_url: user.data.avatar_url } : undefined
              }
              onLogout={logout}
              onClickAccountSettings={() => setAccountSettingsModalOpen(true)}
            />
          )}
          <SettingsButton onClick={() => setSettingsModalIsOpen(true)} />
          <DocsButton />
          <ExitProjectButton
            onClick={() => setStartNewProjectModalIsOpen(true)}
          />
        </nav>
      </aside>
      {accountSettingsModalOpen && (
        <AccountSettingsModal onClose={handleAccountSettingsModalClose} />
      )}
      {(!accountSettingsModalOpen && settingsModalIsOpen) && (
        <SettingsModal onClose={() => setSettingsModalIsOpen(false)} />
      )}
      {startNewProjectModalIsOpen && (
        <ExitProjectConfirmationModal
          onClose={() => setStartNewProjectModalIsOpen(false)}
        />
      )}
    </>
  );
}
