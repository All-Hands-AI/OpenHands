import { useTranslation } from "react-i18next";
import { useClickOutsideElement } from "#/hooks/use-click-outside-element";
import { ContextMenu } from "#/ui/context-menu";
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
      position={position}
      alignment="left"
      size="default"
      className="left-2 w-fit min-w-max"
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
