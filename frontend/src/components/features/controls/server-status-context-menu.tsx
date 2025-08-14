import { useTranslation } from "react-i18next";
import { useClickOutsideElement } from "#/hooks/use-click-outside-element";
import { cn } from "#/utils/utils";
import { ContextMenu } from "../context-menu/context-menu";
import { I18nKey } from "#/i18n/declaration";
import { ConversationStatus } from "#/types/conversation-status";
import StopCircleIcon from "#/icons/stop-circle.svg?react";
import PlayCircleIcon from "#/icons/play-circle.svg?react";
import { ServerStatusContextMenuIconText } from "./server-status-context-menu-icon-text";

interface ServerStatusContextMenuProps {
  onClose: () => void;
  onStopServer?: (event: React.MouseEvent<HTMLButtonElement>) => void;
  onStartServer?: (event: React.MouseEvent<HTMLButtonElement>) => void;
  conversationStatus: ConversationStatus | null;
  position?: "top" | "bottom";
}

export function ServerStatusContextMenu({
  onClose,
  onStopServer,
  onStartServer,
  conversationStatus,
  position = "top",
}: ServerStatusContextMenuProps) {
  const { t } = useTranslation();
  const ref = useClickOutsideElement<HTMLUListElement>(onClose);

  return (
    <ContextMenu
      ref={ref}
      testId="server-status-context-menu"
      className={cn(
        "flex flex-col gap-2 left-2 absolute mt-2 z-50 text-white bg-tertiary rounded-[6px] p-[6px] w-fit min-w-max",
        position === "top" && "bottom-full",
        position === "bottom" && "top-full",
      )}
    >
      {conversationStatus === "RUNNING" && onStopServer && (
        <ServerStatusContextMenuIconText
          icon={<StopCircleIcon width={18} height={18} />}
          text={t(I18nKey.COMMON$STOP_SERVER)}
          onClick={onStopServer}
          testId="stop-server-button"
        />
      )}

      {conversationStatus === "STOPPED" && onStartServer && (
        <ServerStatusContextMenuIconText
          icon={<PlayCircleIcon width={18} height={18} />}
          text={t(I18nKey.COMMON$START_SERVER)}
          onClick={onStartServer}
          testId="start-server-button"
        />
      )}
    </ContextMenu>
  );
}
