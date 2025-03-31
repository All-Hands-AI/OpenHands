import React from "react";
import { SettingsSwitch } from "./settings-switch";

interface ResearchModeToggleProps {
  defaultIsToggled?: boolean;
}

export function ResearchModeToggle({
  defaultIsToggled = false,
}: ResearchModeToggleProps) {
  return (
    <div className="flex flex-col gap-2">
      <h3 className="text-sm font-medium">Research Mode</h3>
      <div className="flex flex-col gap-1">
        <SettingsSwitch
          testId="research-mode-toggle"
          name="research-mode"
          defaultIsToggled={defaultIsToggled}
        >
          Enable Research Mode (Read-only Tools)
        </SettingsSwitch>
        <p className="text-xs text-gray-500 ml-10">
          When enabled, the agent will only use read-only tools like grep, glob,
          view, and web_read. This is useful for exploring a codebase without
          making changes.
        </p>
      </div>
    </div>
  );
}
