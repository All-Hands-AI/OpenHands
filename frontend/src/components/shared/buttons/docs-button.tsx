import DocsIcon from "#/icons/docs.svg?react";
import { TooltipButton } from "./tooltip-button";

export function DocsButton() {
  return (
    <TooltipButton
      tooltip="Documentation"
      ariaLabel="Documentation"
      href="https://docs.all-hands.dev"
    >
      <DocsIcon width={28} height={28} />
    </TooltipButton>
  );
}
