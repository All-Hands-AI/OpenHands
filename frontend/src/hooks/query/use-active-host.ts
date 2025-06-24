import { useQueries, useQuery } from "@tanstack/react-query";
import axios from "axios";
import React from "react";
import OpenHands from "#/api/open-hands";
import { useConversationId } from "#/hooks/use-conversation-id";
import { useRuntimeIsReady } from "#/hooks/use-runtime-is-ready";

export const useActiveHost = () => {
  const [activeHost, setActiveHost] = React.useState<string | null>(null);
  const { conversationId } = useConversationId();
  const runtimeIsReady = useRuntimeIsReady();

  const { data } = useQuery({
    queryKey: [conversationId, "hosts"],
    queryFn: async () => {
      const hosts = await OpenHands.getWebHosts(conversationId);
      return { hosts };
    },
    enabled: runtimeIsReady && !!conversationId,
    initialData: { hosts: [] },
    meta: {
      disableToast: true,
    },
  });

  console.log(
    "useActiveHost: %c%s",
    "background: #444; color: #ffeb3b; font-weight: bold; padding: 2px 4px; border-radius: 4px;",
    `Shakudo: Conversation ID: ${conversationId}, Hosts: ${data.hosts.join(", ")}`,
  );

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
      // refetchInterval: 3000,
      meta: {
        disableToast: true,
      },
    })),
  });

  const appsData = apps.map((app) => app.data);

  React.useEffect(() => {
    const successfulApp = appsData.find((app) => app);
    setActiveHost(successfulApp || "");
  }, [appsData]);

  return { activeHost };
};
