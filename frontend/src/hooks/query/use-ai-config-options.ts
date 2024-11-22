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
  });
