import { useTranslation } from "react-i18next";
import { useClickOutsideElement } from "#/hooks/use-click-outside-element";
import { ContextMenu } from "../context-menu/context-menu";
import { ContextMenuListItem } from "../context-menu/context-menu-list-item";
import { I18nKey } from "#/i18n/declaration";

interface ProjectMenuCardContextMenuProps {
  isConnectedToGitHub: boolean;
  onConnectToGitHub: () => void;
  onPushToGitHub: () => void;
  onDownloadWorkspace: () => void;
  onViewInstructions: () => void;
  onAddInstructions: () => void;
  onViewMicroagents: () => void;
  onAddTemporaryMicroagent: () => void;
  onAddPermanentMicroagent: () => void;
  onClose: () => void;
}

export function ProjectMenuCardContextMenu({
  isConnectedToGitHub,
  onConnectToGitHub,
  onPushToGitHub,
  onDownloadWorkspace,
  onViewInstructions,
  onAddInstructions,
  onViewMicroagents,
  onAddTemporaryMicroagent,
  onAddPermanentMicroagent,
  onClose,
}: ProjectMenuCardContextMenuProps) {
  const menuRef = useClickOutsideElement<HTMLUListElement>(onClose);
  const { t } = useTranslation();
  return (
    <ContextMenu
      ref={menuRef}
      className="absolute right-0 bottom-[calc(100%+8px)]"
    >
      {!isConnectedToGitHub && (
        <ContextMenuListItem onClick={onConnectToGitHub}>
          {t(I18nKey.PROJECT_MENU_CARD_CONTEXT_MENU$CONNECT_TO_GITHUB_LABEL)}
        </ContextMenuListItem>
      )}
      {isConnectedToGitHub && (
        <>
          <ContextMenuListItem onClick={onPushToGitHub}>
            {t(I18nKey.PROJECT_MENU_CARD_CONTEXT_MENU$PUSH_TO_GITHUB_LABEL)}
          </ContextMenuListItem>
          <ContextMenuListItem onClick={onViewInstructions}>
            {t(I18nKey.PROJECT_MENU_CARD_CONTEXT_MENU$VIEW_INSTRUCTIONS_LABEL)}
          </ContextMenuListItem>
          <ContextMenuListItem onClick={onAddInstructions}>
            {t(I18nKey.PROJECT_MENU_CARD_CONTEXT_MENU$ADD_INSTRUCTIONS_LABEL)}
          </ContextMenuListItem>
          <ContextMenuListItem onClick={onViewMicroagents}>
            {t(I18nKey.PROJECT_MENU_CARD_CONTEXT_MENU$VIEW_MICROAGENTS_LABEL)}
          </ContextMenuListItem>
          <ContextMenuListItem onClick={onAddTemporaryMicroagent}>
            {t(I18nKey.PROJECT_MENU_CARD_CONTEXT_MENU$ADD_TEMPORARY_MICROAGENT_LABEL)}
          </ContextMenuListItem>
          <ContextMenuListItem onClick={onAddPermanentMicroagent}>
            {t(I18nKey.PROJECT_MENU_CARD_CONTEXT_MENU$ADD_PERMANENT_MICROAGENT_LABEL)}
          </ContextMenuListItem>
        </>
      )}
      <ContextMenuListItem onClick={onDownloadWorkspace}>
        {t(I18nKey.PROJECT_MENU_CARD_CONTEXT_MENU$DOWNLOAD_FILES_LABEL)}
      </ContextMenuListItem>
    </ContextMenu>
  );
}
