import React from "react";
import { AgentControlBar } from "./agent-control-bar";
import { AgentStatusBar } from "./agent-status-bar";
import { SecurityLock } from "./security-lock";

interface ControlsProps {
  setSecurityOpen: (isOpen: boolean) => void;
  showSecurityLock: boolean;
}

export function Controls({ setSecurityOpen, showSecurityLock }: ControlsProps) {
  return (
    <div className="flex flex-col gap-2 md:items-center md:justify-between md:flex-row">
      <div className="flex items-center gap-2">
        <AgentControlBar />
        <AgentStatusBar />

        {showSecurityLock && (
          <SecurityLock onClick={() => setSecurityOpen(true)} />
        )}
      </div>
    </div>
  );
}
