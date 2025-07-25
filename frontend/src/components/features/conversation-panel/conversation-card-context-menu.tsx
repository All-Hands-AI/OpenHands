import {
  Trash,
  Power,
  Pencil,
  Download,
  Wallet,
  Wrench,
  Bot,
} from "lucide-react";
import { useTranslation } from "react-i18next";
import { useClickOutsideElement } from "#/hooks/use-click-outside-element";
import { cn } from "#/utils/utils";
import { ContextMenu } from "../context-menu/context-menu";
import { ContextMenuListItem } from "../context-menu/context-menu-list-item";
import { ContextMenuSeparator } from "../context-menu/context-menu-separator";
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

  const hasEdit = Boolean(onEdit);
  const hasDownload = Boolean(onDownloadViaVSCode);
  const hasTools = Boolean(onShowAgentTools || onShowMicroagents);
  const hasInfo = Boolean(onDisplayCost);
  const hasControl = Boolean(onStop || onDelete);

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
      {onEdit && (
        <ContextMenuListItem testId="edit-button" onClick={onEdit}>
          <div className="flex items-center gap-3 px-1">
            <Pencil className="w-4 h-4 shrink-0" />
            {t(I18nKey.BUTTON$EDIT_TITLE)}
          </div>
        </ContextMenuListItem>
      )}

      {hasEdit && (hasDownload || hasTools || hasInfo || hasControl) && (
        <ContextMenuSeparator />
      )}

      {onDownloadViaVSCode && (
        <ContextMenuListItem
          testId="download-vscode-button"
          onClick={onDownloadViaVSCode}
        >
          <div className="flex items-center gap-3 px-1">
            <Download className="w-4 h-4 shrink-0" />
            {t(I18nKey.BUTTON$DOWNLOAD_VIA_VSCODE)}
          </div>
        </ContextMenuListItem>
      )}

      {hasDownload && (hasTools || hasInfo || hasControl) && (
        <ContextMenuSeparator />
      )}

      {onShowAgentTools && (
        <ContextMenuListItem
          testId="show-agent-tools-button"
          onClick={onShowAgentTools}
        >
          <div className="flex items-center gap-3 px-1">
            <Wrench className="w-4 h-4 shrink-0" />
            {t(I18nKey.BUTTON$SHOW_AGENT_TOOLS_AND_METADATA)}
          </div>
        </ContextMenuListItem>
      )}

      {onShowMicroagents && (
        <ContextMenuListItem
          testId="show-microagents-button"
          onClick={onShowMicroagents}
        >
          <div className="flex items-center gap-3 px-1">
            <Bot className="w-4 h-4 shrink-0" />
            {t(I18nKey.CONVERSATION$SHOW_MICROAGENTS)}
          </div>
        </ContextMenuListItem>
      )}

      {hasTools && (hasInfo || hasControl) && <ContextMenuSeparator />}

      {onDisplayCost && (
        <ContextMenuListItem
          testId="display-cost-button"
          onClick={onDisplayCost}
        >
          <div className="flex items-center gap-3 px-1">
            <Wallet className="w-4 h-4 shrink-0" />
            {t(I18nKey.BUTTON$DISPLAY_COST)}
          </div>
        </ContextMenuListItem>
      )}

      {hasInfo && hasControl && <ContextMenuSeparator />}

      {onStop && (
        <ContextMenuListItem testId="stop-button" onClick={onStop}>
          <div className="flex items-center gap-3 px-1">
            <Power className="w-4 h-4 shrink-0" />
            {t(I18nKey.BUTTON$STOP)}
          </div>
        </ContextMenuListItem>
      )}

      {onDelete && (
        <ContextMenuListItem testId="delete-button" onClick={onDelete}>
          <div className="flex items-center gap-3 px-1">
            <Trash className="w-4 h-4 shrink-0" />
            {t(I18nKey.BUTTON$DELETE)}
          </div>
        </ContextMenuListItem>
      )}
    </ContextMenu>
  );
}
