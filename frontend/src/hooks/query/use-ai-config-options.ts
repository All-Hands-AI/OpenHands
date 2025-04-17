import { useQuery } from "@tanstack/react-query";
import OpenHands from "#/api/open-hands";

const fetchAiConfigOptions = async () => ({
  models: await OpenHands.getModels(),
  agents: await OpenHands.getAgents(),
  securityAnalyzers: await OpenHands.getSecurityAnalyzers(),
});

export const useAIConfigOptions = () =>
  useQuery({
    queryKey: ["ai-config-options"],
    queryFn: fetchAiConfigOptions,
    staleTime: 1000 * 60 * 5, // 5 minutes
    gcTime: 1000 * 60 * 15, // 15 minutes
  });
