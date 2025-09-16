import { Tooltip } from "@heroui/react";
import { useTranslation } from "react-i18next";
import { Wifi, WifiOff } from "lucide-react";
import { I18nKey } from "#/i18n/declaration";
import { useWsClient } from "#/context/ws-client-provider";

export interface ConnectionStatusProps {
  className?: string;
}

export function ConnectionStatus({ className = "" }: ConnectionStatusProps) {
  const { t } = useTranslation();
  const { webSocketStatus } = useWsClient();

  const getStatusIconAndColor = () => {
    switch (webSocketStatus) {
      case "CONNECTED":
        return {
          icon: Wifi,
          color: "#BCFF8C", // Green
          text: "Connected",
        };
      case "CONNECTING":
        return {
          icon: Wifi,
          color: "#FFD600", // Yellow
          text: t(I18nKey.CHAT_INTERFACE$CONNECTING),
        };
      case "DISCONNECTED":
        return {
          icon: WifiOff,
          color: "#FF684E", // Red
          text: t(I18nKey.CHAT_INTERFACE$DISCONNECTED),
        };
      default:
        return {
          icon: WifiOff,
          color: "#9CA3AF", // Gray
          text: "Unknown Connection",
        };
    }
  };

  const { icon: StatusIcon, color, text } = getStatusIconAndColor();

  return (
    <div className={className}>
      <Tooltip content={`WS ${text}`} closeDelay={100}>
        <div className="flex items-center">
          <StatusIcon className="w-4 h-4" style={{ color }} />
        </div>
      </Tooltip>
    </div>
  );
}

export default ConnectionStatus;
