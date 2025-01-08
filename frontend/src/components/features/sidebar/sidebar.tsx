import React from "react";
import { FaListUl } from "react-icons/fa";
import { useDispatch } from "react-redux";
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
import { SettingsModal } from "#/components/shared/modals/settings/settings-modal";
import { useSettingsUpToDate } from "#/context/settings-up-to-date-context";
import { useSettings } from "#/hooks/query/use-settings";
import { ConversationPanel } from "../conversation-panel/conversation-panel";
import { MULTI_CONVERSATION_UI } from "#/utils/feature-flags";
import { useEndSession } from "#/hooks/use-end-session";
import { setCurrentAgentState } from "#/state/agent-slice";
import { AgentState } from "#/types/agent-state";
import { TooltipButton } from "#/components/shared/buttons/tooltip-button";
import { ConversationPanelWrapper } from "../conversation-panel/conversation-panel-wrapper";

export function Sidebar() {
  const dispatch = useDispatch();
  const endSession = useEndSession();
  const user = useGitHubUser();
  const { data: isAuthed } = useIsAuthed();
  const { logout } = useAuth();
  const { data: settings, isError: settingsIsError } = useSettings();
  const { isUpToDate: settingsAreUpToDate } = useSettingsUpToDate();

  const [accountSettingsModalOpen, setAccountSettingsModalOpen] =
    React.useState(false);
  const [settingsModalIsOpen, setSettingsModalIsOpen] = React.useState(false);

  const [conversationPanelIsOpen, setConversationPanelIsOpen] =
    React.useState(false);

  React.useEffect(() => {
    // If the github token is invalid, open the account settings modal again
    if (user.isError) {
      setAccountSettingsModalOpen(true);
    }
  }, [user.isError]);

  const handleEndSession = () => {
    dispatch(setCurrentAgentState(AgentState.LOADING));
    endSession();
  };

  const handleAccountSettingsModalClose = () => {
    // If the user closes the modal without connecting to GitHub,
    // we need to log them out to clear the invalid token from the
    // local storage
    if (user.isError) logout();
    setAccountSettingsModalOpen(false);
  };

  const showSettingsModal =
    isAuthed && (!settingsAreUpToDate || settingsModalIsOpen);

  return (
    <>
      <aside className="h-[40px] md:h-auto px-1 flex flex-row md:flex-col gap-1">
        <nav className="flex flex-row md:flex-col items-center gap-[18px]">
          <div className="w-[34px] h-[34px] flex items-center justify-center mb-7">
            <AllHandsLogoButton onClick={handleEndSession} />
          </div>
          {user.isLoading && <LoadingSpinner size="small" />}
          <ExitProjectButton onClick={handleEndSession} />
          {MULTI_CONVERSATION_UI && (
            <TooltipButton
              data-testid="toggle-conversation-panel"
              tooltip="Conversations"
              ariaLabel="Conversations"
              onClick={() => setConversationPanelIsOpen((prev) => !prev)}
            >
              <FaListUl size={22} />
            </TooltipButton>
          )}
          <DocsButton />
          <SettingsButton onClick={() => setSettingsModalIsOpen(true)} />
          {!user.isLoading && (
            <UserActions
              user={
                user.data ? { avatar_url: user.data.avatar_url } : undefined
              }
              onLogout={logout}
              onClickAccountSettings={() => setAccountSettingsModalOpen(true)}
            />
          )}
        </nav>

        {conversationPanelIsOpen && (
          <ConversationPanelWrapper isOpen={conversationPanelIsOpen}>
            <ConversationPanel
              onClose={() => setConversationPanelIsOpen(false)}
            />
          </ConversationPanelWrapper>
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
    </>
  );
}
