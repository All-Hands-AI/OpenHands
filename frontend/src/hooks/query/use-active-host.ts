import { useQueries, useQuery, useQueryClient } from "@tanstack/react-query";
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
  const queryClient = useQueryClient();
  const messages = useSelector((state: RootState) => state.chat.messages);
  const prevMessagesLengthRef = React.useRef(messages.length);

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

  // Effect to detect new CommandRunAction and trigger URL testing
  React.useEffect(() => {
    // Check if messages length increased (new message added)
    if (messages.length > prevMessagesLengthRef.current) {
      // Look for CommandRunAction in the new messages
      const newMessages = messages.slice(prevMessagesLengthRef.current);
      const hasCommandRunAction = newMessages.some(
        (msg) =>
          msg.type === "action" && msg.translationID === "ACTION_MESSAGE$RUN",
      );

      // If a new CommandRunAction was added, trigger refetch of all host queries
      if (hasCommandRunAction && data.hosts.length > 0) {
        data.hosts.forEach((host) => {
          queryClient.invalidateQueries({
            queryKey: [conversationId, "hosts", host],
          });
        });
      }
    }

    // Update the ref for next comparison
    prevMessagesLengthRef.current = messages.length;
  }, [messages, data.hosts, conversationId, queryClient]);

  // Update activeHost when app data changes
  React.useEffect(() => {
    const successfulApp = appsData.find((app) => app);
    setActiveHost(successfulApp || "");
  }, [appsData]);

  return { activeHost };
};
