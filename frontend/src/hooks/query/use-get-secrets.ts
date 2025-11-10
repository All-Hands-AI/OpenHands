import { useQuery } from "@tanstack/react-query";
import { SecretsService } from "#/api/secrets-service";
import { useConfig } from "./use-config";
import { useIsAuthed } from "#/hooks/query/use-is-authed";

export const useGetSecrets = () => {
  const { data: config } = useConfig();
  const { data: isAuthed } = useIsAuthed();

  const isOss = config?.APP_MODE === "oss";

  return useQuery({
    queryKey: ["secrets"],
    queryFn: SecretsService.getSecrets,
    enabled: isOss || isAuthed, // Enable regardless of providers
  });
};
