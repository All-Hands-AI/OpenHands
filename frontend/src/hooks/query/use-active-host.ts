import { useQueries, useQuery } from "@tanstack/react-query";
import axios from "axios";
import React from "react";
import { openHands } from "#/api/open-hands-axios";
import {
  useWsClient,
  WsClientProviderStatus,
} from "#/context/ws-client-provider";

export const useActiveHost = () => {
  const { status } = useWsClient();
  const [activeHost, setActiveHost] = React.useState<string | null>(null);

  const { data } = useQuery({
    queryKey: ["hosts"],
    queryFn: async () => {
      const response = await openHands.get<{ hosts: string[] }>(
        "/api/web-hosts",
      );
      return response.data;
    },
    enabled: status === WsClientProviderStatus.ACTIVE,
    initialData: { hosts: [] },
  });

  const apps = useQueries({
    queries: data.hosts.map((port) => ({
      queryKey: ["hosts", port],
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
