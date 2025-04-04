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
    } else if (config?.APP_MODE === "oss" && settingsError?.status === 404) {
      setSettingsModalIsOpen(true);
    }
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
      <aside className="h-[50px] bg-[#141415] md:h-auto px-3 py-3 flex flex-row md:flex-col gap-1">
        <nav className="flex flex-row md:flex-col items-center justify-between w-full h-auto md:w-auto md:h-full">
          <div className="flex flex-row md:flex-col items-center gap-[26px] max-md:gap-4">
            <div className="flex items-center justify-center">
              <AllHandsLogoButton onClick={handleEndSession} />
            </div>
            <ExitProjectButton onClick={handleEndSession} />
            {account?.address && (
              <TooltipButton
                testId="toggle-conversation-panel"
                tooltip="Conversations"
                ariaLabel="Conversations"
                onClick={() => setConversationPanelIsOpen((prev) => !prev)}
              >
                <ChatIcon
                  className={cn(
                    "opacity-50 transition-colors",
                    conversationPanelIsOpen && "opacity-100",
                  )}
                />
              </TooltipButton>
            )}
          </div>

          <div className="flex flex-row md:flex-col md:items-center gap-[26px] md:mb-4">
            {/* <DocsButton /> */}
            {account?.address && (
              <TooltipButton
                testId="toggle-deposit-modal"
                tooltip="Deposit"
                ariaLabel="Deposit"
                onClick={() => setDepositModalIsOpen(true)}
              >
                <MdAccountBalanceWallet
                  size={22}
                  className="text-[#9099AC] hover:text-white transition-colors"
                />
              </TooltipButton>
            )}
            <NavLink
              to="/settings"
              className={({ isActive }) =>
                `${isActive ? "text-white" : "text-[#9099AC]"} mt-0.5 md:mt-0`
              }
            >
              <SettingsButton />
            </NavLink>
            <UserActions onLogout={handleLogout} isLoading={false} />
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
