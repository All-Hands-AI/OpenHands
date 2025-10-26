import { useEffect } from "react";
import { useTranslation } from "react-i18next";
import { useLocalStorage } from "@uidotdev/usehooks";
import JupyterIcon from "#/icons/jupyter.svg?react";
import TerminalIcon from "#/icons/terminal.svg?react";
import GlobeIcon from "#/icons/globe.svg?react";
import ServerIcon from "#/icons/server.svg?react";
import GitChanges from "#/icons/git_changes.svg?react";
import VSCodeIcon from "#/icons/vscode.svg?react";
import { cn } from "#/utils/utils";
import { ConversationTabNav } from "./conversation-tab-nav";
import { ChatActionTooltip } from "../../chat/chat-action-tooltip";
import { I18nKey } from "#/i18n/declaration";
import { VSCodeTooltipContent } from "./vscode-tooltip-content";
import {
  useConversationStore,
  type ConversationTab,
} from "#/state/conversation-store";

export function ConversationTabs() {
  const {
    selectedTab,
    isRightPanelShown,
    setHasRightPanelToggled,
    setSelectedTab,
  } = useConversationStore();

  // Persist selectedTab and isRightPanelShown in localStorage
  const [persistedSelectedTab, setPersistedSelectedTab] =
    useLocalStorage<ConversationTab | null>(
      "conversation-selected-tab",
      "editor",
    );

  const [persistedIsRightPanelShown, setPersistedIsRightPanelShown] =
    useLocalStorage<boolean>("conversation-right-panel-shown", true);

  const onTabChange = (value: ConversationTab | null) => {
    setSelectedTab(value);
    // Persist the selected tab to localStorage
    setPersistedSelectedTab(value);
  };

  // Initialize Zustand state from localStorage on component mount
  useEffect(() => {
    // Initialize selectedTab from localStorage if available
    setSelectedTab(persistedSelectedTab);
    setHasRightPanelToggled(persistedIsRightPanelShown);
  }, [
    setSelectedTab,
    setHasRightPanelToggled,
    persistedSelectedTab,
    persistedIsRightPanelShown,
  ]);

  useEffect(() => {
    const handlePanelVisibilityChange = () => {
      if (isRightPanelShown) {
        // If no tab is selected, default to editor tab
        if (!selectedTab) {
          onTabChange("editor");
        }
      }
    };

    handlePanelVisibilityChange();
  }, [isRightPanelShown, selectedTab, onTabChange]);

  const { t } = useTranslation();

  const onTabSelected = (tab: ConversationTab) => {
    if (selectedTab === tab && isRightPanelShown) {
      // If clicking the same active tab, close the drawer
      setHasRightPanelToggled(false);
      setPersistedIsRightPanelShown(false);
    } else {
      // If clicking a different tab or drawer is closed, open drawer and select tab
      onTabChange(tab);
      if (!isRightPanelShown) {
        setHasRightPanelToggled(true);
        setPersistedIsRightPanelShown(true);
      }
    }
  };

  const isTabActive = (tab: ConversationTab) =>
    isRightPanelShown && selectedTab === tab;

  const tabs = [
    {
      isActive: isTabActive("editor"),
      icon: GitChanges,
      onClick: () => onTabSelected("editor"),
      tooltipContent: t(I18nKey.COMMON$CHANGES),
      tooltipAriaLabel: t(I18nKey.COMMON$CHANGES),
    },
    {
      isActive: isTabActive("vscode"),
      icon: VSCodeIcon,
      onClick: () => onTabSelected("vscode"),
      tooltipContent: <VSCodeTooltipContent />,
      tooltipAriaLabel: t(I18nKey.COMMON$CODE),
    },
    {
      isActive: isTabActive("terminal"),
      icon: TerminalIcon,
      onClick: () => onTabSelected("terminal"),
      tooltipContent: t(I18nKey.COMMON$TERMINAL),
      tooltipAriaLabel: t(I18nKey.COMMON$TERMINAL),
    },
    {
      isActive: isTabActive("jupyter"),
      icon: JupyterIcon,
      onClick: () => onTabSelected("jupyter"),
      tooltipContent: t(I18nKey.COMMON$JUPYTER),
      tooltipAriaLabel: t(I18nKey.COMMON$JUPYTER),
    },
    {
      isActive: isTabActive("served"),
      icon: ServerIcon,
      onClick: () => onTabSelected("served"),
      tooltipContent: t(I18nKey.COMMON$APP),
      tooltipAriaLabel: t(I18nKey.COMMON$APP),
    },
    {
      isActive: isTabActive("browser"),
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
        "flex flex-row justify-start lg:justify-end items-center gap-4.5",
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
