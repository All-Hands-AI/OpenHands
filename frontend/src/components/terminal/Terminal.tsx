import React from "react";
import { useSelector } from "react-redux";
import { VscTerminal } from "react-icons/vsc";
import { RootState } from "#/store";
import { useTerminal } from "../../hooks/useTerminal";

import "@xterm/xterm/css/xterm.css";

function Terminal() {
  const { commands } = useSelector((state: RootState) => state.cmd);
  const ref = useTerminal(commands);

  return (
    <div className="flex flex-col h-full bg-bg-workspace dark:bg-bg-workspace text-text-editor-base dark:text-text-editor-base">
      <div className="flex items-center gap-2 px-4 py-2 text-sm border-b border-border dark:border-border-editor-sidebar bg-bg-editor-sidebar dark:bg-bg-editor-sidebar">
        <VscTerminal />
        Terminal
      </div>
      <div className="grow p-2 flex min-h-0 bg-bg-input dark:bg-bg-input">
        <div ref={ref} className="h-full w-full" />
      </div>
    </div>
  );
}

export default Terminal;
