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
      return { hosts: Object.keys(response.data.hosts) };
    },
    enabled: !RUNTIME_INACTIVE_STATES.includes(curAgentState),
    initialData: { hosts: [] },
  });

  const apps = useQueries({
    queries: data.hosts.map((host) => ({
      queryKey: [conversationId, "hosts", host],
      queryFn: async () => {
        console.log('querying host', host);
        try {
          await axios.get(host);
          return host;
        } catch (e) {
          return '';
        }
      },
      refetchInterval: 3000,
    })),
  });

  React.useEffect(() => {
    console.log('apps', apps);
    const successfulApp = apps.find((app) => app.data);
    console.log('successfulApp', successfulApp);
    // Here's the change - use empty string as fallback instead of null
    setActiveHost(successfulApp?.data || '');
  }, [apps]);

  return { activeHost };
};
