import {
  useWsClient,
  WsClientProviderStatus,
} from "#/context/ws-client-provider";
import { cn } from "#/utils/utils";

export function TerminalStatusLabel() {
  const { status } = useWsClient();

  return (
    <div className="flex items-center gap-2">
      <div
        className={cn(
          "w-2 h-2 rounded-full",
          status === WsClientProviderStatus.ACTIVE && "bg-green-500",
          status !== WsClientProviderStatus.ACTIVE &&
            "bg-red-500 animate-pulse",
        )}
      />
      Terminal
    </div>
  );
}
