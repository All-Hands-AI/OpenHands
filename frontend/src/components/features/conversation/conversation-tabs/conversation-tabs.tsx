import { useTranslation } from "react-i18next";
import JupyterIcon from "#/icons/jupyter.svg?react";
import TerminalIcon from "#/icons/terminal.svg?react";
import GlobeIcon from "#/icons/globe.svg?react";
import ServerIcon from "#/icons/server.svg?react";
import GitChanges from "#/icons/git_changes.svg?react";
import VSCodeIcon from "#/icons/vscode.svg?react";
import { cn } from "#/utils/utils";
import { useConversationTabs } from "./use-conversation-tabs";
import { ConversationTabNav } from "./conversation-tab-nav";
import { ChatActionTooltip } from "../../chat/chat-action-tooltip";
import { I18nKey } from "#/i18n/declaration";
import { VSCodeTooltipContent } from "./vscode-tooltip-content";

export function ConversationTabs() {
  const [{ selectedTab, terminalOpen }, { onTabChange, onTerminalChange }] =
    useConversationTabs();

  const { t } = useTranslation();

  const tabs = [
    {
      isActive: selectedTab === "editor",
      icon: GitChanges,
      onClick: () => onTabChange("editor"),
      tooltipContent: t(I18nKey.COMMON$CHANGES),
      tooltipAriaLabel: t(I18nKey.COMMON$CHANGES),
    },
    {
      isActive: selectedTab === "vscode",
      icon: VSCodeIcon,
      onClick: () => onTabChange("vscode"),
      tooltipContent: <VSCodeTooltipContent />,
      tooltipAriaLabel: t(I18nKey.COMMON$CODE),
    },

    {
      isActive: terminalOpen,
      icon: TerminalIcon,
      onClick: () => onTerminalChange((prev) => !prev),
      tooltipContent: t(I18nKey.COMMON$TERMINAL),
      tooltipAriaLabel: t(I18nKey.COMMON$TERMINAL),
    },
    {
      isActive: selectedTab === "jupyter",
      icon: JupyterIcon,
      onClick: () => onTabChange("jupyter"),
      tooltipContent: t(I18nKey.COMMON$JUPYTER),
      tooltipAriaLabel: t(I18nKey.COMMON$JUPYTER),
    },
    {
      isActive: selectedTab === "served",
      icon: ServerIcon,
      onClick: () => onTabChange("served"),
      tooltipContent: t(I18nKey.COMMON$APP),
      tooltipAriaLabel: t(I18nKey.COMMON$APP),
    },
    {
      isActive: selectedTab === "browser",
      icon: GlobeIcon,
      onClick: () => onTabChange("browser"),
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
