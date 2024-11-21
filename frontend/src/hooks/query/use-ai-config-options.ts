import { useQuery } from "@tanstack/react-query";

const getModels = async (): Promise<string[]> => {
  const response = await fetch("/api/options/models");

  if (!response.ok) {
    throw new Error("Failed to fetch models");
  }

  return response.json();
};

const getAgents = async (): Promise<string[]> => {
  const response = await fetch("/api/options/agents");

  if (!response.ok) {
    throw new Error("Failed to fetch agents");
  }

  return response.json();
};

const getSecurityAnalyzers = async (): Promise<string[]> => {
  const response = await fetch("/api/options/security-analyzers");

  if (!response.ok) {
    throw new Error("Failed to fetch security analyzers");
  }

  return response.json();
};

const fetchAiConfigOptions = async () => ({
  models: await getModels(),
  agents: await getAgents(),
  securityAnalyzers: await getSecurityAnalyzers(),
});

export const useAIConfigOptions = () =>
  useQuery({
    queryKey: ["ai-config-options"],
    queryFn: fetchAiConfigOptions,
  });
