import { useQueries, useQuery } from "@tanstack/react-query";
import axios from "axios";
import React from "react";
import { openHands } from "#/api/open-hands-axios";
import {
  useWsClient,
  WsClientProviderStatus,
} from "#/context/ws-client-provider";

export const useActivePort = () => {
  const { status } = useWsClient();
  const [activePort, setActivePort] = React.useState<number | null>(null);

  const { data } = useQuery({
    queryKey: ["ports"],
    queryFn: async () => {
      const response = await openHands.get<{ ports: Record<number, number> }>(
        "/api/ports",
      );
      return response.data;
    },
    enabled: status !== WsClientProviderStatus.OPENING,
  });

  const apps = useQueries({
    queries: Object.values(data?.ports || {}).map((port) => ({
      queryKey: ["ports", port],
      queryFn: async () => axios.get(`http://localhost:${port}`),
      refetchInterval: 3000,
    })),
  });

  const success = apps.map((app) => app.isSuccess);

  React.useEffect(() => {
    const successfulApp = apps.find((app) => app.isSuccess);
    if (successfulApp) {
      const index = apps.indexOf(successfulApp);
      const port = Object.values(data?.ports || [])[index];
      setActivePort(port);
    } else {
      setActivePort(null);
    }
  }, [success, data]);

  return { activePort };
};
