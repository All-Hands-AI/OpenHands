import React from "react";
import { FaListUl } from "react-icons/fa";
import { useDispatch } from "react-redux";
import posthog from "posthog-js";
import toast from "react-hot-toast";
import { NavLink } from "react-router";
import { useGitHubUser } from "#/hooks/query/use-github-user";
import { UserActions } from "./user-actions";
import { AllHandsLogoButton } from "#/components/shared/buttons/all-hands-logo-button";
import { DocsButton } from "#/components/shared/buttons/docs-button";
import { ExitProjectButton } from "#/components/shared/buttons/exit-project-button";
import { SettingsButton } from "#/components/shared/buttons/settings-button";
import { LoadingSpinner } from "#/components/shared/loading-spinner";
import { SettingsModal } from "#/components/shared/modals/settings/settings-modal";
import { useCurrentSettings } from "#/context/settings-context";
import { useSettings } from "#/hooks/query/use-settings";
import { ConversationPanel } from "../conversation-panel/conversation-panel";
import { MULTI_CONVERSATION_UI } from "#/utils/feature-flags";
import { useEndSession } from "#/hooks/use-end-session";
import { setCurrentAgentState } from "#/state/agent-slice";
import { AgentState } from "#/types/agent-state";
import { TooltipButton } from "#/components/shared/buttons/tooltip-button";
import { ConversationPanelWrapper } from "../conversation-panel/conversation-panel-wrapper";
import { useLogout } from "#/hooks/mutation/use-logout";
import { useConfig } from "#/hooks/query/use-config";

export function Sidebar() {
  const dispatch = useDispatch();
  const endSession = useEndSession();
  const user = useGitHubUser();
  const { data: config } = useConfig();
  const {
    data: settings,
    error: settingsError,
    isError: settingsIsError,
    isFetching: isFetchingSettings,
  } = useSettings();
  const { mutateAsync: logout } = useLogout();
  const { saveUserSettings } = useCurrentSettings();

  const [settingsModalIsOpen, setSettingsModalIsOpen] = React.useState(false);

  const [conversationPanelIsOpen, setConversationPanelIsOpen] =
    React.useState(false);

  React.useEffect(() => {
    // We don't show toast errors for settings in the global error handler
    // because we have a special case for 404 errors
    if (
      !isFetchingSettings &&
      settingsIsError &&
      settingsError?.status !== 404
    ) {
      toast.error(
        "Something went wrong while fetching settings. Please reload the page.",
      );
    }
  }, [settingsError?.status, settingsError, isFetchingSettings]);

  const handleEndSession = () => {
    dispatch(setCurrentAgentState(AgentState.LOADING));
    endSession();
  };

  const handleLogout = async () => {
    if (config?.APP_MODE === "saas") await logout();
    else await saveUserSettings({ unset_github_token: true });
    posthog.reset();
  };

  return (
    <>
      <aside className="h-[40px] md:h-auto px-1 flex flex-row md:flex-col gap-1">
        <nav className="flex flex-row md:flex-col items-center justify-between h-full">
          <div className="flex flex-col items-center gap-[26px]">
            <div className="flex items-center justify-center">
              <AllHandsLogoButton onClick={handleEndSession} />
            </div>
            <ExitProjectButton onClick={handleEndSession} />
            {MULTI_CONVERSATION_UI && (
              <TooltipButton
                testId="toggle-conversation-panel"
                tooltip="Conversations"
                ariaLabel="Conversations"
                onClick={() => setConversationPanelIsOpen((prev) => !prev)}
              >
                <FaListUl size={22} />
              </TooltipButton>
            )}
            <DocsButton />
          </div>

          <div className="flex flex-col items-center gap-[26px] mb-4">
            <NavLink
              to="/settings"
              className={({ isActive }) =>
                isActive ? "text-white" : "text-[#9099AC]"
              }
            >
              <SettingsButton />
            </NavLink>
            {!user.isLoading && (
              <UserActions
                user={
                  user.data ? { avatar_url: user.data.avatar_url } : undefined
                }
                onLogout={handleLogout}
              />
            )}
            {user.isLoading && <LoadingSpinner size="small" />}
          </div>
        </nav>

        {conversationPanelIsOpen && (
          <ConversationPanelWrapper isOpen={conversationPanelIsOpen}>
            <ConversationPanel
              onClose={() => setConversationPanelIsOpen(false)}
            />
          </ConversationPanelWrapper>
        )}
      </aside>

      {(settingsError?.status === 404 || settingsModalIsOpen) && (
        <SettingsModal
          settings={settings}
          onClose={() => setSettingsModalIsOpen(false)}
        />
      )}
    </>
  );
}
