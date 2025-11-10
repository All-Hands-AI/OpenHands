import { useQuery } from "@tanstack/react-query";
import OptionService from "#/api/option-service/option-service.api";

const fetchAiConfigOptions = async () => ({
  models: await OptionService.getModels(),
  agents: await OptionService.getAgents(),
  securityAnalyzers: await OptionService.getSecurityAnalyzers(),
});

export const useAIConfigOptions = () =>
  useQuery({
    queryKey: ["ai-config-options"],
    queryFn: fetchAiConfigOptions,
    staleTime: 1000 * 60 * 5, // 5 minutes
    gcTime: 1000 * 60 * 15, // 15 minutes
  });
