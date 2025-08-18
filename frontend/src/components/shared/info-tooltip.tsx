import React from "react";
import { Tooltip, TooltipProps } from "@heroui/react";
import QuestionCircleIcon from "#/icons/question-circle.svg?react";

interface InfoTooltipProps {
  content: string;
  placement?: TooltipProps["placement"];
  className?: string;
  iconClassName?: string;
  iconSize?: number;
}

export function InfoTooltip({
  content,
  placement = "right",
  className = "max-w-xs",
  iconClassName = "text-[#9099AC] hover:text-white cursor-help",
  iconSize = 16,
}: InfoTooltipProps) {
  return (
    <Tooltip
      content={content}
      closeDelay={100}
      placement={placement}
      className={className}
    >
      <QuestionCircleIcon
        width={iconSize}
        height={iconSize}
        className={iconClassName}
        aria-label="Information"
      />
    </Tooltip>
  );
}
