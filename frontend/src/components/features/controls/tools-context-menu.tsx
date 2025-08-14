import React from "react";
import { useTranslation } from "react-i18next";
import { useClickOutsideElement } from "#/hooks/use-click-outside-element";
import { useActiveConversation } from "#/hooks/query/use-active-conversation";
import { useUserProviders } from "#/hooks/use-user-providers";
import { cn } from "#/utils/utils";
import { ContextMenu } from "../context-menu/context-menu";
import { ContextMenuListItem } from "../context-menu/context-menu-list-item";
import { ContextMenuSeparator } from "../context-menu/context-menu-separator";
import { I18nKey } from "#/i18n/declaration";

import CodeBranchIcon from "#/icons/u-code-branch.svg?react";
import RobotIcon from "#/icons/u-robot.svg?react";
import ToolsIcon from "#/icons/u-tools.svg?react";
import SettingsIcon from "#/icons/settings.svg?react";
import CarretRightFillIcon from "#/icons/carret-right-fill.svg?react";
import { ToolsContextMenuIconText } from "./tools-context-menu-icon-text";
import { GitToolsSubmenu } from "./git-tools-submenu";
import { MacrosSubmenu } from "./macros-submenu";

const contextMenuListItemClassName =
  "cursor-pointer p-0 h-auto hover:bg-transparent px-[6px]";

interface ToolsContextMenuProps {
  onClose: () => void;
  onShowMicroagents: (event: React.MouseEvent<HTMLButtonElement>) => void;
  onShowAgentTools: (event: React.MouseEvent<HTMLButtonElement>) => void;
}

export function ToolsContextMenu({
  onClose,
  onShowMicroagents,
  onShowAgentTools,
}: ToolsContextMenuProps) {
  const { t } = useTranslation();
  const ref = useClickOutsideElement<HTMLUListElement>(onClose);
  const { data: conversation } = useActiveConversation();
  const { providers } = useUserProviders();

  const hasRepository = !!conversation?.selected_repository;
  const providersAreSet = providers.length > 0;
  const showGitTools = hasRepository && providersAreSet;

  return (
    <ContextMenu
      ref={ref}
      testId="tools-context-menu"
      className={cn(
        "flex flex-col gap-2 left-[-16px] absolute mb-2 z-50 text-white bg-tertiary rounded-[6px] py-[6px] px-1",
        "bottom-full overflow-visible",
      )}
    >
      {/* Git Tools */}
      {showGitTools && (
        <div className="relative group/git">
          <ContextMenuListItem
            testId="git-tools-button"
            onClick={() => {}}
            className={contextMenuListItemClassName}
          >
            <ToolsContextMenuIconText
              icon={<CodeBranchIcon width={16} height={16} />}
              text={t(I18nKey.COMMON$GIT_TOOLS)}
              rightIcon={<CarretRightFillIcon width={10} height={10} />}
            />
          </ContextMenuListItem>
          <div className="absolute left-full top-[-6px] z-60 opacity-0 invisible pointer-events-none group-hover/git:opacity-100 group-hover/git:visible group-hover/git:pointer-events-auto hover:opacity-100 hover:visible hover:pointer-events-auto transition-all duration-200 ml-[1px]">
            <GitToolsSubmenu onClose={onClose} />
          </div>
        </div>
      )}

      {/* Macros */}
      <div className="relative group/macros">
        <ContextMenuListItem
          testId="macros-button"
          onClick={() => {}}
          className={contextMenuListItemClassName}
        >
          <ToolsContextMenuIconText
            icon={<SettingsIcon width={16} height={16} />}
            text={t(I18nKey.COMMON$MACROS)}
            rightIcon={<CarretRightFillIcon width={10} height={10} />}
          />
        </ContextMenuListItem>
        <div className="absolute left-full top-[-4px] z-60 opacity-0 invisible pointer-events-none group-hover/macros:opacity-100 group-hover/macros:visible group-hover/macros:pointer-events-auto hover:opacity-100 hover:visible hover:pointer-events-auto transition-all duration-200 ml-[1px]">
          <MacrosSubmenu onClose={onClose} />
        </div>
      </div>

      <ContextMenuSeparator className="bg-[#5C5D62]" />

      {/* Show Available Microagents */}
      <ContextMenuListItem
        testId="show-microagents-button"
        onClick={onShowMicroagents}
        className={contextMenuListItemClassName}
      >
        <ToolsContextMenuIconText
          icon={<RobotIcon width={16} height={16} />}
          text={t(I18nKey.CONVERSATION$SHOW_MICROAGENTS)}
        />
      </ContextMenuListItem>

      {/* Show Agent Tools and Metadata */}
      <ContextMenuListItem
        testId="show-agent-tools-button"
        onClick={onShowAgentTools}
        className={contextMenuListItemClassName}
      >
        <ToolsContextMenuIconText
          icon={<ToolsIcon width={16} height={16} />}
          text={t(I18nKey.BUTTON$SHOW_AGENT_TOOLS_AND_METADATA)}
        />
      </ContextMenuListItem>
    </ContextMenu>
  );
}
