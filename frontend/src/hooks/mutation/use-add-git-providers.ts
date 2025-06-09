import { useMutation, useQueryClient } from "@tanstack/react-query";
import { SecretsService } from "#/api/secrets-service";
import { Provider, ProviderToken } from "#/types/settings";

export const useAddGitProviders = () => {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: ({
      providers,
    }: {
      providers: Record<Provider, ProviderToken>;
    }) => SecretsService.addGitProvider(providers),
    onSuccess: async () => {
      await queryClient.invalidateQueries({ queryKey: ["settings"] });
    },
    meta: {
      disableToast: true,
    },
  });
};
