import { useQuery } from "@tanstack/react-query";
import axios from "axios";
import { openHands } from "#/api/open-hands-axios";

export function useIntegrationStatus(platform: "jira" | "jira-dc" | "linear") {
  return useQuery({
    queryKey: ["integration-status", platform],
    queryFn: async () => {
      try {
        const response = await openHands.get(
          `/integration/${platform}/workspaces/link`,
        );
        return response.data;
      } catch (error) {
        if (axios.isAxiosError(error) && error.response?.status === 404) {
          return null;
        }
        throw error;
      }
    },
  });
}
