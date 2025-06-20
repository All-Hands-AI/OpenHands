import React from "react";
import { FaListUl } from "react-icons/fa";
import { useTranslation } from "react-i18next";
import { I18nKey } from "#/i18n/declaration";
import { TooltipButton } from "./tooltip-button";
import { cn } from "#/utils/utils";

interface ConversationPanelButtonProps {
  isOpen: boolean;
}

export function ConversationPanelButton({
  isOpen,
}: ConversationPanelButtonProps) {
  const { t } = useTranslation();

  return (
    <TooltipButton
      testId="toggle-conversation-panel"
      tooltip=""
      ariaLabel={t(I18nKey.SIDEBAR$CONVERSATIONS)}
    >
      <FaListUl
        size={20}
        className={cn(isOpen ? "text-content" : "text-[#9099AC]")}
      />
    </TooltipButton>
  );
}
