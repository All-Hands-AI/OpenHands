import DepositModal from "#/components/features/modalDeposit/DepositModal";
import { AllHandsLogoButton } from "#/components/shared/buttons/all-hands-logo-button";
import { ExitProjectButton } from "#/components/shared/buttons/exit-project-button";
import { SettingsButton } from "#/components/shared/buttons/settings-button";
import { TooltipButton } from "#/components/shared/buttons/tooltip-button";
import { SettingsModal } from "#/components/shared/modals/settings/settings-modal";
import { useLogout } from "#/hooks/mutation/use-logout";
import { useConfig } from "#/hooks/query/use-config";
import { useSettings } from "#/hooks/query/use-settings";
import { useEndSession } from "#/hooks/use-end-session";
import ChatIcon from "#/icons/chat-icon.svg?react";
import { setCurrentAgentState } from "#/state/agent-slice";
import { AgentState } from "#/types/agent-state";
import { displayErrorToast } from "#/utils/custom-toast-handlers";
import { cn } from "#/utils/utils";
import posthog from "posthog-js";
import React from "react";
import { MdAccountBalanceWallet } from "react-icons/md";
import { useDispatch } from "react-redux";
import { NavLink, useLocation } from "react-router";
import { useAccount } from "wagmi";
import { ConversationPanel } from "../conversation-panel/conversation-panel";
import { ConversationPanelWrapper } from "../conversation-panel/conversation-panel-wrapper";
import { UserActions } from "./user-actions";
import { ModeButton } from "#/components/shared/buttons/mode-button";

export function Sidebar() {
  const location = useLocation();
  const dispatch = useDispatch();
  const endSession = useEndSession();
  // const user = useGitHubUser();
  const { data: config } = useConfig();
  const {
    data: settings,
    error: settingsError,
    isError: settingsIsError,
    isFetching: isFetchingSettings,
  } = useSettings();
  const { mutateAsync: logout } = useLogout();

  const [settingsModalIsOpen, setSettingsModalIsOpen] = React.useState(false);
  const [depositModalIsOpen, setDepositModalIsOpen] = React.useState(false);
  const [conversationPanelIsOpen, setConversationPanelIsOpen] =
    React.useState(false);

  // TODO: Remove HIDE_LLM_SETTINGS check once released
  const shouldHideLlmSettings =
    config?.FEATURE_FLAGS.HIDE_LLM_SETTINGS && config?.APP_MODE === "saas";

  React.useEffect(() => {
    if (shouldHideLlmSettings) return;

    if (location.pathname === "/settings") {
      setSettingsModalIsOpen(false);
    } else if (
      !isFetchingSettings &&
      settingsIsError &&
      settingsError?.status !== 404
    ) {
      // We don't show toast errors for settings in the global error handler
      // because we have a special case for 404 errors
      displayErrorToast(
        "Something went wrong while fetching settings. Please reload the page.",
      );
    }
    // TODO: Enable this when user can customize llm settings
    // else if (config?.APP_MODE === "oss" && settingsError?.status === 404) {
    //   setSettingsModalIsOpen(true);
    // }
  }, [
    settingsError?.status,
    settingsError,
    isFetchingSettings,
    location.pathname,
  ]);

  const handleEndSession = () => {
    dispatch(setCurrentAgentState(AgentState.LOADING));
    endSession();
  };

  const handleLogout = async () => {
    await logout();
    posthog.reset();
  };
  const account = useAccount();

  return (
    <>
      <aside className="h-[50px] bg-neutral-1200 dark:bg-neutral-300 md:h-auto px-3 py-3 flex flex-row md:flex-col gap-1">
        <nav className="flex flex-row md:flex-col items-center justify-between w-full h-auto md:w-auto md:h-full">
          <div className="flex flex-row md:flex-col items-center gap-8 max-md:gap-4">
            <div className="flex items-center justify-center">
              <AllHandsLogoButton onClick={handleEndSession} />
            </div>
            <div className="flex flex-col gap-4">
              <ExitProjectButton onClick={handleEndSession} />
              {account?.address && (
                <TooltipButton
                  testId="toggle-conversation-panel"
                  tooltip="Conversations"
                  ariaLabel="Conversations"
                  onClick={() => setConversationPanelIsOpen((prev) => !prev)}
                  className={cn(
                    "rounded-lg p-2 transition-colors w-10 h-10 group/item",
                    "hover:bg-neutral-1000 dark:hover:bg-[#262525]",
                    conversationPanelIsOpen &&
                      "bg-neutral-1000 dark:bg-[#262525]",
                  )}
                >
                  <ChatIcon
                    className={cn(
                      "transition-colors text-neutral-800",
                      "group-hover/item:text-neutral-100 dark:group-hover/item:text-white",
                      conversationPanelIsOpen &&
                        "text-neutral-100 dark:text-white",
                    )}
                  />
                </TooltipButton>
              )}
            </div>
          </div>

          <div className="flex flex-row md:flex-col md:items-center gap-4">
            {/* <DocsButton /> */}
            {/* <ModeButton /> */}
            {account?.address && (
              <TooltipButton
                testId="toggle-deposit-modal"
                tooltip="Deposit"
                ariaLabel="Deposit"
                onClick={() => setDepositModalIsOpen(true)}
                className="rounded-lg p-2 hover:bg-neutral-1000  transition-colors group/item"
              >
                <MdAccountBalanceWallet
                  size={24}
                  className="text-neutral-800 group-hover/item:text-neutral-100"
                />
              </TooltipButton>
            )}
            <UserActions onLogout={handleLogout} isLoading={false} />
            <NavLink
              to="/settings"
              className={({ isActive }) =>
                cn(
                  "p-2 h-10 w-10 flex items-center justify-center rounded-lg hover:bg-neutral-1000 hover:text-neutral-100",
                  isActive
                    ? "text-neutral-100 bg-neutral-1000"
                    : "text-neutral-800",
                )
              }
            >
              <SettingsButton className="p-2 h-10 w-10" />
            </NavLink>
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

      {settingsModalIsOpen && (
        <SettingsModal
          settings={settings}
          onClose={() => setSettingsModalIsOpen(false)}
        />
      )}

      <DepositModal
        isOpen={depositModalIsOpen}
        onClose={() => setDepositModalIsOpen(false)}
      />
    </>
  );
}
