import { useQuery } from "@tanstack/react-query";
import { SecretsService } from "#/api/secrets-service";
import { useUserProviders } from "../use-user-providers";

export const useGetSecrets = () => {
  const { providers } = useUserProviders();

  return useQuery({
    queryKey: ["secrets"],
    queryFn: SecretsService.getSecrets,
    enabled: providers.length > 0,
  });
};
