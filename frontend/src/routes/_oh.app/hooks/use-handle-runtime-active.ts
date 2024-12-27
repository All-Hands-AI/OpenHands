import React from "react";
import { useSelector } from "react-redux";
import { useAuth } from "#/context/auth-context";
import { useWsClient } from "#/context/ws-client-provider";
import { getGitHubTokenCommand } from "#/services/terminal-service";
import { RootState } from "#/store";
import { useGitHubUser } from "../../../hooks/query/use-github-user";
import { isGitHubErrorReponse } from "#/api/github-axios-instance";
import { RUNTIME_INACTIVE_STATES } from "#/types/agent-state";

export const useHandleRuntimeActive = () => {
  const { gitHubToken } = useAuth();
  const { send } = useWsClient();
  const { curAgentState } = useSelector((state: RootState) => state.agent);

  const { data: user } = useGitHubUser();

  const runtimeActive = !RUNTIME_INACTIVE_STATES.includes(curAgentState);

  const userId = React.useMemo(() => {
    if (user && !isGitHubErrorReponse(user)) return user.id;
    return null;
  }, [user]);

  React.useEffect(() => {
    if (runtimeActive && userId && gitHubToken) {
      // Export if the user valid, this could happen mid-session so it is handled here
      send(getGitHubTokenCommand(gitHubToken));
    }
  }, [userId, gitHubToken, runtimeActive]);
};
