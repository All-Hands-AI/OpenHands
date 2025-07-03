import { useTranslation } from "react-i18next";
import { useClickOutsideElement } from "#/hooks/use-click-outside-element";
import { cn } from "#/utils/utils";
import { ContextMenu } from "../context-menu/context-menu";
import { ContextMenuListItem } from "../context-menu/context-menu-list-item";
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

  return (
    <ContextMenu
      ref={ref}
      testId="context-menu"
      className={cn(
        "right-0 absolute mt-3",
        position === "top" && "bottom-full",
        position === "bottom" && "top-full",
      )}
    >
      {onDelete && (
        <ContextMenuListItem testId="delete-button" onClick={onDelete}>
          {t(I18nKey.BUTTON$DELETE)}
        </ContextMenuListItem>
      )}
      {onStop && (
        <ContextMenuListItem testId="stop-button" onClick={onStop}>
          {t(I18nKey.BUTTON$STOP)}
        </ContextMenuListItem>
      )}
      {onEdit && (
        <ContextMenuListItem testId="edit-button" onClick={onEdit}>
          {t(I18nKey.BUTTON$EDIT_TITLE)}
        </ContextMenuListItem>
      )}
      {onDownloadViaVSCode && (
        <ContextMenuListItem
          testId="download-vscode-button"
          onClick={onDownloadViaVSCode}
        >
          {t(I18nKey.BUTTON$DOWNLOAD_VIA_VSCODE)}
        </ContextMenuListItem>
      )}
      {onDisplayCost && (
        <ContextMenuListItem
          testId="display-cost-button"
          onClick={onDisplayCost}
        >
          {t(I18nKey.BUTTON$DISPLAY_COST)}
        </ContextMenuListItem>
      )}
      {onShowAgentTools && (
        <ContextMenuListItem
          testId="show-agent-tools-button"
          onClick={onShowAgentTools}
        >
          {t(I18nKey.BUTTON$SHOW_AGENT_TOOLS_AND_METADATA)}
        </ContextMenuListItem>
      )}
      {onShowMicroagents && (
        <ContextMenuListItem
          testId="show-microagents-button"
          onClick={onShowMicroagents}
        >
          {t(I18nKey.CONVERSATION$SHOW_MICROAGENTS)}
        </ContextMenuListItem>
      )}
    </ContextMenu>
  );
}
