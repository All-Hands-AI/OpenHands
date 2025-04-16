import { useSelector } from "react-redux";
import { RootState } from "#/store";
import { useTerminal } from "#/hooks/use-terminal";
import "@xterm/xterm/css/xterm.css";
import { Tooltip } from "@heroui/react";
import React, { useState } from "react";

function Terminal() {
  const { commands } = useSelector((state: RootState) => state.cmd);
  const [showTooltip, setShowTooltip] = useState(false);
  
  const ref = useTerminal({
    commands,
  });

  // Show tooltip when user clicks or tries to interact with terminal
  const handleTerminalClick = () => {
    setShowTooltip(true);
    // Hide tooltip after 5 seconds
    setTimeout(() => setShowTooltip(false), 5000);
  };

  const handleTerminalKeyDown = () => {
    setShowTooltip(true);
    // Hide tooltip after 5 seconds
    setTimeout(() => setShowTooltip(false), 5000);
  };

  const readOnlyMessage = "The terminal is read-only. To make manual modifications, please launch the VSCode server from Workspace.";

  return (
    <div className="h-full p-2 min-h-0 flex-grow">
      <Tooltip 
        content={
          <div className="max-w-xs">
            {readOnlyMessage}
          </div>
        } 
        placement="bottom"
        open={showTooltip}
      >
        <div 
          ref={ref} 
          className="h-full w-full cursor-not-allowed" 
          onClick={handleTerminalClick}
          onKeyDown={handleTerminalKeyDown}
          tabIndex={0}
        />
      </Tooltip>
    </div>
  );
}

export default Terminal;
