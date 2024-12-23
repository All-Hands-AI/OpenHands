import { useQueries, useQuery } from "@tanstack/react-query";
import axios from "axios";
import React from "react";
import { useSelector } from "react-redux";
import { openHands } from "#/api/open-hands-axios";
import { RUNTIME_INACTIVE_STATES } from "#/types/agent-state";
import { RootState } from "#/store";
import { useConversation } from "#/context/conversation-context";

export const useActiveHost = () => {
  const { curAgentState } = useSelector((state: RootState) => state.agent);
  const [activeHost, setActiveHost] = React.useState<string | null>(null);

  const { conversationId } = useConversation();

  const { data } = useQuery({
    queryKey: [conversationId, "hosts"],
    queryFn: async () => {
      const response = await openHands.get<{ hosts: string[] }>(
        `/api/conversations/${conversationId}/web-hosts`,
      );
      return response.data;
    },
    enabled: !RUNTIME_INACTIVE_STATES.includes(curAgentState),
    initialData: { hosts: [] },
  });

  const apps = useQueries({
    queries: data.hosts.map((port) => ({
      queryKey: [conversationId, "hosts", port],
      queryFn: async () => axios.get(port),
      refetchInterval: 3000,
    })),
  });

  const success = apps.map((app) => app.isSuccess);

  React.useEffect(() => {
    const successfulApp = apps.find((app) => app.isSuccess);
    if (successfulApp) {
      const index = apps.indexOf(successfulApp);
      const port = data.hosts[index];
      setActiveHost(port);
    } else {
      setActiveHost(null);
    }
  }, [success, data]);

  return { activeHost };
};
