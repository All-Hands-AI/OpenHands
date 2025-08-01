import { useTranslation } from "react-i18next";
import React, { useCallback } from "react";
import { useClickOutsideElement } from "#/hooks/use-click-outside-element";
import { cn } from "#/utils/utils";
import { ContextMenu } from "../../context-menu/context-menu";
import { ContextMenuListItem } from "../../context-menu/context-menu-list-item";
import { I18nKey } from "#/i18n/declaration";

interface ConversationCardContextMenuProps {
  onClose: () => void;
  onDelete?: (event: React.MouseEvent<HTMLButtonElement>) => void;
  onStop?: (event: React.MouseEvent<HTMLButtonElement>) => void;
  onEdit?: (event: React.MouseEvent<HTMLButtonElement>) => void;
  onDisplayCost?: (event: React.MouseEvent<HTMLButtonElement>) => void;
  onShowAgentTools?: (event: React.MouseEvent<HTMLButtonElement>) => void;
  onShowMicroagents?: (event: React.MouseEvent<HTMLButtonElement>) => void;
  onDownloadViaVSCode?: (event: React.MouseEvent<HTMLButtonElement>) => void;
  position?: "top" | "bottom";
}

export function ConversationCardContextMenu({
  onClose,
  onDelete,
  onStop,
  onEdit,
  onDisplayCost,
  onShowAgentTools,
  onShowMicroagents,
  onDownloadViaVSCode,
  position = "bottom",
}: ConversationCardContextMenuProps) {
  const { t } = useTranslation();
  const ref = useClickOutsideElement<HTMLUListElement>(onClose);

  const generateSection = useCallback(
    (items: React.ReactNode[], isLast?: boolean) => {
      const filteredItems = items.filter((i) => i != null);
      const divider = <div className="border-b-1 border-[#A3A3A3]" />;

      if (filteredItems.length > 0) {
        return !isLast ? [...filteredItems, divider] : filteredItems;
      }
      return [];
    },
    [],
  );

  return (
    <ContextMenu
      ref={ref}
      testId="context-menu"
      className={cn(
        "right-0 absolute mt-2",
        position === "top" && "bottom-full",
        position === "bottom" && "top-full",
      )}
    >
      {generateSection([
        onEdit && (
          <ContextMenuListItem testId="edit-button" onClick={onEdit}>
            {t(I18nKey.BUTTON$RENAME)}
          </ContextMenuListItem>
        ),
      ])}
      {generateSection([
        onShowAgentTools && (
          <ContextMenuListItem
            testId="show-agent-tools-button"
            onClick={onShowAgentTools}
          >
            {t(I18nKey.BUTTON$SHOW_AGENT_TOOLS_AND_METADATA)}
          </ContextMenuListItem>
        ),
        onShowMicroagents && (
          <ContextMenuListItem
            testId="show-microagents-button"
            onClick={onShowMicroagents}
          >
            {t(I18nKey.CONVERSATION$SHOW_MICROAGENTS)}
          </ContextMenuListItem>
        ),
      ])}
      {generateSection([
        onStop && (
          <ContextMenuListItem testId="stop-button" onClick={onStop}>
            {t(I18nKey.BUTTON$STOP)}
          </ContextMenuListItem>
        ),
        onDownloadViaVSCode && (
          <ContextMenuListItem
            testId="download-vscode-button"
            onClick={onDownloadViaVSCode}
          >
            {t(I18nKey.BUTTON$DOWNLOAD_VIA_VSCODE)}
          </ContextMenuListItem>
        ),
      ])}
      {generateSection(
        [
          onDisplayCost && (
            <ContextMenuListItem
              testId="display-cost-button"
              onClick={onDisplayCost}
            >
              {t(I18nKey.BUTTON$DISPLAY_COST)}
            </ContextMenuListItem>
          ),
          onDelete && (
            <ContextMenuListItem testId="delete-button" onClick={onDelete}>
              {t(I18nKey.BUTTON$DELETE_CONVERSATION)}
            </ContextMenuListItem>
          ),
        ],
        true,
      )}
    </ContextMenu>
  );
}
