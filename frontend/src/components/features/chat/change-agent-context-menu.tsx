import React from "react";
import { useTranslation } from "react-i18next";
import { I18nKey } from "#/i18n/declaration";
import CodeTagIcon from "#/icons/code-tag.svg?react";
import LessonPlanIcon from "#/icons/lesson-plan.svg?react";
import { ContextMenu } from "#/ui/context-menu";
import { ContextMenuListItem } from "../context-menu/context-menu-list-item";
import { ContextMenuIconText } from "../context-menu/context-menu-icon-text";
import { useClickOutsideElement } from "#/hooks/use-click-outside-element";
import { cn } from "#/utils/utils";
import { CONTEXT_MENU_ICON_TEXT_CLASSNAME } from "#/utils/constants";

const contextMenuListItemClassName = cn(
  "cursor-pointer p-0 h-auto hover:bg-transparent",
  CONTEXT_MENU_ICON_TEXT_CLASSNAME,
);

const contextMenuIconTextClassName =
  "gap-2 p-2 hover:bg-[#5C5D62] rounded h-[30px]";

interface ChangeAgentContextMenuProps {
  onClose: () => void;
  onCodeClick?: (event: React.MouseEvent<HTMLButtonElement>) => void;
  onPlanClick?: (event: React.MouseEvent<HTMLButtonElement>) => void;
}

export function ChangeAgentContextMenu({
  onClose,
  onCodeClick,
  onPlanClick,
}: ChangeAgentContextMenuProps) {
  const { t } = useTranslation();
  const menuRef = useClickOutsideElement<HTMLUListElement>(onClose);

  const handleCodeClick = (event: React.MouseEvent<HTMLButtonElement>) => {
    event.preventDefault();
    event.stopPropagation();
    onCodeClick?.(event);
    onClose();
  };

  const handlePlanClick = (event: React.MouseEvent<HTMLButtonElement>) => {
    event.preventDefault();
    event.stopPropagation();
    onPlanClick?.(event);
    onClose();
  };

  return (
    <ContextMenu
      ref={menuRef}
      testId="change-agent-context-menu"
      position="top"
      alignment="left"
      className="min-h-fit min-w-[195px] mb-2"
    >
      <ContextMenuListItem
        testId="code-option"
        onClick={handleCodeClick}
        className={contextMenuListItemClassName}
      >
        <ContextMenuIconText
          icon={CodeTagIcon}
          text={t(I18nKey.COMMON$CODE)}
          className={contextMenuIconTextClassName}
        />
      </ContextMenuListItem>
      <ContextMenuListItem
        testId="plan-option"
        onClick={handlePlanClick}
        className={contextMenuListItemClassName}
      >
        <ContextMenuIconText
          icon={LessonPlanIcon}
          text={t(I18nKey.COMMON$PLAN)}
          className={contextMenuIconTextClassName}
        />
      </ContextMenuListItem>
    </ContextMenu>
  );
}
