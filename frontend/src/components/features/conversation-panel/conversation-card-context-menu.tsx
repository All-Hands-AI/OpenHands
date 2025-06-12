import { useTranslation } from "react-i18next";
import { useClickOutsideElement } from "#/hooks/use-click-outside-element";
import { cn } from "#/utils/utils";
import { ContextMenu } from "../context-menu/context-menu";
import { ContextMenuListItem } from "../context-menu/context-menu-list-item";
import { I18nKey } from "#/i18n/declaration";

interface ConversationCardContextMenuProps {
  onClose: () => void;
  onDelete?: (event: React.MouseEvent<HTMLButtonElement>) => void;
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
          Delete
        </ContextMenuListItem>
      )}
      {onEdit && (
        <ContextMenuListItem testId="edit-button" onClick={onEdit}>
          Edit Title
        </ContextMenuListItem>
      )}
      {onDownloadViaVSCode && (
        <ContextMenuListItem
          testId="download-vscode-button"
          onClick={onDownloadViaVSCode}
        >
          Download via VS Code
        </ContextMenuListItem>
      )}
      {onDisplayCost && (
        <ContextMenuListItem
          testId="display-cost-button"
          onClick={onDisplayCost}
        >
          Display Cost
        </ContextMenuListItem>
      )}
      {onShowAgentTools && (
        <ContextMenuListItem
          testId="show-agent-tools-button"
          onClick={onShowAgentTools}
        >
          Show Agent Tools & Metadata
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
