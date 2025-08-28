import { useEffect, useRef } from "react";
import { useDispatch, useSelector } from "react-redux";
import { useTranslation } from "react-i18next";
import JupyterIcon from "#/icons/jupyter.svg?react";
import TerminalIcon from "#/icons/terminal.svg?react";
import GlobeIcon from "#/icons/globe.svg?react";
import ServerIcon from "#/icons/server.svg?react";
import GitChanges from "#/icons/git_changes.svg?react";
import VSCodeIcon from "#/icons/vscode.svg?react";
import { cn } from "#/utils/utils";
import { ConversationTab, useConversationTabs } from "./use-conversation-tabs";
import { ConversationTabNav } from "./conversation-tab-nav";
import { ChatActionTooltip } from "../../chat/chat-action-tooltip";
import { I18nKey } from "#/i18n/declaration";
import { VSCodeTooltipContent } from "./vscode-tooltip-content";
import { setIsRightPanelShown } from "#/state/conversation-slice";
import { RootState } from "#/store";

export function ConversationTabs() {
  const [{ selectedTab, terminalOpen }, { onTabChange, onTerminalChange }] =
    useConversationTabs();

  const isTabClicked = useRef<boolean>(false);

  const { isRightPanelShown } = useSelector(
    (state: RootState) => state.conversation,
  );

  useEffect(() => {
    const handlePanelVisibilityChange = () => {
      if (isRightPanelShown) {
        // Only change to editor tab if no tab was explicitly clicked
        if (!isTabClicked.current) {
          onTabChange("editor");
        }
      } else {
        // Reset state when panel is hidden
        onTabChange(null);
        onTerminalChange(false);
      }

      // Reset the click flag after handling the change
      isTabClicked.current = false;
    };

    handlePanelVisibilityChange();
  }, [isRightPanelShown]);

  const dispatch = useDispatch();

  const { t } = useTranslation();

  const showActionPanel = () => {
    dispatch(setIsRightPanelShown(true));
  };

  const onTerminalSelected = () => {
    onTerminalChange((prev) => !prev);
    if (!selectedTab) {
      onTabChange("editor");
    }
  };

  const onTabSelected = (
    tab: ConversationTab | null,
    isTerminal: boolean = false,
  ) => {
    if (isTerminal) {
      onTerminalSelected();
    } else if (tab) {
      onTabChange(tab);
    }
    showActionPanel();
    isTabClicked.current = true;
  };

  const tabs = [
    {
      isActive: selectedTab === "editor",
      icon: GitChanges,
      onClick: () => onTabSelected("editor"),
      tooltipContent: t(I18nKey.COMMON$CHANGES),
      tooltipAriaLabel: t(I18nKey.COMMON$CHANGES),
    },
    {
      isActive: selectedTab === "vscode",
      icon: VSCodeIcon,
      onClick: () => onTabSelected("vscode"),
      tooltipContent: <VSCodeTooltipContent />,
      tooltipAriaLabel: t(I18nKey.COMMON$CODE),
    },

    {
      isActive: terminalOpen,
      icon: TerminalIcon,
      onClick: () => onTabSelected(null, true),
      tooltipContent: t(I18nKey.COMMON$TERMINAL),
      tooltipAriaLabel: t(I18nKey.COMMON$TERMINAL),
    },
    {
      isActive: selectedTab === "jupyter",
      icon: JupyterIcon,
      onClick: () => onTabSelected("jupyter"),
      tooltipContent: t(I18nKey.COMMON$JUPYTER),
      tooltipAriaLabel: t(I18nKey.COMMON$JUPYTER),
    },
    {
      isActive: selectedTab === "served",
      icon: ServerIcon,
      onClick: () => onTabSelected("served"),
      tooltipContent: t(I18nKey.COMMON$APP),
      tooltipAriaLabel: t(I18nKey.COMMON$APP),
    },
    {
      isActive: selectedTab === "browser",
      icon: GlobeIcon,
      onClick: () => onTabSelected("browser"),
      tooltipContent: t(I18nKey.COMMON$BROWSER),
      tooltipAriaLabel: t(I18nKey.COMMON$BROWSER),
    },
  ];

  return (
    <div
      className={cn(
        "relative w-full",
        "flex flex-row justify-end items-center gap-4.5",
      )}
    >
      {tabs.map(
        (
          { icon, onClick, isActive, tooltipContent, tooltipAriaLabel },
          index,
        ) => (
          <ChatActionTooltip
            key={index}
            tooltip={tooltipContent}
            ariaLabel={tooltipAriaLabel}
          >
            <ConversationTabNav
              icon={icon}
              onClick={onClick}
              isActive={isActive}
            />
          </ChatActionTooltip>
        ),
      )}
    </div>
  );
}
