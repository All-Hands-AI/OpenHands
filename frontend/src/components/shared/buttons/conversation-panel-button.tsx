import React from "react";
import { FaListUl } from "react-icons/fa";
import { useTranslation } from "react-i18next";
import { I18nKey } from "#/i18n/declaration";
import { TooltipButton } from "./tooltip-button";
import { cn } from "#/utils/utils";

interface ConversationPanelButtonProps {
  isOpen: boolean;
  onClick: () => void;
  disabled?: boolean;
}

export function ConversationPanelButton({
  isOpen,
  onClick,
  disabled = false,
}: ConversationPanelButtonProps) {
  const { t } = useTranslation();

  return (
    <TooltipButton
      testId="toggle-conversation-panel"
      tooltip={t(I18nKey.SIDEBAR$CONVERSATIONS)}
      ariaLabel={t(I18nKey.SIDEBAR$CONVERSATIONS)}
      onClick={onClick}
      disabled={disabled}
    >
      <FaListUl
        size={22}
        className={cn(
          isOpen ? "text-white" : "text-[#9099AC]",
          disabled && "opacity-50",
        )}
      />
    </TooltipButton>
  );
}
