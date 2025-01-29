import { useEffect } from "react";
import { useSelector } from "react-redux";
import { AgentState } from "#/types/agent-state";
import { useNotification } from "../hooks/useNotification";

const notificationStates = [
  AgentState.AWAITING_USER_INPUT,
  AgentState.FINISHED,
  AgentState.AWAITING_USER_CONFIRMATION,
];

const stateMessages = {
  [AgentState.AWAITING_USER_INPUT]: "Agent needs your input",
  [AgentState.FINISHED]: "Task completed",
  [AgentState.AWAITING_USER_CONFIRMATION]: "Agent needs your confirmation",
};

export function AgentStateNotifier() {
  const { notify } = useNotification();
  const curAgentState = useSelector(
    (state: { agent: { curAgentState: AgentState } }) =>
      state.agent.curAgentState,
  );

  useEffect(() => {
    if (notificationStates.includes(curAgentState)) {
      notify(stateMessages[curAgentState as keyof typeof stateMessages], {
        body: `Agent state changed to ${curAgentState}`,
      });
    }
  }, [curAgentState, notify]);

  return null;
}
