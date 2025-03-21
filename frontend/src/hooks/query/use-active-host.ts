import { useQueries, useQuery, useQueryClient } from "@tanstack/react-query";
import axios from "axios";
import React from "react";
import { useSelector } from "react-redux";
import { openHands } from "#/api/open-hands-axios";
import { RUNTIME_INACTIVE_STATES } from "#/types/agent-state";
import { RootState } from "#/store";
import { useConversation } from "#/context/conversation-context";
import { useActionSubscription } from "#/hooks/use-action-subscription";
import ActionType from "#/types/action-type";

export const useActiveHost = () => {
  const { curAgentState } = useSelector((state: RootState) => state.agent);
  const [activeHost, setActiveHost] = React.useState<string | null>(null);
  const queryClient = useQueryClient();
  const { conversationId } = useConversation();

  // Get the list of hosts from the backend
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
    meta: {
      disableToast: true,
    },
  });

  // Create queries for each host, but don't automatically refetch
  const apps = useQueries({
    queries: data.hosts.map((host) => ({
      queryKey: [conversationId, "hosts", host],
      queryFn: async () => {
        try {
          await axios.get(host);
          return host;
        } catch (e) {
          return "";
        }
      },
      // Don't automatically refetch - we'll trigger manually
      refetchInterval: undefined,
      meta: {
        disableToast: true,
      },
    })),
  });

  const appsData = apps.map((app) => app.data);

  // Subscribe to "run" action events and test URLs when a new command is run
  useActionSubscription(ActionType.RUN, () => {
    if (data.hosts.length > 0) {
      data.hosts.forEach((host) => {
        queryClient.invalidateQueries({
          queryKey: [conversationId, "hosts", host],
        });
      });
    }
  });

  // Update activeHost when app data changes
  React.useEffect(() => {
    const successfulApp = appsData.find((app) => app);
    setActiveHost(successfulApp || "");
  }, [appsData]);

  return { activeHost };
};
