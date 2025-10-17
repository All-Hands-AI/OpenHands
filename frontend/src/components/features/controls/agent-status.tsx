import { useTranslation } from "react-i18next";
import { useEffect } from "react";
import { useStatusStore } from "#/state/status-store";
import { useActiveConversation } from "#/hooks/query/use-active-conversation";
import { getStatusCode } from "#/utils/status";
import { ChatStopButton } from "../chat/chat-stop-button";
import { AgentState } from "#/types/agent-state";
import ClockIcon from "#/icons/u-clock-three.svg?react";
import { ChatResumeAgentButton } from "../chat/chat-play-button";
import { cn } from "#/utils/utils";
import { AgentLoading } from "./agent-loading";
import { useConversationStore } from "#/state/conversation-store";
import CircleErrorIcon from "#/icons/circle-error.svg?react";
import { useAgentState } from "#/hooks/use-agent-state";
import { useUnifiedWebSocketStatus } from "#/hooks/use-unified-websocket-status";

export interface AgentStatusProps {
  className?: string;
  handleStop: () => void;
  handleResumeAgent: () => void;
  disabled?: boolean;
  isPausing?: boolean;
}

export function AgentStatus({
  className = "",
  handleStop,
  handleResumeAgent,
  disabled = false,
  isPausing = false,
}: AgentStatusProps) {
  const { t } = useTranslation();
  const { setShouldShownAgentLoading } = useConversationStore();
  const { curAgentState } = useAgentState();
  const { curStatusMessage } = useStatusStore();
  const webSocketStatus = useUnifiedWebSocketStatus();
  const { data: conversation } = useActiveConversation();

  const statusCode = getStatusCode(
    curStatusMessage,
    webSocketStatus,
    conversation?.status || null,
    conversation?.runtime_status || null,
    curAgentState,
  );

  const shouldShownAgentLoading =
    isPausing ||
    curAgentState === AgentState.INIT ||
    curAgentState === AgentState.LOADING ||
    webSocketStatus === "CONNECTING";

  const shouldShownAgentError =
    curAgentState === AgentState.ERROR ||
    curAgentState === AgentState.RATE_LIMITED;

  const shouldShownAgentStop = curAgentState === AgentState.RUNNING;

  const shouldShownAgentResume = curAgentState === AgentState.STOPPED;

  // Update global state when agent loading condition changes
  useEffect(() => {
    setShouldShownAgentLoading(shouldShownAgentLoading);
  }, [shouldShownAgentLoading, setShouldShownAgentLoading]);

  return (
    <div className={cn("flex items-center gap-1 min-w-0", className)}>
      <span
        className="text-[11px] text-white font-normal leading-5 flex-1 min-w-0 max-w-full whitespace-normal break-words"
        title={t(statusCode)}
      >
        {t(statusCode)}
      </span>
      <div
        className={cn(
          "bg-[#525252] box-border content-stretch flex flex-row gap-[3px] items-center justify-center overflow-clip px-0.5 py-1 relative rounded-[100px] shrink-0 size-6 transition-all duration-200 active:scale-95",
          (shouldShownAgentStop || shouldShownAgentResume) &&
            "hover:bg-[#737373] cursor-pointer",
        )}
      >
        {shouldShownAgentLoading && <AgentLoading />}
        {shouldShownAgentStop && <ChatStopButton handleStop={handleStop} />}
        {shouldShownAgentResume && (
          <ChatResumeAgentButton
            onAgentResumed={handleResumeAgent}
            disabled={disabled}
          />
        )}
        {shouldShownAgentError && <CircleErrorIcon className="w-4 h-4" />}
        {!shouldShownAgentLoading &&
          !shouldShownAgentStop &&
          !shouldShownAgentResume &&
          !shouldShownAgentError && <ClockIcon className="w-4 h-4" />}
      </div>
    </div>
  );
}

export default AgentStatus;
