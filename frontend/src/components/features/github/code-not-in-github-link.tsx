import React from "react";
import { Tooltip } from "@heroui/react";

export function CodeNotInGitHubLink() {
  return (
    <Tooltip
      content='To upload files from your computer, start a new project by saying "wait for me to upload files". You can then use the provided VS Code interface to upload any files you want OpenHands to work with. When you&apos;re done, you can also use VS Code to download the changes.'
      closeDelay={100}
      className="max-w-md"
    >
      <span className="text-xs text-neutral-400 cursor-pointer italic border-b border-dashed border-neutral-400">
        Code not in GitHub?
      </span>
    </Tooltip>
  );
}
