import ActionType from "#/types/ActionType";
import AgentState from "#/types/AgentState";
import Session from "./session";

const INIT_DELAY = 1000;

export const generateAgentStateChangeEvent = (state: AgentState) =>
  JSON.stringify({
    action: ActionType.CHANGE_AGENT_STATE,
    args: { agent_state: state },
  });

export function changeAgentState(state: AgentState): void {
  const eventString = generateAgentStateChangeEvent(state);
  Session.send(eventString);
  if (state === AgentState.STOPPED) {
    setTimeout(() => {
      Session.startNewSession();
    }, INIT_DELAY);
  }
}
