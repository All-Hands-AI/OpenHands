import React from "react";
import { useLocation } from "react-router";
import FolderIcon from "#/icons/docs.svg?react";
import { useAuth } from "#/context/auth-context";
import { useGitHubUser } from "#/hooks/query/use-github-user";
import { useIsAuthed } from "#/hooks/query/use-is-authed";
import { UserActions } from "./user-actions";
import { AllHandsLogoButton } from "#/components/shared/buttons/all-hands-logo-button";
import { DocsButton } from "#/components/shared/buttons/docs-button";
import { ExitProjectButton } from "#/components/shared/buttons/exit-project-button";
import { SettingsButton } from "#/components/shared/buttons/settings-button";
import { LoadingSpinner } from "#/components/shared/loading-spinner";
import { AccountSettingsModal } from "#/components/shared/modals/account-settings/account-settings-modal";
import { ExitProjectConfirmationModal } from "#/components/shared/modals/exit-project-confirmation-modal";
import { SettingsModal } from "#/components/shared/modals/settings/settings-modal";
import { useSettingsUpToDate } from "#/context/settings-up-to-date-context";
import { useSettings } from "#/hooks/query/use-settings";
import { ConversationPanel } from "../conversation-panel/conversation-panel";
import { cn } from "#/utils/utils";
import { MULTI_CONVO_UI_IS_ENABLED } from "#/utils/constants";

export function Sidebar() {
  const location = useLocation();
  const user = useGitHubUser();
  const { data: isAuthed } = useIsAuthed();
  const { logout } = useAuth();
  const { data: settings, isError: settingsIsError } = useSettings();
  const { isUpToDate: settingsAreUpToDate } = useSettingsUpToDate();

  const [accountSettingsModalOpen, setAccountSettingsModalOpen] =
    React.useState(false);
  const [settingsModalIsOpen, setSettingsModalIsOpen] = React.useState(false);
  const [startNewProjectModalIsOpen, setStartNewProjectModalIsOpen] =
    React.useState(false);
  const [conversationPanelIsOpen, setConversationPanelIsOpen] = React.useState(
    MULTI_CONVO_UI_IS_ENABLED,
  );

  React.useEffect(() => {
    // If the github token is invalid, open the account settings modal again
    if (user.isError) {
      setAccountSettingsModalOpen(true);
    }
  }, [user.isError]);

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

  const showSettingsModal =
    isAuthed && (!settingsAreUpToDate || settingsModalIsOpen);

  return (
    <>
      <aside className="h-[40px] md:h-auto px-1 flex flex-row md:flex-col gap-1 relative">
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
          {MULTI_CONVO_UI_IS_ENABLED && (
            <button
              data-testid="toggle-conversation-panel"
              type="button"
              onClick={() => setConversationPanelIsOpen((prev) => !prev)}
              className={cn(
                conversationPanelIsOpen ? "border-b-2 border-[#FFE165]" : "",
              )}
            >
              <FolderIcon width={28} height={28} />
            </button>
          )}
          <DocsButton />
          <ExitProjectButton
            onClick={() => setStartNewProjectModalIsOpen(true)}
          />
        </nav>

        {conversationPanelIsOpen && (
          <div
            className="absolute h-full left-[calc(100%+12px)] top-0 z-20" // 12px padding (sidebar parent)
          >
            <ConversationPanel
              onClose={() => setConversationPanelIsOpen(false)}
            />
          </div>
        )}
      </aside>

      {accountSettingsModalOpen && (
        <AccountSettingsModal onClose={handleAccountSettingsModalClose} />
      )}
      {settingsIsError ||
        (showSettingsModal && (
          <SettingsModal
            settings={settings}
            onClose={() => setSettingsModalIsOpen(false)}
          />
        ))}
      {startNewProjectModalIsOpen && (
        <ExitProjectConfirmationModal
          onClose={() => setStartNewProjectModalIsOpen(false)}
        />
      )}
    </>
  );
}
