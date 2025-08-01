import { useTranslation } from "react-i18next";
import { useClickOutsideElement } from "#/hooks/use-click-outside-element";
import { cn } from "#/utils/utils";
import { ContextMenu } from "../context-menu/context-menu";
import { ContextMenuListItem } from "../context-menu/context-menu-list-item";
import { I18nKey } from "#/i18n/declaration";

interface ConversationNameContextMenuProps {
  onClose: () => void;
  onRename?: (event: React.MouseEvent<HTMLButtonElement>) => void;
  position?: "top" | "bottom";
}

export function ConversationNameContextMenu({
  onClose,
  onRename,
  position = "bottom",
}: ConversationNameContextMenuProps) {
  const { t } = useTranslation();
  const ref = useClickOutsideElement<HTMLUListElement>(onClose);

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
    </ContextMenu>
  );
}
