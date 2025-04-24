import { useQuery } from "@tanstack/react-query";
import { SecretsService } from "#/api/secrets-service";

export const useGetSecrets = () =>
  useQuery({
    queryKey: ["secrets"],
    queryFn: SecretsService.getSecrets,
  });
