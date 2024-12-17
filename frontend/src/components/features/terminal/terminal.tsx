import { useSelector } from "react-redux";
import { RootState } from "#/store";
import { useTerminal } from "#/hooks/use-terminal";
import "@xterm/xterm/css/xterm.css";
import {
  useWsClient,
  WsClientProviderStatus,
} from "#/context/ws-client-provider";

interface TerminalProps {
  secrets: string[];
}

function Terminal({ secrets }: TerminalProps) {
  const { status } = useWsClient();
  const { commands } = useSelector((state: RootState) => state.cmd);

  const ref = useTerminal({
    commands,
    secrets,
    disabled: status === WsClientProviderStatus.OPENING,
  });

  return (
    <div className="h-full p-2 min-h-0">
      <div ref={ref} className="h-full w-full" />
    </div>
  );
}

export default Terminal;
