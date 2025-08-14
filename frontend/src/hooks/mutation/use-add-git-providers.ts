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
      // Refresh settings (providers), installations list, and repositories right away
      await Promise.all([
        queryClient.invalidateQueries({ queryKey: ["settings"], exact: false }),
        queryClient.invalidateQueries({ queryKey: ["installations"], exact: false }),
        queryClient.invalidateQueries({ queryKey: ["repositories"], exact: false }),
      ]);
    },
    meta: {
      disableToast: true,
    },
  });
};
