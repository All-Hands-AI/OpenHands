import React from "react";
import { Button } from "@nextui-org/react";
import ChevronDoubleRight from "#/icons/chevron-double-right.svg?react";

interface CollapsePanelButtonProps {
  isCollapsed: boolean;
  onClick: () => void;
}

export function CollapsePanelButton({
  isCollapsed,
  onClick,
}: CollapsePanelButtonProps) {
  return (
    <Button
      isIconOnly
      variant="light"
      aria-label={isCollapsed ? "Expand panel" : "Collapse panel"}
      className="absolute -right-4 top-1/2 transform -translate-y-1/2 z-10 bg-neutral-800 border border-neutral-600 rounded-full p-1"
      onClick={onClick}
    >
      <ChevronDoubleRight
        className={`w-4 h-4 transition-transform duration-200 ${
          isCollapsed ? "rotate-180" : ""
        }`}
      />
    </Button>
  );
}
