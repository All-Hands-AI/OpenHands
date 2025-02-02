import { Tooltip } from "@nextui-org/react";
import { ReactNode } from "react";

interface TooltipWrapperProps {
  content: string;
  children: ReactNode;
}

export function TooltipWrapper({ content, children }: TooltipWrapperProps) {
  return (
    <Tooltip content={content} closeDelay={100}>
      {children}
    </Tooltip>
  );
}