import { useTranslation } from "react-i18next";
import { useClickOutsideElement } from "#/hooks/use-click-outside-element";
import { cn } from "#/utils/utils";
import { ContextMenu } from "../context-menu/context-menu";
import { ContextMenuListItem } from "../context-menu/context-menu-list-item";
import { ContextMenuSeparator } from "../context-menu/context-menu-separator";
import { I18nKey } from "#/i18n/declaration";

interface ConversationNameContextMenuProps {
  onClose: () => void;
  onRename?: (event: React.MouseEvent<HTMLButtonElement>) => void;
  onDelete?: (event: React.MouseEvent<HTMLButtonElement>) => void;
  onStop?: (event: React.MouseEvent<HTMLButtonElement>) => void;
  onDisplayCost?: (event: React.MouseEvent<HTMLButtonElement>) => void;
  onShowAgentTools?: (event: React.MouseEvent<HTMLButtonElement>) => void;
  onShowMicroagents?: (event: React.MouseEvent<HTMLButtonElement>) => void;
  onExportConversation?: (event: React.MouseEvent<HTMLButtonElement>) => void;
  onDownloadViaVSCode?: (event: React.MouseEvent<HTMLButtonElement>) => void;
  position?: "top" | "bottom";
}

export function ConversationNameContextMenu({
  onClose,
  onRename,
  onDelete,
  onStop,
  onDisplayCost,
  onShowAgentTools,
  onShowMicroagents,
  onExportConversation,
  onDownloadViaVSCode,
  position = "bottom",
}: ConversationNameContextMenuProps) {
  const { t } = useTranslation();
  const ref = useClickOutsideElement<HTMLUListElement>(onClose);

  const hasDownload = Boolean(onDownloadViaVSCode);
  const hasExport = Boolean(onExportConversation);
  const hasTools = Boolean(onShowAgentTools || onShowMicroagents);
  const hasInfo = Boolean(onDisplayCost);
  const hasControl = Boolean(onStop || onDelete);

  return (
    <ContextMenu
      ref={ref}
      testId="conversation-name-context-menu"
      className={cn(
        "left-0 absolute mt-2 z-50 text-white bg-[#525662] rounded-[6px]",
        position === "top" && "bottom-full",
        position === "bottom" && "top-full",
      )}
    >
      {onRename && (
        <ContextMenuListItem
          testId="rename-button"
          onClick={onRename}
          className="cursor-pointer"
        >
          {t(I18nKey.BUTTON$RENAME)}
        </ContextMenuListItem>
      )}

      {hasTools && <ContextMenuSeparator className="bg-[#959CB2]" />}

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

      {(hasExport || hasDownload) && (
        <ContextMenuSeparator className="bg-[#959CB2]" />
      )}

      {onExportConversation && (
        <ContextMenuListItem
          testId="export-conversation-button"
          onClick={onExportConversation}
        >
          {t(I18nKey.BUTTON$EXPORT_CONVERSATION)}
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

      {(hasInfo || hasControl) && (
        <ContextMenuSeparator className="bg-[#959CB2]" />
      )}

      {onDisplayCost && (
        <ContextMenuListItem
          testId="display-cost-button"
          onClick={onDisplayCost}
        >
          {t(I18nKey.BUTTON$DISPLAY_COST)}
        </ContextMenuListItem>
      )}

      {onStop && (
        <ContextMenuListItem testId="stop-button" onClick={onStop}>
          {t(I18nKey.COMMON$STOP_CONVERSATION)}
        </ContextMenuListItem>
      )}

      {onDelete && (
        <ContextMenuListItem testId="delete-button" onClick={onDelete}>
          {t(I18nKey.COMMON$DELETE_CONVERSATION)}
        </ContextMenuListItem>
      )}
    </ContextMenu>
  );
}
