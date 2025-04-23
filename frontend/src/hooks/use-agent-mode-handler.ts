import { useEffect } from "react";
import { useDispatch } from "react-redux";
import { setAgentType, setDelegationState } from "#/state/agent-slice";
import ActionType from "#/types/action-type";

/**
 * Hook to handle agent mode changes based on WebSocket events
 */
export function useAgentModeHandler(events: Record<string, unknown>[]) {
  const dispatch = useDispatch();

  useEffect(() => {
    // Process only the latest event
    if (events.length === 0) return;

    const latestEvent = events[events.length - 1];

    // Handle agent delegation events
    if (
      "action" in latestEvent &&
      latestEvent.action === ActionType.DELEGATE &&
      "args" in latestEvent &&
      typeof latestEvent.args === "object" &&
      latestEvent.args !== null &&
      "agent" in latestEvent.args
    ) {
      // A delegation is starting
      dispatch(setDelegationState(true));
      dispatch(setAgentType(latestEvent.args.agent as string));
    }

    // Handle agent delegate observation (delegation ended)
    else if (
      "observation" in latestEvent &&
      latestEvent.observation === "delegate" &&
      "data" in latestEvent &&
      typeof latestEvent.data === "object" &&
      latestEvent.data !== null &&
      "status" in latestEvent.data &&
      latestEvent.data.status === "finished"
    ) {
      // Delegation has ended, returning to parent agent
      dispatch(setDelegationState(false));
      dispatch(setAgentType("CodeActAgent")); // Reset to default agent
    }
  }, [events, dispatch]);
}
