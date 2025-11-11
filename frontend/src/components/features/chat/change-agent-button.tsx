import React, { useMemo, useEffect } from "react";
import { useTranslation } from "react-i18next";
import { Typography } from "#/ui/typography";
import { I18nKey } from "#/i18n/declaration";
import CodeTagIcon from "#/icons/code-tag.svg?react";
import ChevronDownSmallIcon from "#/icons/chevron-down-small.svg?react";
import LessonPlanIcon from "#/icons/lesson-plan.svg?react";
import { useConversationStore } from "#/state/conversation-store";
import { ChangeAgentContextMenu } from "./change-agent-context-menu";
import { cn } from "#/utils/utils";
import { USE_PLANNING_AGENT } from "#/utils/feature-flags";
import { useAgentState } from "#/hooks/use-agent-state";
import { AgentState } from "#/types/agent-state";

export function ChangeAgentButton() {
  const { t } = useTranslation();
  const [contextMenuOpen, setContextMenuOpen] = React.useState(false);

  const conversationMode = useConversationStore(
    (state) => state.conversationMode,
  );

  const setConversationMode = useConversationStore(
    (state) => state.setConversationMode,
  );

  const shouldUsePlanningAgent = USE_PLANNING_AGENT();

  const { curAgentState } = useAgentState();

  const isAgentRunning = curAgentState === AgentState.RUNNING;

  // Close context menu when agent starts running
  useEffect(() => {
    if (isAgentRunning && contextMenuOpen) {
      setContextMenuOpen(false);
    }
  }, [isAgentRunning, contextMenuOpen]);

  const handleButtonClick = (event: React.MouseEvent<HTMLButtonElement>) => {
    event.preventDefault();
    event.stopPropagation();
    setContextMenuOpen(!contextMenuOpen);
  };

  const handleCodeClick = (event: React.MouseEvent<HTMLButtonElement>) => {
    event.preventDefault();
    event.stopPropagation();
    setConversationMode("code");
  };

  const handlePlanClick = (event: React.MouseEvent<HTMLButtonElement>) => {
    event.preventDefault();
    event.stopPropagation();
    setConversationMode("plan");
  };

  const isExecutionAgent = conversationMode === "code";

  const buttonLabel = useMemo(() => {
    if (isExecutionAgent) {
      return t(I18nKey.COMMON$CODE);
    }
    return t(I18nKey.COMMON$PLAN);
  }, [isExecutionAgent, t]);

  const buttonIcon = useMemo(() => {
    if (isExecutionAgent) {
      return <CodeTagIcon width={18} height={18} color="#737373" />;
    }
    return <LessonPlanIcon width={18} height={18} color="#ffffff" />;
  }, [isExecutionAgent]);

  if (!shouldUsePlanningAgent) {
    return null;
  }

  return (
    <div className="relative">
      <button
        type="button"
        onClick={handleButtonClick}
        disabled={isAgentRunning}
        className={cn(
          "flex items-center border border-[#4B505F] rounded-[100px] transition-opacity",
          !isExecutionAgent && "border-[#597FF4] bg-[#4A67BD]",
          isAgentRunning
            ? "opacity-50 cursor-not-allowed"
            : "cursor-pointer hover:opacity-80",
        )}
      >
        <div className="flex items-center gap-1 pl-1.5">
          {buttonIcon}
          <Typography.Text className="text-white text-2.75 not-italic font-normal leading-5">
            {buttonLabel}
          </Typography.Text>
        </div>
        <ChevronDownSmallIcon width={24} height={24} color="#ffffff" />
      </button>
      {contextMenuOpen && (
        <ChangeAgentContextMenu
          onClose={() => setContextMenuOpen(false)}
          onCodeClick={handleCodeClick}
          onPlanClick={handlePlanClick}
        />
      )}
    </div>
  );
}
