import { useSelector, useDispatch } from "react-redux";
import { useEffect } from "react";
import { RootState } from "#/store";
import { AgentState } from "#/types/agent-state";
import { ChatStopButton } from "../chat/chat-stop-button";
import { ChatResumeAgentButton } from "../chat/chat-play-button";
import { cn } from "#/utils/utils";
import { AgentLoading } from "../controls/agent-loading";
import { setShouldShownAgentLoading } from "#/state/conversation-slice";

export interface AgentControlsProps {
  className?: string;
  handleStop: () => void;
  handleResumeAgent: () => void;
  disabled?: boolean;
}

export function AgentControls({
  className = "",
  handleStop,
  handleResumeAgent,
  disabled = false,
}: AgentControlsProps) {
  const dispatch = useDispatch();
  const { curAgentState } = useSelector((state: RootState) => state.agent);

  const shouldShownAgentLoading =
    curAgentState === AgentState.INIT || curAgentState === AgentState.LOADING;

  const shouldShownAgentStop = curAgentState === AgentState.RUNNING;

  const shouldShownAgentResume = curAgentState === AgentState.STOPPED;

  // Update global state when agent loading condition changes
  useEffect(() => {
    dispatch(setShouldShownAgentLoading(shouldShownAgentLoading));
  }, [shouldShownAgentLoading, dispatch]);

  const hasControls =
    shouldShownAgentLoading || shouldShownAgentStop || shouldShownAgentResume;

  return (
    <div className={className}>
      {hasControls ? (
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
        </div>
      ) : (
        // Maintain consistent height when no controls are shown
        <div className="size-6 invisible" />
      )}
    </div>
  );
}

export default AgentControls;
