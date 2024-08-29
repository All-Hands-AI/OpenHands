import React from "react";
import { VscTerminal } from "react-icons/vsc";
import { useTerminal } from "../../hooks/useTerminal";
import { useSession } from "#/context/session";

import "@xterm/xterm/css/xterm.css";

const isCommandAction = (message: object): message is CommandAction =>
  "action" in message && message.action === "run";

const isCommandObservation = (message: object): message is CommandObservation =>
  "observation" in message && message.observation === "run";

const simplifyTerminalMessages = (messages: TrajectoryItem[]) => {
  const filteredMessages = messages.filter(
    (message) => isCommandAction(message) || isCommandObservation(message),
  );

  return filteredMessages.map((message) => {
    if (isCommandAction(message)) {
      return {
        type: "input",
        content: message.args.command,
      } as const;
    }

    return {
      type: "output",
      content: message.content,
    } as const;
  });
};

function Terminal() {
  const { eventLog } = useSession();
  const ref = useTerminal(
    simplifyTerminalMessages(eventLog.map((message) => JSON.parse(message))),
  );

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
