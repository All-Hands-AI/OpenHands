import React from "react";
import { VscTerminal } from "react-icons/vsc";
import { useTerminal } from "../../hooks/useTerminal";
import { useSession } from "#/context/session";

import "@xterm/xterm/css/xterm.css";

function Terminal() {
  const { data } = useSession();
  const ref = useTerminal(data.terminalStreams);

  return (
    <div className="flex flex-col h-full">
      <div className="flex items-center gap-2 px-4 py-2 text-sm border-b border-neutral-600">
        <VscTerminal />
        Terminal
      </div>
      <div className="grow p-2 flex min-h-0">
        <div ref={ref} className="h-full w-full" />
      </div>
    </div>
  );
}

export default Terminal;
