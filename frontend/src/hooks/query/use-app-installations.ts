import { useQuery } from "@tanstack/react-query";
import { useConfig } from "./use-config";
import { useIsAuthed } from "./use-is-authed";
import OpenHands from "#/api/open-hands";
import { useUserProviders } from "../use-user-providers";
import { Provider } from "#/types/settings";
import { shouldUseInstallationRepos } from "#/utils/utils";

export const useAppInstallations = (selectedProvider: Provider | null) => {
  const { data: config } = useConfig();
  const { data: userIsAuthenticated } = useIsAuthed();
  const { providers } = useUserProviders();

  return useQuery({
    queryKey: ["installations", providers || [], selectedProvider],
    queryFn: () => OpenHands.getUserInstallationIds(selectedProvider!),
    enabled:
      userIsAuthenticated &&
      !!selectedProvider &&
      shouldUseInstallationRepos(selectedProvider, config?.APP_MODE),
    staleTime: 1000 * 60 * 5, // 5 minutes
    gcTime: 1000 * 60 * 15, // 15 minutes
  });
};
