import { useMemo } from "react";
import { useAgentStore } from "#/stores/agent-store";
import { useV1ConversationStateStore } from "#/stores/v1-conversation-state-store";
import { useActiveConversation } from "#/hooks/query/use-active-conversation";
import { AgentState } from "#/types/agent-state";
import { V1AgentStatus } from "#/types/v1/core/base/common";

/**
 * Maps V1 agent status to V0 AgentState
 */
function mapV1StatusToV0State(status: V1AgentStatus | null): AgentState {
  if (!status) {
    return AgentState.LOADING;
  }

  switch (status) {
    case V1AgentStatus.IDLE:
      return AgentState.AWAITING_USER_INPUT;
    case V1AgentStatus.RUNNING:
      return AgentState.RUNNING;
    case V1AgentStatus.PAUSED:
      return AgentState.PAUSED;
    case V1AgentStatus.WAITING_FOR_CONFIRMATION:
      return AgentState.AWAITING_USER_CONFIRMATION;
    case V1AgentStatus.FINISHED:
      return AgentState.FINISHED;
    case V1AgentStatus.ERROR:
      return AgentState.ERROR;
    case V1AgentStatus.STUCK:
      return AgentState.ERROR; // Map STUCK to ERROR for now
    default:
      return AgentState.LOADING;
  }
}

/**
 * Unified hook that returns the current agent state
 * - For V0 conversations: Returns state from useAgentStore
 * - For V1 conversations: Returns mapped state from useV1ConversationStateStore
 */
export function useAgentState() {
  const { data: conversation } = useActiveConversation();
  const v0State = useAgentStore((state) => state.curAgentState);
  const v1Status = useV1ConversationStateStore((state) => state.agent_status);

  const isV1Conversation = conversation?.conversation_version === "V1";

  const curAgentState = useMemo(() => {
    if (isV1Conversation) {
      return mapV1StatusToV0State(v1Status);
    }
    return v0State;
  }, [isV1Conversation, v1Status, v0State]);

  return { curAgentState };
}
